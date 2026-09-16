from __future__ import annotations

import json
import tempfile
import unittest
import uuid
from datetime import datetime, timezone
from pathlib import Path

from app.artifact_store import ArtifactStore
from app.catalog_promotion import promote_candidate
from app.product_migrator import ProductMigrationError, ProductMigrator
from app.product_snapshot_store import get_snapshot
from app.product_store import get_product
from app.product_visibility import filter_visible_products


def _write_offer(root: Path, offer_id: str, *, name: str = "Acme Suite", workspace_id: str | None = None, hard_gates: list[str] | None = None) -> None:
    offer = {
        "offer_id": offer_id,
        "name": name,
        "status": "draft",
        "positioning": {"one_liner": "Automates onboarding"},
        "problem": {"canonical": None, "anti_problem": ["not for regulated finance"]},
        "outcomes": {"primary": ["faster onboarding"], "secondary": []},
        "hard_gates": hard_gates or ["SOC2 required"],
        "proof": {"source_registry": None, "evidence_status": "hypothesis", "epistemic_status": "hypothesis"},
        "unknowns": [],
    }
    if workspace_id:
        offer["workspace_id"] = workspace_id
    profile = {"schema_version": "0.2", "offer": offer}
    path = root / "product_catalog" / f"{offer_id}.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    ArtifactStore(root).write_yaml(path, profile)


def _write_harvest(root: Path, *, company: str, name: str) -> tuple[str, str]:
    harvest_id = str(uuid.uuid4())
    candidate_id = "CAND-001"
    document = {
        "schema_version": "0.5",
        "harvest_id": harvest_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "company": company,
        "shelf_id": "shelf-1",
        "source_kind": "manual_or_external_harvest",
        "acquisition": {},
        "items": [
            {
                "candidate_id": candidate_id,
                "name": name,
                "source_url": "https://example.com/acme",
                "raw_claims": ["Automates onboarding"],
                "source_metadata": {},
                "epistemic_status": "unreviewed_source_claim",
                "promotion_status": "candidate",
            }
        ],
        "promotion_contract": {
            "automatic_promotion_to_product_catalog": False,
            "required_skill": "product-icp-intelligence",
            "required_human_review": True,
        },
    }
    company_slug = company.lower().replace(" ", "-")
    path = root / "data" / "private" / "catalog_harvest" / company_slug / f"{harvest_id}.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    ArtifactStore(root).write_yaml(path, document)
    return harvest_id, candidate_id


class ProductMigratorTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        _write_offer(self.root, "acme-suite")
        _write_offer(self.root, "globex-tool", name="Globex Tool")
        self.migrator = ProductMigrator(self.root)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_plan_finds_both_offers(self) -> None:
        plan = self.migrator.plan()
        self.assertEqual(2, plan["counts"]["offers"])

    def test_plan_is_deterministic(self) -> None:
        plan_a = self.migrator.plan()
        plan_b = self.migrator.plan()
        self.assertEqual(
            sorted(i["product_id"] for i in plan_a["items"]),
            sorted(i["product_id"] for i in plan_b["items"]),
        )

    def test_apply_creates_product_and_snapshot(self) -> None:
        plan = self.migrator.plan()
        self.migrator.apply(plan)
        product_id = next(i["product_id"] for i in plan["items"] if i["offer_id"] == "acme-suite")
        product = get_product(self.root, product_id)
        self.assertEqual("Acme Suite", product["name"])
        snapshot_id = next(i["snapshot_id"] for i in plan["items"] if i["offer_id"] == "acme-suite")
        snapshot = get_snapshot(self.root, snapshot_id)
        self.assertEqual("Automates onboarding", snapshot["content"]["description"])
        self.assertIn("SOC2 required", snapshot["content"]["hard_gates"])

    def test_apply_is_idempotent_on_rerun(self) -> None:
        plan = self.migrator.plan()
        self.migrator.apply(plan)
        second_plan = self.migrator.plan()
        manifest_path = self.migrator.apply(second_plan)
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(0, manifest["counts"]["applied"])
        self.assertEqual(2, manifest["counts"]["skipped"])

    def test_workspace_scoped_offer_maps_to_workspace_overlay(self) -> None:
        _write_offer(self.root, "acme-ws-only", workspace_id="ws-a")
        plan = self.migrator.plan()
        item = next(i for i in plan["items"] if i["offer_id"] == "acme-ws-only")
        self.assertEqual("workspace", item["owner_scope"]["kind"])
        self.assertEqual("ws-a", item["owner_scope"]["workspace_id"])

    def test_rollback_removes_exactly_the_applied_set(self) -> None:
        plan = self.migrator.plan()
        manifest_path = self.migrator.apply(plan)
        result = self.migrator.rollback(manifest_path)
        self.assertEqual(4, result["removed_count"])  # 2 products + 2 snapshots
        with self.assertRaises(Exception):
            get_product(self.root, plan["items"][0]["product_id"])

    def test_rollback_rejects_a_non_applied_manifest(self) -> None:
        import json as _json

        fake_manifest_path = self.root / "runtime" / "migrations" / "fake.json"
        fake_manifest_path.parent.mkdir(parents=True, exist_ok=True)
        fake_manifest_path.write_text(
            _json.dumps({"migration_id": "fake", "mode": "dry_run"}), encoding="utf-8"
        )
        with self.assertRaises(ProductMigrationError):
            self.migrator.rollback(fake_manifest_path)


class HarvestToPublishE2ETests(unittest.TestCase):
    """Epic 06 S06's own stop condition: 'catalogue compatible' -- an old
    harvest -> promote (legacy path) -> migrate -> v1 read must produce a
    stable, queryable, correctly-visible Product+Snapshot."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_harvest_promote_migrate_publish_end_to_end(self) -> None:
        ArtifactStore(self.root).write_yaml(
            self.root / "product_catalog" / "index.yaml", {"schema_version": "0.2", "offers": []}
        )
        harvest_id, candidate_id = _write_harvest(self.root, company="Acme Corp", name="Acme Suite")
        promoted = promote_candidate(
            self.root, candidate_id=f"{harvest_id}:{candidate_id}", offer_id="acme-suite-e2e",
        )
        self.assertEqual("acme-suite-e2e", promoted["offer_id"])

        migrator = ProductMigrator(self.root)
        plan = migrator.plan()
        item = next(i for i in plan["items"] if i["offer_id"] == "acme-suite-e2e")
        migrator.apply(plan)

        product = get_product(self.root, item["product_id"])
        snapshot = get_snapshot(self.root, item["snapshot_id"])
        self.assertEqual("active", product["status"])
        self.assertEqual("Automates onboarding", snapshot["content"]["description"])

        # Visible to any workspace, since the promoted offer carries no
        # workspace_id -- it's a shared-core product.
        visible = filter_visible_products([product], workspace_id="any-workspace")
        self.assertEqual(1, len(visible))


if __name__ == "__main__":
    unittest.main()
