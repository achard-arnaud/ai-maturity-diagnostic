from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.external_identity_store import find_by_external_subject_ref, list_mappings_for_entity, put_mapping


def _mapping(mapping_id: str, *, internal_entity_id: str = "person_1", external_subject_ref: str = "https://linkedin.com/in/a") -> dict:
    return {
        "mapping_id": mapping_id,
        "provider": "linkedin",
        "internal_entity_type": "person",
        "internal_entity_id": internal_entity_id,
        "external_subject_ref": external_subject_ref,
        "status": "candidate",
        "observed_at": "2026-06-01T00:00:00+00:00",
        "source_evidence_id": "evidence_1",
    }


class ExternalIdentityStoreTests(unittest.TestCase):
    def test_put_and_list_for_entity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            put_mapping(root, "ws-a", _mapping("m1"))
            put_mapping(root, "ws-a", _mapping("m2", internal_entity_id="person_2"))
            results = list_mappings_for_entity(root, "ws-a", internal_entity_type="person", internal_entity_id="person_1")
            self.assertEqual(["m1"], [r["mapping_id"] for r in results])

    def test_isolated_per_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            put_mapping(root, "ws-a", _mapping("m1"))
            results = list_mappings_for_entity(root, "ws-b", internal_entity_type="person", internal_entity_id="person_1")
            self.assertEqual([], results)

    def test_find_by_external_subject_ref(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            put_mapping(root, "ws-a", _mapping("m1"))
            found = find_by_external_subject_ref(
                root, "ws-a", provider="linkedin", external_subject_ref="https://linkedin.com/in/a"
            )
            self.assertEqual("m1", found["mapping_id"])
            missing = find_by_external_subject_ref(
                root, "ws-a", provider="linkedin", external_subject_ref="https://linkedin.com/in/nope"
            )
            self.assertIsNone(missing)

    def test_upsert_by_mapping_id_replaces_not_duplicates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            put_mapping(root, "ws-a", _mapping("m1"))
            updated = _mapping("m1")
            updated["status"] = "candidate"
            updated["external_subject_ref"] = "https://linkedin.com/in/updated"
            put_mapping(root, "ws-a", updated)
            results = list_mappings_for_entity(root, "ws-a", internal_entity_type="person", internal_entity_id="person_1")
            self.assertEqual(1, len(results))
            self.assertEqual("https://linkedin.com/in/updated", results[0]["external_subject_ref"])


if __name__ == "__main__":
    unittest.main()
