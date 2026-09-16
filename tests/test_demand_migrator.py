from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.demand_migrator import DemandMigrationError, DemandMigrator
from app.demand_store import get_demand, list_demands


def _write_study(root: Path, study_id: str, company: str, problem: str) -> None:
    study_dir = root / "studies" / study_id
    study_dir.mkdir(parents=True)
    (study_dir / "00_manifest.yaml").write_text(
        f"study_id: {study_id}\ncompany_id: {company}\ncompany: {company}\n", encoding="utf-8"
    )
    (study_dir / "05_enterprise_demand_profile.yaml").write_text(
        "schema_version: '0.2'\n"
        f"study_id: {study_id}\n"
        f"company: {company}\n"
        "evidence_claims:\n"
        f"  - claim_id: E1\n    statement: {problem}\n    source: manual_entry\n    evidence_status: hypothesis\n"
        "capability_gaps: []\n"
        "buying_context:\n  sponsors: []\n  terrain_owners: []\n  veto_players: []\n  timing_signals: []\n"
        "constraints:\n  technical: []\n  organizational: []\n  regulatory: []\n"
        "unknowns: []\nconfidence: low\n",
        encoding="utf-8",
    )


class DemandMigratorTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        _write_study(self.root, "acme-20260101", "Acme", "manual onboarding")
        _write_study(self.root, "globex-20260102", "Globex", "manual reporting")
        self.migrator = DemandMigrator(self.root, "default")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_plan_finds_both_studies(self) -> None:
        plan = self.migrator.plan()
        self.assertEqual(2, plan["counts"]["studies"])
        self.assertEqual("dry_run", plan["mode"])

    def test_plan_is_deterministic_across_calls(self) -> None:
        plan_a = self.migrator.plan()
        plan_b = self.migrator.plan()
        ids_a = sorted(item["demand_id"] for item in plan_a["items"])
        ids_b = sorted(item["demand_id"] for item in plan_b["items"])
        self.assertEqual(ids_a, ids_b)

    def test_plan_carries_content_hash_per_item(self) -> None:
        plan = self.migrator.plan()
        for item in plan["items"]:
            self.assertEqual(64, len(item["content_hash"]))

    def test_apply_creates_demands_and_manifest(self) -> None:
        plan = self.migrator.plan()
        manifest_path = self.migrator.apply(plan)
        self.assertTrue(manifest_path.is_file())
        page = list_demands(self.root, "default")
        self.assertEqual(2, len(page.items))

    def test_apply_preserves_problem_statement(self) -> None:
        plan = self.migrator.plan()
        self.migrator.apply(plan)
        demand_id = next(item["demand_id"] for item in plan["items"] if item["study_id"] == "acme-20260101")
        demand, _version = get_demand(self.root, "default", demand_id)
        self.assertEqual("manual onboarding", demand["problem"]["value"])

    def test_apply_is_idempotent_on_rerun(self) -> None:
        plan = self.migrator.plan()
        self.migrator.apply(plan)
        second_plan = self.migrator.plan()
        self.migrator.apply(second_plan)  # should skip, not raise or duplicate
        page = list_demands(self.root, "default")
        self.assertEqual(2, len(page.items))

    def test_apply_wrong_workspace_plan_rejected(self) -> None:
        plan = self.migrator.plan()
        other = DemandMigrator(self.root, "other-ws")
        with self.assertRaises(DemandMigrationError):
            other.apply(plan)

    def test_rollback_removes_exactly_the_applied_demands(self) -> None:
        plan = self.migrator.plan()
        manifest_path = self.migrator.apply(plan)
        before_rollback = list_demands(self.root, "default")
        self.assertEqual(2, len(before_rollback.items))

        result = self.migrator.rollback(manifest_path)
        self.assertEqual(2, result["removed_count"])

        after_rollback = list_demands(self.root, "default")
        self.assertEqual(0, len(after_rollback.items))

    def test_rollback_validated_n_minus_1(self) -> None:
        # Apply migration A (2 studies), then a manually-created third
        # demand outside this migration; rollback of A must remove
        # exactly its own 2, leaving the third (N-1 semantics: only the
        # applied set is reverted, nothing else).
        plan = self.migrator.plan()
        manifest_path = self.migrator.apply(plan)

        from app.demand_store import create_demand
        from app.demand_policy import known, unknown

        create_demand(
            self.root, "default",
            {
                "demand_id": "manual-demand",
                "workspace_id": "default",
                "company_entity_id": "entity_manual",
                "status": "observed",
                "problem": known("manually entered"),
                "population": unknown(), "impact": unknown(), "urgency": unknown(),
                "initiative": unknown(), "sponsor": unknown(), "budget": unknown(), "timing": unknown(),
                "claim_ids": [], "origin_profile_ref": None,
                "created_at": "2026-01-01T00:00:00+00:00", "updated_at": "2026-01-01T00:00:00+00:00",
            },
        )
        self.assertEqual(3, len(list_demands(self.root, "default").items))

        self.migrator.rollback(manifest_path)
        remaining = list_demands(self.root, "default")
        self.assertEqual(1, len(remaining.items))
        self.assertEqual("manual-demand", remaining.items[0]["demand_id"])

    def test_rollback_rejects_manifest_from_wrong_workspace(self) -> None:
        plan = self.migrator.plan()
        manifest_path = self.migrator.apply(plan)
        other = DemandMigrator(self.root, "other-ws")
        with self.assertRaises(DemandMigrationError):
            other.rollback(manifest_path)


if __name__ == "__main__":
    unittest.main()
