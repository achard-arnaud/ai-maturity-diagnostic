from __future__ import annotations

import unittest

from app.demand_evidence import (
    compute_confidence,
    has_complete_provenance,
    is_provenance_stale,
    link_claim,
    unlink_claim,
)
from app.demand_policy import known, unknown


def _demand(**kwargs) -> dict:
    base = {
        "demand_id": "d1",
        "workspace_id": "ws-a",
        "company_entity_id": "entity_1",
        "status": "observed",
        "problem": unknown(),
        "population": unknown(),
        "impact": unknown(),
        "urgency": unknown(),
        "initiative": unknown(),
        "sponsor": unknown(),
        "budget": unknown(),
        "timing": unknown(),
        "claim_ids": [],
        "origin_profile_ref": None,
        "created_at": "2026-01-01T00:00:00+00:00",
        "updated_at": "2026-01-01T00:00:00+00:00",
    }
    base.update(kwargs)
    return base


def _claim(claim_id: str, status: str = "active", evidence_grade: str | None = None) -> dict:
    return {"claim_id": claim_id, "status": status, "evidence_grade": evidence_grade}


class LinkUnlinkTests(unittest.TestCase):
    def test_link_adds_claim_id(self) -> None:
        demand = link_claim(_demand(), "c1")
        self.assertEqual(["c1"], demand["claim_ids"])

    def test_link_is_idempotent(self) -> None:
        demand = link_claim(_demand(), "c1")
        demand = link_claim(demand, "c1")
        self.assertEqual(["c1"], demand["claim_ids"])

    def test_unlink_removes_claim_id(self) -> None:
        demand = link_claim(_demand(), "c1")
        demand = unlink_claim(demand, "c1")
        self.assertEqual([], demand["claim_ids"])

    def test_unlink_missing_claim_is_a_noop(self) -> None:
        demand = unlink_claim(_demand(), "nope")
        self.assertEqual([], demand["claim_ids"])


class ProvenanceCompletenessTests(unittest.TestCase):
    def test_no_known_fields_has_trivially_complete_provenance(self) -> None:
        demand = _demand()
        self.assertTrue(has_complete_provenance(demand, {}))

    def test_known_field_without_linked_claims_is_incomplete(self) -> None:
        demand = _demand(problem=known("manual onboarding"))
        self.assertFalse(has_complete_provenance(demand, {}))

    def test_known_field_with_active_linked_claim_is_complete(self) -> None:
        demand = _demand(problem=known("manual onboarding"), claim_ids=["c1"])
        claims_by_id = {"c1": _claim("c1", status="active")}
        self.assertTrue(has_complete_provenance(demand, claims_by_id))

    def test_known_field_with_only_superseded_claim_is_incomplete(self) -> None:
        demand = _demand(problem=known("manual onboarding"), claim_ids=["c1"])
        claims_by_id = {"c1": _claim("c1", status="superseded")}
        self.assertFalse(has_complete_provenance(demand, claims_by_id))


class ProvenanceStalenessTests(unittest.TestCase):
    def test_no_linked_claims_is_not_stale(self) -> None:
        demand = _demand()
        self.assertFalse(is_provenance_stale(demand, {}))

    def test_linked_active_claim_is_not_stale(self) -> None:
        demand = _demand(claim_ids=["c1"])
        claims_by_id = {"c1": _claim("c1", status="active")}
        self.assertFalse(is_provenance_stale(demand, claims_by_id))

    def test_linked_claims_all_superseded_is_stale(self) -> None:
        demand = _demand(claim_ids=["c1", "c2"])
        claims_by_id = {"c1": _claim("c1", status="superseded"), "c2": _claim("c2", status="retracted")}
        self.assertTrue(is_provenance_stale(demand, claims_by_id))

    def test_at_least_one_active_claim_among_linked_is_not_stale(self) -> None:
        demand = _demand(claim_ids=["c1", "c2"])
        claims_by_id = {"c1": _claim("c1", status="superseded"), "c2": _claim("c2", status="active")}
        self.assertFalse(is_provenance_stale(demand, claims_by_id))


class ConfidenceTests(unittest.TestCase):
    def test_no_linked_claims_is_low_confidence(self) -> None:
        demand = _demand()
        self.assertEqual("low", compute_confidence(demand, {}))

    def test_p1_evidence_grade_is_high_confidence(self) -> None:
        demand = _demand(claim_ids=["c1"])
        claims_by_id = {"c1": _claim("c1", evidence_grade="P1")}
        self.assertEqual("high", compute_confidence(demand, claims_by_id))

    def test_u1_evidence_grade_is_medium_confidence(self) -> None:
        demand = _demand(claim_ids=["c1"])
        claims_by_id = {"c1": _claim("c1", evidence_grade="U1")}
        self.assertEqual("medium", compute_confidence(demand, claims_by_id))

    def test_n0_evidence_grade_is_low_confidence(self) -> None:
        demand = _demand(claim_ids=["c1"])
        claims_by_id = {"c1": _claim("c1", evidence_grade="N0")}
        self.assertEqual("low", compute_confidence(demand, claims_by_id))

    def test_best_of_multiple_linked_claims_wins(self) -> None:
        demand = _demand(claim_ids=["c1", "c2"])
        claims_by_id = {"c1": _claim("c1", evidence_grade="N0"), "c2": _claim("c2", evidence_grade="P1")}
        self.assertEqual("high", compute_confidence(demand, claims_by_id))

    def test_superseded_claim_does_not_count_toward_confidence(self) -> None:
        demand = _demand(claim_ids=["c1"])
        claims_by_id = {"c1": _claim("c1", status="superseded", evidence_grade="P1")}
        self.assertEqual("low", compute_confidence(demand, claims_by_id))


if __name__ == "__main__":
    unittest.main()
