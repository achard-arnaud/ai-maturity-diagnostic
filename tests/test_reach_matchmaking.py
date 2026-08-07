from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import yaml

from app.core import ControlPlaneError
from app.reach import ReachMatchmaker


def dump(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


class ReachMatchmakerTests(unittest.TestCase):
    def seed(self, root: Path, *, stale_second: bool = False, open_gate: bool = False) -> Path:
        study = root / "studies/acme"
        snapshot = "inputs/product_snapshots/OFFER-1__v1.yaml"
        dump(study / "00_manifest.yaml", {
            "study_id": "acme-1", "company_id": "C1", "company": "Acme",
            "product_snapshots": [{"offer_id": "OFFER-1", "path": snapshot}],
        })
        dump(study / snapshot, {"offer": {"offer_id": "OFFER-1", "profile_version": "v1", "icp": {"personas": {"economic_sponsors": ["CIO"], "terrain_owners": ["Transformation_Lead"], "veto_players": ["CISO"]}}}})
        gates = [{"id": "G1", "status": "OPEN", "severity": "blocker"}] if open_gate else []
        dump(study / "06_product_fit_matrix.yaml", {
            "recommended_offer_id": "OFFER-1", "decision": "validate",
            "matches": [{"offer_id": "OFFER-1", "product_profile_version": "v1", "decision": "validate", "hard_gates": gates}],
        })
        dump(study / "05_enterprise_demand_profile.yaml", {"company": "Acme", "evidence_claims": [{"claim_id": "E1"}], "capability_gaps": [{"claim_id": "GAP1"}], "confidence": "high"})
        dump(study / "04_newsflow_evidence.yaml", {"claims": [{"claim_id": "N1", "statement": "New transformation program launched", "epistemic_status": "fact"}]})
        dump(study / "05b_use_case_inventory.yaml", {"study_id": "acme-1", "company": "Acme", "use_cases": [{"use_case_id": "UC-1", "name": "Workflow assistant", "line_of_business": "Operations", "outcome_family": "cycle-time", "evidence_status": "validated"}]})
        dump(study / "06b_contact_targets.yaml", {
            "study_id": "acme-1", "company_id": "C1", "offer_id": "OFFER-1", "fit_decision": "validate",
            "targets": [
                {"person_id": "P1", "target_id": "T1", "role_hypotheses": ["economic_sponsor"], "persona_matches": ["CIO"], "target_score": 80, "current_role_status": "current", "required_validations": ["Confirm mandate"]},
                {"person_id": "P2", "target_id": "T2", "role_hypotheses": ["terrain_owner"], "persona_matches": ["Transformation_Lead"], "target_score": 45, "current_role_status": "stale" if stale_second else "current", "required_validations": ["Confirm role"]},
            ],
        })
        return study

    def test_reach_bridges_fit_icp_people_use_cases_and_newsflow_without_recomputing_fit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); self.seed(root)
            result = ReachMatchmaker(root).preview("acme-1")
            first = [item for item in result["stakeholders"] if item["wave"] == "first"]
            second = [item for item in result["stakeholders"] if item["wave"] == "second"]
            self.assertTrue(first)
            self.assertTrue(second)
            self.assertIn("promoter", first[0]["stakeholder_roles"])
            self.assertEqual("New transformation program launched", first[0]["why_now"])
            self.assertFalse(result["boundaries"]["recomputes_fit"])
            self.assertFalse(result["boundaries"]["newsflow_changes_fit"])
            self.assertEqual("UC-1", result["relevant_use_cases"][0]["use_case_id"])

    def test_stale_role_becomes_validation_only_with_resolver(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); self.seed(root, stale_second=True)
            result = ReachMatchmaker(root).preview("acme-1")
            stale = next(item for item in result["stakeholders"] if item["person_id"] == "P2")
            self.assertEqual("validation_only", stale["wave"])
            role_blocker = next(item for item in result["blockers"] if item["category"] == "role")
            self.assertEqual("person-opportunity-targeting", role_blocker["owner_skill"])
            self.assertEqual("Valider le rôle actuel", role_blocker["cta_label"])

    def test_missing_prescriber_lane_routes_second_round_org_expansion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); self.seed(root)
            result = ReachMatchmaker(root).preview("acme-1")
            missing = [item for item in result["blockers"] if item["category"] == "organization"]
            self.assertTrue(any("prescripteur" in item["message"] for item in missing))
            self.assertTrue(all(item["cta_label"] == "Élargir le 2e tour" for item in missing))

    def test_open_fit_gate_is_carried_into_reach_as_validation_blocker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); self.seed(root, open_gate=True)
            result = ReachMatchmaker(root).preview("acme-1")
            gate = next(item for item in result["blockers"] if item["category"] == "fit_gate")
            self.assertEqual("opportunity-fit-matching", gate["owner_skill"])
            self.assertIn("OPEN", gate["message"])

    def test_non_positive_fit_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); study = self.seed(root)
            dump(study / "06_product_fit_matrix.yaml", {"decision": "nurture", "matches": [{"offer_id": "OFFER-1", "decision": "nurture"}]})
            with self.assertRaises(ControlPlaneError):
                ReachMatchmaker(root).preview("acme-1")


if __name__ == "__main__":
    unittest.main()
