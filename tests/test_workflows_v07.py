from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import yaml

from app.core import ControlPlaneError
from app.workflows import WorkflowPlanner


def dump(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


class WorkflowPlannerV07Tests(unittest.TestCase):
    def seed(self, root: Path, *, with_value_analysis: bool = True, with_reach: bool = False) -> None:
        dump(root / "data/taxonomies/icb_v5_2026.yaml", {
            "industries": [{"code": "30", "name": "Financials", "supersectors": [{"code": "3010", "name": "Banks", "sectors": [{"code": "301010", "name": "Banks"}]}]}]
        })
        jsonl(root / "data/private/network/companies.jsonl", [{"company_id": "C1", "canonical_name": "Acme Bank"}])
        jsonl(root / "data/private/network/company_icb_mappings.jsonl", [{"company_id": "C1", "mapping_status": "validated", "confidence": "high", "sector": {"code": "301010", "name": "Banks"}}])

        dump(root / "product_catalog/index.yaml", {"schema_version": "0.2", "catalog_version": "v1", "offers": [{"offer_id": "OFFER-1", "name": "Offer One", "status": "draft", "file": "OFFER-1.yaml"}]})
        dump(root / "product_catalog/OFFER-1.yaml", {"schema_version": "0.2", "offer": {"offer_id": "OFFER-1", "name": "Offer One", "profile_version": "v1", "status": "draft", "unknowns": ["reference"], "proof": {"evidence_grade": "U1"}, "icp": {"personas": {"economic_sponsors": ["CIO"]}}}})

        study = root / "studies/acme"
        snapshot = "inputs/product_snapshots/OFFER-1__v1.yaml"
        dump(study / "00_manifest.yaml", {"study_id": "acme-1", "company_id": "C1", "company": "Acme Bank", "updated_at": "2026-08-07", "product_snapshots": [{"offer_id": "OFFER-1", "path": snapshot}]})
        dump(study / snapshot, {"offer": {"offer_id": "OFFER-1", "profile_version": "v1", "icp": {"personas": {"economic_sponsors": ["CIO"]}}}})
        dump(study / "05_enterprise_demand_profile.yaml", {"company": "Acme Bank", "evidence_claims": [{"claim_id": "E1"}], "capability_gaps": [{"claim_id": "G1"}], "confidence": "high"})
        dump(study / "05b_use_case_inventory.yaml", {"study_id": "acme-1", "company_id": "C1", "company": "Acme Bank", "inventory_version": "1", "use_cases": [{"use_case_id": "UC-1", "name": "Request triage", "workflow": "Requests", "line_of_business": "Operations", "outcome_family": "cycle-time", "evidence_status": "validated", "maturity": "pilot", "dependencies": {"depends_on": [], "enables": []}, "repeatability": "medium", "variant_axes": [], "reusable_assets": [], "feedback": [], "confidence": "high", "unknowns": []}]})
        if with_value_analysis:
            dump(study / "05c_value_chain_causal_map.yaml", {"analyses": [{"use_case_id": "UC-1", "evidence_refs": ["E1"], "porter": {"upstream": [], "focal_activity": "Triage", "downstream": [], "support_activities": [], "handoffs": [], "control_points": [], "value_effects": {"value": [], "cost": [], "quality": [], "time": [], "risk": []}}, "ishikawa": {"people": [], "process": [], "technology": [], "data": [], "governance_control": [], "environment_external": []}, "adjacent_workflow_hypotheses": [], "validation_questions": [], "confidence": "medium"}]})
        dump(study / "06_product_fit_matrix.yaml", {"recommended_offer_id": "OFFER-1", "decision": "validate", "matches": [{"offer_id": "OFFER-1", "product_profile_version": "v1", "decision": "validate", "hard_gates": []}]})
        dump(study / "06b_contact_targets.yaml", {"study_id": "acme-1", "company_id": "C1", "offer_id": "OFFER-1", "targets": [{"person_id": "P1", "target_id": "T1", "role_hypotheses": ["economic_sponsor"], "persona_matches": ["CIO"], "target_score": 80, "current_role_status": "current", "required_validations": []}]})
        if with_reach:
            dump(study / "06c_reach_strategy.yaml", {"stakeholders": [{"person_id": "P1", "status": "ready"}], "blockers": []})

    def test_demand_company_offer_qualification_and_nudging_plans(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); self.seed(root)
            planner = WorkflowPlanner(root)
            demand = planner.plan({"kind": "demand", "sector_code": "301010"})
            self.assertEqual("demand", demand["kind"])
            self.assertEqual("blocked", demand["steps"][-1]["status"])
            self.assertEqual("Compléter la couverture", demand["steps"][-1]["resolver"]["cta_label"])

            company = planner.plan({"kind": "company", "study_id": "acme-1"})
            self.assertEqual(1, company["current"]["use_cases"])
            self.assertEqual(1, company["current"]["value_chain_analyses"])

            offer = planner.plan({"kind": "offer", "offer_id": "OFFER-1"})
            owner = next(step for step in offer["steps"] if step["id"] == "owner_review")
            self.assertEqual("blocked", owner["status"])
            self.assertEqual("Valider l'offre", owner["resolver"]["cta_label"])

            qualification = planner.plan({"kind": "qualification", "study_id": "acme-1"})
            self.assertEqual("reach", qualification["stage"])
            self.assertEqual("Construire / résoudre le reach", qualification["current_blocker"]["cta_label"])

            nudging = planner.plan({"kind": "nudging", "study_id": "acme-1"})
            self.assertEqual("completed", nudging["steps"][0]["status"])
            self.assertEqual("blocked", nudging["steps"][3]["status"])
            self.assertEqual("Revoir les nudges", nudging["steps"][3]["resolver"]["cta_label"])

    def test_value_chain_plan_blocks_when_analysis_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); self.seed(root, with_value_analysis=False)
            plan = WorkflowPlanner(root).plan({"kind": "value_chain", "study_id": "acme-1", "use_case_id": "UC-1"})
            step = next(item for item in plan["steps"] if item["id"] == "porter_ishikawa")
            self.assertEqual("blocked", step["status"])
            self.assertEqual("Analyser la chaîne de valeur", step["resolver"]["cta_label"])

    def test_reach_plan_exposes_missing_stakeholder_lane_resolver(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); self.seed(root)
            plan = WorkflowPlanner(root).plan({"kind": "reach", "study_id": "acme-1"})
            reach = next(item for item in plan["steps"] if item["id"] == "reach")
            self.assertEqual("blocked", reach["status"])
            self.assertTrue(reach["resolver"]["owner_skill"] in {"tech-leadership-org-intelligence", "opportunity-fit-matching", "person-opportunity-targeting"})

    def test_company_plan_resolves_missing_inventory_and_value_analysis(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); self.seed(root, with_value_analysis=False)
            inventory_path = root / "studies/acme/05b_use_case_inventory.yaml"
            inventory_path.unlink()
            plan = WorkflowPlanner(root).plan({"kind": "company", "study_id": "acme-1"})
            use_cases = next(item for item in plan["steps"] if item["id"] == "use_cases")
            self.assertEqual("blocked", use_cases["status"])
            self.assertEqual("Récolter les use cases", use_cases["resolver"]["cta_label"])

    def test_invalid_workflow_kind_and_missing_targets_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); self.seed(root)
            planner = WorkflowPlanner(root)
            with self.assertRaises(ControlPlaneError):
                planner.plan({"kind": "unknown"})
            with self.assertRaises(ControlPlaneError):
                planner.plan({"kind": "value_chain", "study_id": "acme-1"})
            with self.assertRaises(ControlPlaneError):
                planner.plan({"kind": "offer", "offer_id": "NOPE"})


if __name__ == "__main__":
    unittest.main()
