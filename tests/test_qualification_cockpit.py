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
    def test_matching_is_next_when_demand_and_snapshots_are_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            study = root / "studies/acme"
            dump(study / "00_manifest.yaml", {"study_id": "acme-1", "company": "Acme", "product_snapshots": [{"offer_id": "OFFER-1", "path": "inputs/x.yaml"}]})
            dump(study / "05_enterprise_demand_profile.yaml", {"evidence_claims": [{"claim_id": "E1"}], "capability_gaps": [{"claim_id": "G1"}], "confidence": "medium"})
            dump(study / "06_product_fit_matrix.yaml", {"matches": [], "decision": None})
            row = QualificationCockpit(root).list_studies()[0]
            self.assertEqual("matching", row["stage"])
            self.assertEqual("opportunity-fit-matching", row["next_skill"])
            self.assertEqual("ready", row["steps"][2]["status"])

    def test_nurture_stops_contact_and_pilot_progression(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            study = root / "studies/acme"
            dump(study / "00_manifest.yaml", {"study_id": "acme-1", "company": "Acme", "product_snapshots": [{"offer_id": "OFFER-1"}]})
            dump(study / "05_enterprise_demand_profile.yaml", {"evidence_claims": [{"claim_id": "E1"}], "capability_gaps": [{"claim_id": "G1"}], "confidence": "high"})
            dump(study / "06_product_fit_matrix.yaml", {"matches": [{"offer_id": "OFFER-1"}], "decision": "nurture"})
            row = QualificationCockpit(root).list_studies()[0]
            self.assertEqual("stopped", row["stage"])
            self.assertIsNone(row["next_skill"])
            self.assertEqual("blocked", row["steps"][3]["status"])
            self.assertEqual("blocked", row["steps"][4]["status"])


if __name__ == "__main__":
    unittest.main()
