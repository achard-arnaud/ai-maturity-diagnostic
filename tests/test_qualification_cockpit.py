from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import yaml

from app.qualification import QualificationCockpit


def dump(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


class QualificationCockpitTests(unittest.TestCase):
    def seed_ready_study(self, root: Path) -> Path:
        study = root / "studies/acme"
        dump(study / "00_manifest.yaml", {"study_id": "acme-1", "company": "Acme", "company_id": "C1", "product_snapshots": [{"offer_id": "OFFER-1", "path": "inputs/x.yaml"}]})
        dump(study / "05_enterprise_demand_profile.yaml", {"evidence_claims": [{"claim_id": "E1"}], "capability_gaps": [{"claim_id": "G1"}], "confidence": "medium"})
        return study

    def positive_fit(self, study: Path, decision: str = "validate", gates: list[dict] | None = None) -> None:
        dump(study / "06_product_fit_matrix.yaml", {"recommended_offer_id": "OFFER-1", "decision": decision, "matches": [{"offer_id": "OFFER-1", "decision": decision, "hard_gates": gates or []}]})

    def test_matching_has_resolver_when_demand_and_snapshots_are_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); study = self.seed_ready_study(root)
            dump(study / "06_product_fit_matrix.yaml", {"matches": [], "decision": None})
            row = QualificationCockpit(root).list_studies()[0]
            self.assertEqual("matching", row["stage"])
            self.assertEqual("opportunity-fit-matching", row["next_skill"])
            self.assertEqual("blocked", row["steps"][2]["status"])
            self.assertEqual("Résoudre le matching", row["current_blocker"]["cta_label"])

    def test_nurture_stops_downstream_with_human_review_action(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); study = self.seed_ready_study(root)
            dump(study / "06_product_fit_matrix.yaml", {"matches": [{"offer_id": "OFFER-1", "decision": "nurture"}], "decision": "nurture"})
            row = QualificationCockpit(root).list_studies()[0]
            self.assertEqual("stopped", row["stage"])
            self.assertEqual("Revoir la décision", row["current_blocker"]["cta_label"])
            self.assertEqual("locked", row["steps"][3]["status"])
            self.assertEqual("locked", row["steps"][4]["status"])
            self.assertEqual("locked", row["steps"][5]["status"])

    def test_invalid_positive_fit_returns_to_matching(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); study = self.seed_ready_study(root)
            self.positive_fit(study, "pursue", [{"id": "GATE-1", "status": "FAIL", "severity": "blocker"}])
            row = QualificationCockpit(root).list_studies()[0]
            self.assertEqual("matching_invalid", row["stage"])
            self.assertEqual("opportunity-fit-matching", row["next_skill"])
            self.assertFalse(row["artifacts"]["fit_progression_allowed"])
            self.assertEqual("review", row["steps"][2]["status"])
            self.assertEqual("locked", row["steps"][3]["status"])

    def test_validate_with_open_gate_can_reach_contact_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); study = self.seed_ready_study(root)
            self.positive_fit(study, "validate", [{"id": "GATE-1", "status": "OPEN", "severity": "blocker"}])
            row = QualificationCockpit(root).list_studies()[0]
            self.assertEqual("contact_targeting", row["stage"])
            self.assertTrue(row["artifacts"]["fit_progression_allowed"])
            self.assertEqual("Cibler les contacts", row["current_blocker"]["cta_label"])

    def test_empty_contact_artifact_routes_to_second_round(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); study = self.seed_ready_study(root); self.positive_fit(study)
            dump(study / "06b_contact_targets.yaml", {"study_id": "acme-1", "company_id": "C1", "offer_id": "OFFER-1", "targets": []})
            row = QualificationCockpit(root).list_studies()[0]
            self.assertEqual("tech-leadership-org-intelligence", row["next_skill"])
            self.assertEqual("Élargir le 2e tour", row["current_blocker"]["cta_label"])

    def test_reach_is_required_before_pilot(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); study = self.seed_ready_study(root); self.positive_fit(study)
            dump(study / "06b_contact_targets.yaml", {"study_id": "acme-1", "company_id": "C1", "offer_id": "OFFER-1", "targets": [{"person_id": "P1"}]})
            row = QualificationCockpit(root).list_studies()[0]
            self.assertEqual("reach", row["stage"])
            self.assertEqual("blocked", row["steps"][4]["status"])
            self.assertEqual("locked", row["steps"][5]["status"])
            dump(study / "06c_reach_strategy.yaml", {"stakeholders": [{"person_id": "P1", "status": "ready"}], "blockers": []})
            refreshed = QualificationCockpit(root).list_studies()[0]
            self.assertEqual("pilot", refreshed["stage"])


if __name__ == "__main__":
    unittest.main()
