from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import yaml

from app.core import ControlPlaneError
from app.nudging import UseCaseNudger


def write_inventory(root: Path) -> None:
    path = root / "studies/acme/05b_use_case_inventory.yaml"
    path.parent.mkdir(parents=True)
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
                        "feedback": [{"statement": "Cycle time fell.", "outcome": "faster", "evidence_status": "observed", "source_claim_ids": ["F1"]}],
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

    def test_sector_or_product_context_is_rejected_at_api_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_inventory(root)
            with self.assertRaises(ControlPlaneError):
                UseCaseNudger(root).generate_request({"study_id": "acme-1", "mode": "all", "sector_code": "301010"})
            with self.assertRaises(ControlPlaneError):
                UseCaseNudger(root).generate_request({"study_id": "acme-1", "offer_id": "OFFER-X"})


if __name__ == "__main__":
    unittest.main()
