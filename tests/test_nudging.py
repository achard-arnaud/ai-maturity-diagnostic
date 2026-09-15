from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import yaml

from app.core import ControlPlaneError
from app.nudging import UseCaseNudger


def write_inventory(root: Path, *, with_feedback: bool = True) -> None:
    path = root / "studies/acme/05b_use_case_inventory.yaml"
    path.parent.mkdir(parents=True)
    feedback = [{"statement": "Cycle time fell.", "outcome": "faster", "evidence_status": "observed", "source_claim_ids": ["F1"]}] if with_feedback else []
    path.write_text(
        yaml.safe_dump(
            {
                "schema_version": "0.6",
                "inventory_version": "2026-08-07.1",
                "study_id": "acme-1",
                "company": "Acme",
                "use_cases": [
                    {
                        "use_case_id": "UC-A",
                        "name": "Draft response",
                        "line_of_business": "Sales",
                        "workflow": "RFP",
                        "outcome_family": "commercial-response",
                        "evidence_status": "validated",
                        "maturity": "production",
                        "dependencies": {"depends_on": [], "enables": ["UC-B"]},
                        "repeatability": "high",
                        "variant_axes": ["country", "segment"],
                        "reusable_assets": ["prompt", "knowledge-base"],
                        "feedback": feedback,
                        "confidence": "high",
                        "unknowns": [],
                    },
                    {
                        "use_case_id": "UC-B",
                        "name": "Quality check",
                        "line_of_business": "Sales",
                        "workflow": "RFP",
                        "outcome_family": "commercial-response",
                        "evidence_status": "observed",
                        "maturity": "pilot",
                        "dependencies": {"depends_on": ["UC-A"], "enables": []},
                        "repeatability": "medium",
                        "variant_axes": [],
                        "reusable_assets": [],
                        "feedback": [],
                        "confidence": "medium",
                        "unknowns": ["Target precision"],
                    },
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )


class NudgingTests(unittest.TestCase):
    def test_all_three_modes_are_generated_from_inventory_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_inventory(root)
            result = UseCaseNudger(root).generate("acme-1", "all")
            modes = {item["mode"] for item in result["nudges"]}
            self.assertEqual({"productivization", "upsell_dependency", "cross_sell_package"}, modes)
            self.assertTrue(result["input_boundary"]["use_case_inventory_only"])
            self.assertFalse(result["input_boundary"]["icb_loaded"])
            self.assertFalse(result["input_boundary"]["sector_rollup_loaded"])
            self.assertFalse(result["input_boundary"]["product_fit_loaded"])

    def test_upsell_requires_explicit_dependency_edge(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_inventory(root)
            result = UseCaseNudger(root).generate("acme-1", "upsell_dependency")
            self.assertEqual(1, len(result["nudges"]))
            self.assertEqual(["UC-B"], result["nudges"][0]["target_use_case_ids"])

    def test_cross_sell_requires_recorded_company_feedback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_inventory(root, with_feedback=False)
            result = UseCaseNudger(root).generate("acme-1", "cross_sell_package")
            self.assertEqual([], result["nudges"])

    def test_sector_or_product_context_is_rejected_at_api_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_inventory(root)
            with self.assertRaises(ControlPlaneError):
                UseCaseNudger(root).generate_request({"study_id": "acme-1", "mode": "all", "sector_code": "301010"})
            with self.assertRaises(ControlPlaneError):
                UseCaseNudger(root).generate_request({"study_id": "acme-1", "offer_id": "OFFER-X"})

    def test_for_workspace_default_matches_legacy_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertEqual(UseCaseNudger.for_workspace("default", repo_root=root).root, root.resolve())

    def test_for_workspace_named_resolves_under_workspaces_tree(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            nudger = UseCaseNudger.for_workspace("acme", repo_root=root)
            self.assertEqual(nudger.root, (root / "workspaces" / "acme").resolve())


class NudgePersistenceTests(unittest.TestCase):
    def test_regenerating_unchanged_input_reuses_the_same_nudge_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_inventory(root)
            nudger = UseCaseNudger(root)
            first = nudger.generate("acme-1", "all")
            second = nudger.generate("acme-1", "all")
            first_ids = sorted(item["nudge_id"] for item in first["nudges"])
            second_ids = sorted(item["nudge_id"] for item in second["nudges"])
            self.assertEqual(first_ids, second_ids)
            persisted = nudger.list_nudges("acme-1")
            self.assertEqual(len(first_ids), len(persisted))

    def test_persisted_store_survives_across_nudger_instances(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_inventory(root)
            UseCaseNudger(root).generate("acme-1", "all")
            persisted = UseCaseNudger(root).list_nudges("acme-1")
            self.assertTrue(persisted)
            self.assertTrue(all(item["status"] == "hypothesis" for item in persisted))

    def test_accept_nudge_transitions_status_and_records_actor(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_inventory(root)
            nudger = UseCaseNudger(root)
            generated = nudger.generate("acme-1", "all")
            nudge_id = generated["nudges"][0]["nudge_id"]
            updated = nudger.accept_nudge("acme-1", nudge_id, actor="rep@acme.com")
            self.assertEqual("accepted", updated["status"])
            self.assertEqual("rep@acme.com", updated["decided_by"])
            self.assertTrue(updated["decided_at"])
            persisted = nudger.list_nudges("acme-1")
            self.assertEqual("accepted", next(item for item in persisted if item["nudge_id"] == nudge_id)["status"])

    def test_accept_nudge_is_idempotent_first_call_wins(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_inventory(root)
            nudger = UseCaseNudger(root)
            nudge_id = nudger.generate("acme-1", "all")["nudges"][0]["nudge_id"]
            first = nudger.accept_nudge("acme-1", nudge_id, actor="rep@acme.com")
            second = nudger.accept_nudge("acme-1", nudge_id, actor="someone-else@acme.com")
            self.assertEqual(first, second)
            self.assertEqual("rep@acme.com", second["decided_by"])

    def test_reject_after_accept_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_inventory(root)
            nudger = UseCaseNudger(root)
            nudge_id = nudger.generate("acme-1", "all")["nudges"][0]["nudge_id"]
            nudger.accept_nudge("acme-1", nudge_id, actor="rep@acme.com")
            with self.assertRaises(ControlPlaneError):
                nudger.reject_nudge("acme-1", nudge_id, actor="rep@acme.com")

    def test_reject_nudge_records_reason(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_inventory(root)
            nudger = UseCaseNudger(root)
            nudge_id = nudger.generate("acme-1", "all")["nudges"][0]["nudge_id"]
            updated = nudger.reject_nudge("acme-1", nudge_id, actor="rep@acme.com", reason="not relevant")
            self.assertEqual("rejected", updated["status"])
            self.assertEqual("not relevant", updated["decision_reason"])

    def test_decision_survives_regeneration(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_inventory(root)
            nudger = UseCaseNudger(root)
            nudge_id = nudger.generate("acme-1", "all")["nudges"][0]["nudge_id"]
            nudger.accept_nudge("acme-1", nudge_id, actor="rep@acme.com")
            regenerated = nudger.generate("acme-1", "all")
            decided = next(item for item in regenerated["nudges"] if item["nudge_id"] == nudge_id)
            self.assertEqual("accepted", decided["status"])

    def test_unknown_nudge_id_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_inventory(root)
            nudger = UseCaseNudger(root)
            nudger.generate("acme-1", "all")
            with self.assertRaises(ControlPlaneError):
                nudger.accept_nudge("acme-1", "NUD-does-not-exist", actor="rep@acme.com")

    def test_missing_actor_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_inventory(root)
            nudger = UseCaseNudger(root)
            nudge_id = nudger.generate("acme-1", "all")["nudges"][0]["nudge_id"]
            with self.assertRaises(ControlPlaneError):
                nudger.accept_nudge("acme-1", nudge_id, actor="")


if __name__ == "__main__":
    unittest.main()
