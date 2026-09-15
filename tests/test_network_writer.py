from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from app.core import ControlPlaneError
from app.network_writer import create_company, create_person


def _read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


class NetworkWriterTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.data_root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_create_company_writes_schema_valid_record(self) -> None:
        company = create_company(self.data_root, canonical_name="Acme Corp")
        for field in [
            "company_id", "canonical_name", "aliases", "countries",
            "relationship_ids", "status", "last_updated", "stale_after_months",
        ]:
            self.assertIn(field, company)
        records = _read_jsonl(self.data_root / "network" / "companies.jsonl")
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["company_id"], company["company_id"])
        self.assertEqual(records[0]["canonical_name"], "Acme Corp")

    def test_create_person_requires_existing_company(self) -> None:
        with self.assertRaises(ControlPlaneError):
            create_person(self.data_root, display_name="Jane Doe", seed_company_id="COMP-DOES-NOT-EXIST")

    def test_create_person_writes_schema_valid_record(self) -> None:
        company = create_company(self.data_root, canonical_name="Acme Corp")
        person = create_person(
            self.data_root,
            display_name="Jane Doe",
            seed_company_id=company["company_id"],
            role_hypotheses=[{"role": "economic_sponsor", "confidence": "medium", "basis": "manual_entry", "epistemic_status": "hypothesis"}],
        )
        for field in [
            "person_id", "display_name", "seed_company_id", "identity_key_basis",
            "relationship_ids", "role_hypotheses", "status", "last_updated", "stale_after_months",
        ]:
            self.assertIn(field, person)
        self.assertEqual(person["seed_company_id"], company["company_id"])
        self.assertEqual(person["identity_key_basis"], "normalized_name_and_company")
        records = _read_jsonl(self.data_root / "network" / "people.jsonl")
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["display_name"], "Jane Doe")

    def test_duplicate_company_creation_updates_in_place(self) -> None:
        first = create_company(self.data_root, canonical_name="Acme Corp")
        second = create_company(self.data_root, canonical_name="Acme Corp", sector_code="651010")
        self.assertEqual(first["company_id"], second["company_id"])
        records = _read_jsonl(self.data_root / "network" / "companies.jsonl")
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["icb_mapping"], {"sector": {"code": "651010"}})

    def test_duplicate_person_creation_updates_in_place_and_merges_roles(self) -> None:
        company = create_company(self.data_root, canonical_name="Acme Corp")
        first = create_person(
            self.data_root,
            display_name="Jane Doe",
            seed_company_id=company["company_id"],
            role_hypotheses=[{"role": "influencer", "confidence": "low", "basis": "manual_entry", "epistemic_status": "hypothesis"}],
        )
        second = create_person(
            self.data_root,
            display_name="Jane Doe",
            seed_company_id=company["company_id"],
            role_hypotheses=[{"role": "economic_sponsor", "confidence": "medium", "basis": "manual_entry", "epistemic_status": "hypothesis"}],
        )
        self.assertEqual(first["person_id"], second["person_id"])
        records = _read_jsonl(self.data_root / "network" / "people.jsonl")
        self.assertEqual(len(records), 1)
        roles = {item["role"] for item in records[0]["role_hypotheses"]}
        self.assertEqual(roles, {"influencer", "economic_sponsor"})

    def test_schema_invalid_input_raises_control_plane_error(self) -> None:
        with self.assertRaises(ControlPlaneError):
            create_company(self.data_root, canonical_name="")
        with self.assertRaises(ControlPlaneError):
            create_person(self.data_root, display_name="", seed_company_id="COMP-1")


if __name__ == "__main__":
    unittest.main()
