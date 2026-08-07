from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import yaml

from app.dashboard import FollowUpDashboard, UseCaseHeritage


def dump(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


class DashboardTests(unittest.TestCase):
    def test_follow_up_surfaces_qualification_resolver_before_technical_todo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            study = root / "studies/acme"
            dump(study / "00_manifest.yaml", {"study_id": "acme-1", "company": "Acme", "company_id": "C1", "product_snapshots": []})
            dump(study / "05_enterprise_demand_profile.yaml", {"evidence_claims": [], "capability_gaps": [], "confidence": "low"})
            dump(root / "artifacts/TODO_productization_v0_7.yaml", {"items": [{"id": "T1", "priority": "P2", "status": "open", "area": "quality", "task": "Later technical task"}]})
            rows = FollowUpDashboard(root).items()
            business = next(item for item in rows if item["kind"] == "qualification")
            self.assertEqual("P0", business["priority"])
            self.assertEqual("enterprise-demand-intelligence", business["resolver"]["owner_skill"])
            self.assertEqual("Compléter la demande", business["resolver"]["cta_label"])
            self.assertTrue(any(item["kind"] == "technical_todo" for item in rows))

    def test_company_heritage_counts_derived_edges(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            study = root / "studies/acme"
            dump(study / "05b_use_case_inventory.yaml", {
                "study_id": "acme-1", "company": "Acme", "inventory_version": "1",
                "use_cases": [
                    {"use_case_id": "UC-1", "name": "Draft", "outcome_family": "quality", "dependencies": {"enables": ["UC-2"], "depends_on": []}, "reusable_assets": []},
                    {"use_case_id": "UC-2", "name": "Review", "outcome_family": "quality", "dependencies": {"enables": [], "depends_on": ["UC-1"]}, "reusable_assets": []},
                ],
            })
            heritage = UseCaseHeritage(root).company("acme-1")
            self.assertEqual(2, heritage["use_case_count"])
            self.assertGreaterEqual(heritage["edge_count"], 2)
            self.assertIn("enables", heritage["relations"])

    def test_sector_heritage_keeps_comparative_warning(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name, cid in (("a", "C1"), ("b", "C2")):
                dump(root / f"studies/{name}/05b_use_case_inventory.yaml", {"study_id": name, "company_id": cid, "company": name.upper(), "use_cases": [{"use_case_id": "UC-1", "name": "X", "outcome_family": "quality"}]})
            jsonl(root / "data/private/network/company_icb_mappings.jsonl", [
                {"company_id": "C1", "mapping_status": "validated", "sector": {"code": "301010"}},
                {"company_id": "C2", "mapping_status": "validated", "sector": {"code": "301010"}},
            ])
            heritage = UseCaseHeritage(root).sector("301010")
            self.assertEqual(2, heritage["company_count"])
            self.assertGreaterEqual(heritage["similarity_hypotheses"], 1)
            self.assertIn("never populates", heritage["warning"])


if __name__ == "__main__":
    unittest.main()
