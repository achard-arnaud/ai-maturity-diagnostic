from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.evidence_store import EvidenceNotFound, get_evidence, list_evidence, put_evidence


def _evidence(evidence_id: str, *, entity_refs: list[str] | None = None) -> dict:
    return {
        "evidence_id": evidence_id,
        "workspace_id": "ws-a",
        "source": {"kind": "public", "ref": "ref"},
        "locator": "https://example.com",
        "evidence_type": "observation",
        "dated_at": "2026-06-01T00:00:00+00:00",
        "excerpt": "excerpt",
        "hash": "abc",
        "license": "public",
        "entity_refs": entity_refs or ["entity_1"],
        "supports_claim_ids": [],
        "contests_claim_ids": [],
        "evidence_grade": "P1",
    }


class EvidenceStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_put_then_get_round_trips(self) -> None:
        put_evidence(self.root, "ws-a", _evidence("e1"))
        record = get_evidence(self.root, "ws-a", "e1")
        self.assertEqual("e1", record["evidence_id"])

    def test_get_missing_evidence_raises(self) -> None:
        with self.assertRaises(EvidenceNotFound):
            get_evidence(self.root, "ws-a", "nope")

    def test_workspaces_are_isolated(self) -> None:
        put_evidence(self.root, "ws-a", _evidence("e1"))
        with self.assertRaises(EvidenceNotFound):
            get_evidence(self.root, "ws-b", "e1")

    def test_filter_by_entity_ref(self) -> None:
        put_evidence(self.root, "ws-a", _evidence("e1", entity_refs=["entity_1"]))
        put_evidence(self.root, "ws-a", _evidence("e2", entity_refs=["entity_2"]))
        records = list_evidence(self.root, "ws-a", entity_ref="entity_2")
        self.assertEqual(["e2"], [e["evidence_id"] for e in records])


if __name__ == "__main__":
    unittest.main()
