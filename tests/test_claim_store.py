from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.claim_store import ClaimNotFound, get_claim, list_claims, put_claim


def _claim(claim_id: str, *, company_entity_id: str = "entity_1", research_case_id: str = "rc1") -> dict:
    return {
        "claim_id": claim_id,
        "workspace_id": "ws-a",
        "research_case_id": research_case_id,
        "company_entity_id": company_entity_id,
        "statement": "stmt",
        "claim_type": "fact",
        "evidence_ids": [],
        "derived_from_claim_ids": [],
        "status": "active",
    }


class ClaimStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_put_then_get_round_trips(self) -> None:
        put_claim(self.root, "ws-a", _claim("c1"))
        record = get_claim(self.root, "ws-a", "c1")
        self.assertEqual("c1", record["claim_id"])

    def test_get_missing_claim_raises(self) -> None:
        with self.assertRaises(ClaimNotFound):
            get_claim(self.root, "ws-a", "nope")

    def test_workspaces_are_isolated(self) -> None:
        put_claim(self.root, "ws-a", _claim("c1"))
        with self.assertRaises(ClaimNotFound):
            get_claim(self.root, "ws-b", "c1")

    def test_filter_by_company(self) -> None:
        put_claim(self.root, "ws-a", _claim("c1", company_entity_id="entity_1"))
        put_claim(self.root, "ws-a", _claim("c2", company_entity_id="entity_2"))
        claims = list_claims(self.root, "ws-a", company_entity_id="entity_1")
        self.assertEqual(["c1"], [c["claim_id"] for c in claims])

    def test_filter_by_research_case(self) -> None:
        put_claim(self.root, "ws-a", _claim("c1", research_case_id="rc1"))
        put_claim(self.root, "ws-a", _claim("c2", research_case_id="rc2"))
        claims = list_claims(self.root, "ws-a", research_case_id="rc2")
        self.assertEqual(["c2"], [c["claim_id"] for c in claims])


if __name__ == "__main__":
    unittest.main()
