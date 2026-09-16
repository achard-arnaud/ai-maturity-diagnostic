from __future__ import annotations

import unittest

from app.research_policy import (
    ClaimLineageError,
    can_transition_case,
    compute_completeness,
    is_claim_type_promotion,
    validate_claim_lineage,
)


def _evidence(evidence_id: str, grade: str = "P1") -> dict:
    return {"evidence_id": evidence_id, "evidence_grade": grade}


def _claim(claim_id: str, claim_type: str, **kwargs) -> dict:
    base = {
        "claim_id": claim_id,
        "claim_type": claim_type,
        "evidence_ids": [],
        "derived_from_claim_ids": [],
        "status": "active",
    }
    base.update(kwargs)
    return base


class CaseTransitionTests(unittest.TestCase):
    def test_open_to_in_progress_allowed(self) -> None:
        self.assertTrue(can_transition_case("open", "in_progress", open_blockers=0))

    def test_open_to_accepted_not_allowed(self) -> None:
        self.assertFalse(can_transition_case("open", "accepted", open_blockers=0))

    def test_in_review_to_accepted_blocked_by_open_blocker(self) -> None:
        self.assertFalse(can_transition_case("in_review", "accepted", open_blockers=1))

    def test_in_review_to_accepted_allowed_with_no_blockers(self) -> None:
        self.assertTrue(can_transition_case("in_review", "accepted", open_blockers=0))

    def test_accepted_to_stale_allowed(self) -> None:
        self.assertTrue(can_transition_case("accepted", "stale", open_blockers=0))

    def test_stale_to_reopened_allowed(self) -> None:
        self.assertTrue(can_transition_case("stale", "reopened", open_blockers=0))

    def test_terminal_like_state_rejects_unknown_transition(self) -> None:
        self.assertFalse(can_transition_case("blocked", "accepted", open_blockers=0))


class ClaimLineageTests(unittest.TestCase):
    def test_fact_claim_requires_evidence(self) -> None:
        claim = _claim("c1", "fact", evidence_ids=[])
        error = validate_claim_lineage(claim, evidence_by_id={}, claims_by_id={})
        self.assertIsInstance(error, ClaimLineageError)
        self.assertIn("evidence_id", error.reason)

    def test_fact_claim_with_only_n0_evidence_rejected(self) -> None:
        claim = _claim("c1", "fact", evidence_ids=["e1"])
        error = validate_claim_lineage(
            claim, evidence_by_id={"e1": _evidence("e1", "N0")}, claims_by_id={}
        )
        self.assertIsInstance(error, ClaimLineageError)

    def test_fact_claim_with_p1_evidence_valid(self) -> None:
        claim = _claim("c1", "fact", evidence_ids=["e1"])
        error = validate_claim_lineage(
            claim, evidence_by_id={"e1": _evidence("e1", "P1")}, claims_by_id={}
        )
        self.assertIsNone(error)

    def test_claim_referencing_missing_evidence_rejected(self) -> None:
        claim = _claim("c1", "fact", evidence_ids=["missing"])
        error = validate_claim_lineage(claim, evidence_by_id={}, claims_by_id={})
        self.assertIsInstance(error, ClaimLineageError)
        self.assertIn("does not exist", error.reason)

    def test_inference_requires_evidence_or_parent_claims(self) -> None:
        claim = _claim("c2", "inference")
        error = validate_claim_lineage(claim, evidence_by_id={}, claims_by_id={})
        self.assertIsInstance(error, ClaimLineageError)

    def test_inference_valid_from_derived_claims(self) -> None:
        claim = _claim("c2", "inference", derived_from_claim_ids=["c1"])
        error = validate_claim_lineage(
            claim, evidence_by_id={}, claims_by_id={"c1": _claim("c1", "fact")}
        )
        self.assertIsNone(error)

    def test_inference_referencing_missing_parent_claim_rejected(self) -> None:
        claim = _claim("c2", "inference", derived_from_claim_ids=["missing"])
        error = validate_claim_lineage(claim, evidence_by_id={}, claims_by_id={})
        self.assertIsInstance(error, ClaimLineageError)

    def test_hypothesis_requires_owner_and_due_date(self) -> None:
        claim = _claim("c3", "hypothesis")
        error = validate_claim_lineage(claim, evidence_by_id={}, claims_by_id={})
        self.assertIsInstance(error, ClaimLineageError)

    def test_hypothesis_valid_with_owner_and_due_date(self) -> None:
        claim = _claim(
            "c3",
            "hypothesis",
            hypothesis_owner="alice@example.com",
            hypothesis_due_at="2026-12-01T00:00:00+00:00",
        )
        error = validate_claim_lineage(claim, evidence_by_id={}, claims_by_id={})
        self.assertIsNone(error)


class ClaimPromotionTests(unittest.TestCase):
    def test_hypothesis_to_fact_is_a_promotion(self) -> None:
        self.assertTrue(is_claim_type_promotion("hypothesis", "fact"))

    def test_fact_to_hypothesis_is_not_a_promotion(self) -> None:
        self.assertFalse(is_claim_type_promotion("fact", "hypothesis"))

    def test_inference_to_inference_is_not_a_promotion(self) -> None:
        self.assertFalse(is_claim_type_promotion("inference", "inference"))


class CompletenessTests(unittest.TestCase):
    def test_no_claims_is_incomplete(self) -> None:
        result = compute_completeness([])
        self.assertFalse(result.is_complete)
        self.assertIn("no active fact claim", result.missing)

    def test_one_active_fact_claim_is_complete(self) -> None:
        result = compute_completeness([_claim("c1", "fact")])
        self.assertTrue(result.is_complete)

    def test_superseded_fact_claim_does_not_count(self) -> None:
        result = compute_completeness([_claim("c1", "fact", status="superseded")])
        self.assertFalse(result.is_complete)

    def test_only_hypothesis_claims_is_incomplete(self) -> None:
        result = compute_completeness(
            [_claim("c1", "hypothesis", hypothesis_owner="a", hypothesis_due_at="2026-01-01")]
        )
        self.assertFalse(result.is_complete)


if __name__ == "__main__":
    unittest.main()
