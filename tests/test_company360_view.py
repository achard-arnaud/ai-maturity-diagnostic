from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.claim_store import put_claim
from app.company360_view import _FORBIDDEN_FIELD_TOKENS, get_company_360
from app.evidence_store import put_evidence
from app.research_case_store import put_case


def _case(research_case_id: str, company_entity_id: str = "entity_1") -> dict:
    return {
        "research_case_id": research_case_id,
        "workspace_id": "ws-a",
        "company_entity_id": company_entity_id,
        "status": "open",
        "owner": None,
        "created_at": "2026-01-01T00:00:00+00:00",
        "updated_at": "2026-01-01T00:00:00+00:00",
        "origin_signal_id": None,
        "blockers": [],
    }


def _claim(claim_id: str, claim_type: str, **kwargs) -> dict:
    base = {
        "claim_id": claim_id,
        "workspace_id": "ws-a",
        "research_case_id": "rc1",
        "company_entity_id": "entity_1",
        "statement": "stmt",
        "claim_type": claim_type,
        "evidence_ids": [],
        "derived_from_claim_ids": [],
        "status": "active",
        "contradicted_by_claim_ids": [],
    }
    base.update(kwargs)
    return base


def _evidence(evidence_id: str) -> dict:
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
        "entity_refs": ["entity_1"],
        "supports_claim_ids": [],
        "contests_claim_ids": [],
        "evidence_grade": "P1",
    }


class CompanyThreeSixtyTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_aggregates_research_case_claims_and_evidence(self) -> None:
        put_case(self.root, "ws-a", _case("rc1"))
        put_claim(self.root, "ws-a", _claim("c1", "fact"))
        put_evidence(self.root, "ws-a", _evidence("e1"))

        view = get_company_360(self.root, "ws-a", "entity_1")

        self.assertEqual(1, len(view["research_cases"]))
        self.assertEqual(1, len(view["claims"]["fact"]))
        self.assertEqual(1, view["evidence_count"])

    def test_claims_grouped_by_truth_type(self) -> None:
        put_claim(self.root, "ws-a", _claim("c1", "fact"))
        put_claim(
            self.root,
            "ws-a",
            _claim("c2", "hypothesis", hypothesis_owner="alice", hypothesis_due_at="2026-12-01"),
        )
        view = get_company_360(self.root, "ws-a", "entity_1")
        self.assertEqual(["c1"], [c["claim_id"] for c in view["claims"]["fact"]])
        self.assertEqual(["c2"], [c["claim_id"] for c in view["claims"]["hypothesis"]])

    def test_superseded_claim_excluded_from_grouping(self) -> None:
        put_claim(self.root, "ws-a", _claim("c1", "fact", status="superseded"))
        view = get_company_360(self.root, "ws-a", "entity_1")
        self.assertEqual([], view["claims"]["fact"])

    def test_unknowns_are_hypotheses_with_a_due_date(self) -> None:
        put_claim(
            self.root,
            "ws-a",
            _claim("c1", "hypothesis", hypothesis_owner="alice", hypothesis_due_at="2026-12-01"),
        )
        view = get_company_360(self.root, "ws-a", "entity_1")
        self.assertEqual(1, len(view["unknowns"]))

    def test_contradictions_surfaced(self) -> None:
        put_claim(self.root, "ws-a", _claim("c1", "fact", contradicted_by_claim_ids=["c2"]))
        put_claim(self.root, "ws-a", _claim("c2", "fact"))
        view = get_company_360(self.root, "ws-a", "entity_1")
        self.assertIn(("c1", "c2"), view["contradictions"])

    def test_company_with_no_data_returns_empty_view(self) -> None:
        view = get_company_360(self.root, "ws-a", "entity_unknown")
        self.assertEqual([], view["research_cases"])
        self.assertEqual(0, view["evidence_count"])


class NoProductDataStructuralGuard(unittest.TestCase):
    """Gold-set-style guard mirroring app.signal_screening's 'never a fit
    score' test: the Company 360 view must never carry a product/offer
    field, by construction, not just by convention."""

    def test_view_keys_never_look_product_shaped(self) -> None:
        result_keys = ["company_entity_id", "research_cases", "claims", "unknowns", "contradictions", "evidence_count"]
        for key in result_keys:
            for token in _FORBIDDEN_FIELD_TOKENS:
                self.assertNotIn(token, key.lower())

    def test_claim_type_keys_never_look_product_shaped(self) -> None:
        from app.company360_view import _CLAIM_TYPES

        for claim_type in _CLAIM_TYPES:
            for token in _FORBIDDEN_FIELD_TOKENS:
                self.assertNotIn(token, claim_type.lower())


if __name__ == "__main__":
    unittest.main()
