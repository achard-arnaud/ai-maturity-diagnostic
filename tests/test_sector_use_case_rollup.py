from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def dump_yaml(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def dump_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


class SectorUseCaseRollupTests(unittest.TestCase):
    def test_rollup_ingests_company_use_case_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data_root = root / "private"
            mappings = []
            for index in range(1, 4):
                company_id = f"C{index}"
                mappings.append({"mapping_id": f"M{index}", "company_id": company_id, "mapping_status": "validated", "confidence": "high", "sector": {"code": "301010", "name": "Banks"}})
                study = root / "studies" / f"study-{index}"
                dump_yaml(study / "00_manifest.yaml", {"study_id": f"study-{index}", "company_id": company_id, "updated_at": "2026-08-01"})
                dump_yaml(study / "05_enterprise_demand_profile.yaml", {"evidence_claims": [{"claim_id": f"E{index}"}], "strategic_priorities": [], "capability_gaps": [{"claim_id": f"G{index}"}], "confidence": "medium"})
                dump_yaml(study / "05b_use_case_inventory.yaml", {"study_id": f"study-{index}", "company": f"Bank {index}", "use_cases": [{"use_case_id": f"UC-{index}", "name": "KYC review", "line_of_business": "Operations", "workflow": "KYC", "evidence_status": "observed", "maturity": "pilot", "dependencies": {"depends_on": [], "enables": []}, "feedback": [], "confidence": "medium"}]})
            dump_jsonl(data_root / "network/company_icb_mappings.jsonl", mappings)
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts/build_sector_rollups.py"), "--data-root", str(data_root), "--studies-root", str(root / "studies"), "--date", "2026-08-07"],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            rollup = yaml.safe_load((data_root / "sector_rollups/ICB-301010.yaml").read_text(encoding="utf-8"))
            self.assertEqual(3, len(rollup["evidence_pool"]["use_cases"]))
            self.assertEqual("UC-1", rollup["evidence_pool"]["use_cases"][0]["use_case_id"])


if __name__ == "__main__":
    unittest.main()
