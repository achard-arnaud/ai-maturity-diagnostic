from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import yaml

from app.core import ControlPlaneError
from app.value_chain import ValueChainCatalog


def dump(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


class ValueChainCatalogTests(unittest.TestCase):
    def seed(self, root: Path) -> Path:
        study = root / "studies/acme"
        dump(study / "00_manifest.yaml", {"study_id": "acme-1", "company": "Acme"})
        dump(study / "05b_use_case_inventory.yaml", {
            "schema_version": "0.6", "inventory_version": "1", "study_id": "acme-1", "company": "Acme",
            "use_cases": [{"use_case_id": "UC-1", "name": "Request triage", "workflow": "Requests", "evidence_status": "validated", "confidence": "high"}],
        })
        dump(study / "05_enterprise_demand_profile.yaml", {"evidence_claims": [{"claim_id": "E1"}]})
        return study

    def test_missing_analysis_prepares_owner_skill_without_auto_promotion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); self.seed(root)
            prepared = ValueChainCatalog(root).prepare_request({"study_id": "acme-1", "use_case_id": "UC-1"})
            self.assertEqual("enterprise-value-chain-causal-analysis", prepared["skill"])
            self.assertFalse(prepared["automatic_use_case_promotion"])
            self.assertIn("05b_use_case_inventory.yaml", prepared["context_paths"][0])
            self.assertIn("Porter", prepared["input"])
            self.assertIn("Ishikawa", prepared["input"])

    def test_existing_analysis_keeps_adjacent_workflow_as_hypothesis(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); study = self.seed(root)
            dump(study / "05c_value_chain_causal_map.yaml", {
                "schema_version": "0.7", "study_id": "acme-1", "company": "Acme",
                "analyses": [{
                    "use_case_id": "UC-1", "evidence_refs": ["E1"],
                    "porter": {"upstream": [], "focal_activity": "Triage", "downstream": [], "support_activities": [], "handoffs": [], "control_points": [], "value_effects": {"value": [], "cost": [], "quality": [], "time": [], "risk": []}},
                    "ishikawa": {"people": [], "process": ["manual routing"], "technology": [], "data": [], "governance_control": [], "environment_external": []},
                    "adjacent_workflow_hypotheses": [{"label": "Quality review", "relation": "downstream", "basis": "handoff", "status": "hypothesis", "candidate_use_case_id": None}],
                    "validation_questions": ["Is quality review recurrent?"], "unknowns": [], "confidence": "medium",
                }],
            })
            result = ValueChainCatalog(root).study("acme-1")
            self.assertEqual("completed", result["use_cases"][0]["analysis_status"])
            hypothesis = result["use_cases"][0]["analysis"]["adjacent_workflow_hypotheses"][0]
            self.assertEqual("hypothesis", hypothesis["status"])

    def test_unknown_uc_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); self.seed(root)
            with self.assertRaises(ControlPlaneError):
                ValueChainCatalog(root).prepare_request({"study_id": "acme-1", "use_case_id": "UC-X"})


if __name__ == "__main__":
    unittest.main()
