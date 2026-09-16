from __future__ import annotations

import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from app.network_v1_migrator import NetworkMigrationError, NetworkV1Migrator
from app.network_v1_store import get_entity, list_entities


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8")


class NetworkV1MigratorTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        legacy = self.root / "data" / "private" / "network"

        _write_jsonl(
            legacy / "companies.jsonl",
            [
                {
                    "company_id": "COMP-1",
                    "canonical_name": "Acme Corp",
                    "aliases": [],
                    "countries": ["FR"],
                    "relationship_ids": ["REL-1"],
                    "source_batch_ids": [],
                    "workspace_id": "ws-a",
                    "status": "active",
                    "last_updated": "2026-01-01",
                    "stale_after_months": 6,
                },
                {
                    "company_id": "COMP-2",
                    "canonical_name": "Other Workspace Co",
                    "aliases": [],
                    "countries": ["US"],
                    "relationship_ids": [],
                    "source_batch_ids": [],
                    "workspace_id": "ws-b",
                    "status": "active",
                    "last_updated": "2026-01-01",
                    "stale_after_months": 6,
                },
            ],
        )
        _write_jsonl(
            legacy / "people.jsonl",
            [
                {
                    "person_id": "PERS-1",
                    "display_name": "Jane Doe",
                    "seed_company_id": "COMP-1",
                    "identity_key_basis": "normalized_name_and_company",
                    "relationship_ids": ["REL-1"],
                    "role_hypotheses": [],
                    "source_batch_ids": [],
                    "status": "active",
                    "last_updated": "2026-01-01",
                    "stale_after_months": 6,
                },
                {
                    "person_id": "PERS-2",
                    "display_name": "Other Workspace Person",
                    "seed_company_id": "COMP-2",
                    "identity_key_basis": "normalized_name_and_company",
                    "relationship_ids": [],
                    "role_hypotheses": [],
                    "source_batch_ids": [],
                    "status": "active",
                    "last_updated": "2026-01-01",
                    "stale_after_months": 6,
                },
            ],
        )
        _write_jsonl(
            legacy / "relationships.jsonl",
            [
                {
                    "relationship_id": "REL-1",
                    "person_id": "PERS-1",
                    "company_id": "COMP-1",
                    "job_title": "VP Engineering",
                    "country": "FR",
                    "relationship_type": "employment",
                    "current_status": "current",
                    "role_hypotheses": [],
                    "source_refs": ["evidence-1"],
                    "observed_at": "2026-01-01",
                    "epistemic_status": "fact",
                    "evidence_grade": "P1",
                    "requires_validation": False,
                },
            ],
        )

        self.migrator = NetworkV1Migrator(repo_root=self.root, workspace_id="ws-a")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_dry_run_scopes_to_the_target_workspace_only(self) -> None:
        plan = self.migrator.plan(as_of=date(2026, 6, 1))
        self.assertEqual(1, plan["counts"]["people"])
        self.assertEqual(1, plan["counts"]["companies"])
        self.assertEqual(1, plan["counts"]["relationships"])

    def test_dry_run_does_not_write_anything(self) -> None:
        self.migrator.plan(as_of=date(2026, 6, 1))
        self.assertFalse((self.root / "data" / "private" / "network_v1").exists())

    def test_apply_requires_a_dry_run_plan_for_the_same_workspace(self) -> None:
        other_migrator = NetworkV1Migrator(repo_root=self.root, workspace_id="ws-b")
        plan = self.migrator.plan(as_of=date(2026, 6, 1))
        with self.assertRaises(NetworkMigrationError):
            other_migrator.apply(plan)

    def test_apply_backfills_v1_store_and_legacy_ids_link_back(self) -> None:
        plan = self.migrator.plan(as_of=date(2026, 6, 1))
        self.migrator.apply(plan)

        people_page = list_entities(self.root, "ws-a", "person")
        self.assertEqual(1, len(people_page.items))
        self.assertEqual(["PERS-1"], people_page.items[0]["legacy_ids"])

        companies_page = list_entities(self.root, "ws-a", "company")
        self.assertEqual(["COMP-1"], companies_page.items[0]["legacy_ids"])

    def test_apply_is_deterministic_across_repeated_dry_runs(self) -> None:
        # Migration rehearsal: running the dry-run twice must plan the same
        # entity_ids both times (reproducibility is the whole point of a
        # rehearsal-first migration).
        plan_1 = self.migrator.plan(as_of=date(2026, 6, 1))
        plan_2 = self.migrator.plan(as_of=date(2026, 6, 1))
        ids_1 = {item["legacy_id"]: item["entity_id"] for item in plan_1["items"]}
        ids_2 = {item["legacy_id"]: item["entity_id"] for item in plan_2["items"]}
        self.assertEqual(ids_1, ids_2)

    def test_legacy_jsonl_files_are_untouched_by_apply(self) -> None:
        legacy_people_path = self.root / "data" / "private" / "network" / "people.jsonl"
        before = legacy_people_path.read_text(encoding="utf-8")
        plan = self.migrator.plan(as_of=date(2026, 6, 1))
        self.migrator.apply(plan)
        after = legacy_people_path.read_text(encoding="utf-8")
        self.assertEqual(before, after)

    def test_rollback_removes_only_this_migrations_entities(self) -> None:
        plan = self.migrator.plan(as_of=date(2026, 6, 1))
        manifest_path = self.migrator.apply(plan)

        self.migrator.rollback(manifest_path)

        from app.network_v1_store import EntityNotFound

        with self.assertRaises(EntityNotFound):
            get_entity(self.root, "ws-a", "person", people_entity_id_from(plan))


def people_entity_id_from(plan: dict) -> str:
    for item in plan["items"]:
        if item["kind"] == "person":
            return item["entity_id"]
    raise AssertionError("no person in plan")


if __name__ == "__main__":
    unittest.main()
