from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import yaml

from app.workflows import WorkflowPlanner


def dump(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


def assert_blocked_steps_have_resolver(test: unittest.TestCase, plan: dict) -> None:
    for step in plan.get("steps", []):
        if step.get("status") == "blocked":
            test.assertIn("resolver", step, f"blocked step {step.get('id')} has no resolver")
            resolver = step["resolver"]
            test.assertTrue(resolver.get("cta_label"), step.get("id"))
            test.assertTrue(resolver.get("postcondition"), step.get("id"))
            test.assertTrue(resolver.get("owner_skill") or resolver.get("human_action"), step.get("id"))


class BlockerCompletenessTests(unittest.TestCase):
    def seed(self, root: Path) -> None:
        dump(root / "data/taxonomies/icb_v5_2026.yaml", {"industries": [{"code": "30", "name": "Financials", "supersectors": [{"code": "3010", "name": "Banks", "sectors": [{"code": "301010", "name": "Banks"}]}]}]})
        jsonl(root / "data/private/network/companies.jsonl", [{"company_id": "C1", "canonical_name": "Acme"}])
        jsonl(root / "data/private/network/company_icb_mappings.jsonl", [{"company_id": "C1", "mapping_status": "validated", "confidence": "high", "sector": {"code": "301010", "name": "Banks"}}])
        dump(root / "product_catalog/index.yaml", {"schema_version": "0.2", "catalog_version": "1", "offers": [{"offer_id": "O1", "name": "Offer", "status": "draft", "file": "O1.yaml"}]})
        dump(root / "product_catalog/O1.yaml", {"schema_version": "0.2", "offer": {"offer_id": "O1", "name": "Offer", "profile_version": "v1", "status": "draft", "unknowns": ["proof"], "proof": {"evidence_grade": "U1"}}})
        study = root / "studies/acme"
        dump(study / "00_manifest.yaml", {"study_id": "acme-1", "company_id": "C1", "company": "Acme", "updated_at": "2026-08-07", "product_snapshots": []})
        dump(study / "05_enterprise_demand_profile.yaml", {"evidence_claims": [], "capability_gaps": [], "confidence": "low"})

    def test_every_active_blocker_has_an_actionable_resolver(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.seed(root)
            planner = WorkflowPlanner(root)
            plans = [
                planner.plan({"kind": "demand", "sector_code": "301010"}),
                planner.plan({"kind": "company", "study_id": "acme-1"}),
                planner.plan({"kind": "offer", "offer_id": "O1"}),
                planner.plan({"kind": "qualification", "study_id": "acme-1"}),
                planner.plan({"kind": "reach", "study_id": "acme-1"}),
                planner.plan({"kind": "nudging", "study_id": "acme-1"}),
            ]
            for plan in plans:
                assert_blocked_steps_have_resolver(self, plan)


if __name__ == "__main__":
    unittest.main()
