from __future__ import annotations

import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

import yaml

from app.demand import DemandCatalog


def dump_yaml(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def dump_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


class DemandCatalogTests(unittest.TestCase):
    def make_root(self, tmp: str, count: int) -> Path:
        root = Path(tmp)
        dump_yaml(
            root / "data/taxonomies/icb_v5_2026.yaml",
            {"industries": [{"code": "30", "name": "Financials", "supersectors": [{"code": "3010", "name": "Banks", "sectors": [{"code": "301010", "name": "Banks"}]}]}]},
        )
        companies = []
        mappings = []
        for index in range(1, count + 1):
            company_id = f"C{index}"
            companies.append({"company_id": company_id, "canonical_name": f"Bank {index}"})
            mappings.append({"company_id": company_id, "mapping_status": "validated", "confidence": "high", "sector": {"code": "301010", "name": "Banks"}})
            study = root / "studies" / f"bank-{index}"
            dump_yaml(study / "00_manifest.yaml", {"study_id": f"study-{index}", "company_id": company_id, "company": f"Bank {index}", "updated_at": "2026-08-01"})
            dump_yaml(study / "05_enterprise_demand_profile.yaml", {"evidence_claims": [{"claim_id": "E1"}], "capability_gaps": [{"claim_id": "G1"}], "confidence": "medium"})
        dump_jsonl(root / "data/private/network/companies.jsonl", companies)
        dump_jsonl(root / "data/private/network/company_icb_mappings.jsonl", mappings)
        return root

    def test_two_eligible_companies_promote_third_company_cta(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_root(tmp, 2)
            sector = DemandCatalog(root).snapshot(as_of=date(2026, 8, 7))["sectors"][0]
            self.assertEqual("benchmark_edge", sector["benchmark_state"])
            self.assertEqual("add_third_company", sector["primary_action"])
            self.assertTrue(sector["third_company_cta"])
            self.assertFalse(sector["benchmark_enabled"])

    def test_three_eligible_companies_unlock_benchmark(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_root(tmp, 3)
            sector = DemandCatalog(root).snapshot(as_of=date(2026, 8, 7))["sectors"][0]
            self.assertEqual("benchmark_ready", sector["benchmark_state"])
            self.assertTrue(sector["benchmark_enabled"])
            self.assertEqual("launch_benchmark", sector["primary_action"])

    def test_use_case_inventory_is_counted_without_proving_sector_demand(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_root(tmp, 1)
            dump_yaml(root / "studies/bank-1/05b_use_case_inventory.yaml", {"study_id": "study-1", "company": "Bank 1", "inventory_version": "1", "use_cases": [{"use_case_id": "UC-1"}]})
            sector = DemandCatalog(root).snapshot(as_of=date(2026, 8, 7))["sectors"][0]
            self.assertEqual(1, sector["use_case_count"])
            self.assertEqual(1, sector["eligible_study_count"])


if __name__ == "__main__":
    unittest.main()
