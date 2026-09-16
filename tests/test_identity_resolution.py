from __future__ import annotations

import unittest

from app.identity_resolution import (
    IdentityResolutionError,
    apply_accepted_merge,
    decide_merge,
    propose_merge,
    reverse_merge,
)


def _entity(entity_id: str, legacy_ids: list[str], **overrides) -> dict:
    base = {
        "entity_id": entity_id,
        "legacy_ids": legacy_ids,
        "status": "active",
        "merged_into_entity_id": None,
    }
    base.update(overrides)
    return base


class GoldPairMergeProposalTests(unittest.TestCase):
    """"Gold pairs": known true-duplicate and known non-duplicate cases."""

    def test_gold_pair_same_person_different_employer_can_be_proposed(self) -> None:
        # Jane Doe at Acme, then Jane Doe at Beta -- a true duplicate per
        # ADR-009's motivating scenario.
        survivor = _entity("entity_jane_1", ["PERS-ACME-JANE"])
        candidate = _entity("entity_jane_2", ["PERS-BETA-JANE"])
        proposal = propose_merge(
            survivor,
            candidate,
            evidence=["same LinkedIn profile URL observed in both intake batches"],
            confidence=0.92,
        )
        self.assertEqual("pending_review", proposal.status)
        self.assertEqual("entity_jane_1", proposal.survivor_entity_id)

    def test_proposal_never_mutates_inputs(self) -> None:
        survivor = _entity("entity_jane_1", ["PERS-ACME-JANE"])
        candidate = _entity("entity_jane_2", ["PERS-BETA-JANE"])
        propose_merge(survivor, candidate, evidence=["evidence-1"], confidence=0.9)
        self.assertEqual(["PERS-ACME-JANE"], survivor["legacy_ids"])
        self.assertEqual(["PERS-BETA-JANE"], candidate["legacy_ids"])

    def test_cannot_propose_merging_entity_with_itself(self) -> None:
        entity = _entity("entity_jane_1", ["PERS-ACME-JANE"])
        with self.assertRaises(IdentityResolutionError):
            propose_merge(entity, entity, evidence=["x"], confidence=0.5)

    def test_confidence_out_of_range_is_rejected(self) -> None:
        survivor = _entity("entity_a", ["A"])
        candidate = _entity("entity_b", ["B"])
        with self.assertRaises(IdentityResolutionError):
            propose_merge(survivor, candidate, evidence=["x"], confidence=1.5)

    def test_proposal_requires_evidence(self) -> None:
        survivor = _entity("entity_a", ["A"])
        candidate = _entity("entity_b", ["B"])
        with self.assertRaises(IdentityResolutionError):
            propose_merge(survivor, candidate, evidence=[], confidence=0.5)


class HumanAuditedMergeTests(unittest.TestCase):
    def test_merge_requires_a_named_reviewer(self) -> None:
        survivor = _entity("entity_a", ["A"])
        candidate = _entity("entity_b", ["B"])
        proposal = propose_merge(survivor, candidate, evidence=["x"], confidence=0.9)
        with self.assertRaises(IdentityResolutionError):
            decide_merge(proposal, decision="accepted", reviewed_by="", rationale="looks right")

    def test_accepted_merge_marks_candidate_merged_and_absorbs_legacy_ids(self) -> None:
        survivor = _entity("entity_jane_1", ["PERS-ACME-JANE"])
        candidate = _entity("entity_jane_2", ["PERS-BETA-JANE"])
        proposal = propose_merge(survivor, candidate, evidence=["same profile"], confidence=0.95)
        decision = decide_merge(proposal, decision="accepted", reviewed_by="alice@acme.example", rationale="confirmed same person")

        updated_survivor, updated_candidate = apply_accepted_merge(survivor, candidate, decision=decision)

        self.assertEqual(["PERS-ACME-JANE", "PERS-BETA-JANE"], updated_survivor["legacy_ids"])
        self.assertEqual("merged", updated_candidate["status"])
        self.assertEqual("entity_jane_1", updated_candidate["merged_into_entity_id"])
        # Original inputs are untouched (no in-place mutation).
        self.assertEqual("active", candidate["status"])

    def test_rejected_decision_cannot_be_applied(self) -> None:
        survivor = _entity("entity_a", ["A"])
        candidate = _entity("entity_b", ["B"])
        proposal = propose_merge(survivor, candidate, evidence=["x"], confidence=0.4)
        decision = decide_merge(proposal, decision="rejected", reviewed_by="bob@acme.example", rationale="different people, same name")
        with self.assertRaises(IdentityResolutionError):
            apply_accepted_merge(survivor, candidate, decision=decision)

    def test_gold_pair_non_duplicate_same_name_different_person_is_rejected_not_merged(self) -> None:
        # Two different "John Smith"s at unrelated companies -- a known
        # non-duplicate gold pair. The proposal can still be raised (name
        # collision), but the human decision must reject it.
        survivor = _entity("entity_john_1", ["PERS-ACME-JOHN"])
        candidate = _entity("entity_john_2", ["PERS-BETA-JOHN"])
        proposal = propose_merge(survivor, candidate, evidence=["name collision only, no corroborating signal"], confidence=0.2)
        decision = decide_merge(proposal, decision="rejected", reviewed_by="carol@acme.example", rationale="unrelated people, coincidental name match")
        self.assertEqual("rejected", decision.decision)
        with self.assertRaises(IdentityResolutionError):
            apply_accepted_merge(survivor, candidate, decision=decision)


class ReversibilityTests(unittest.TestCase):
    def test_merge_can_be_fully_reversed(self) -> None:
        survivor = _entity("entity_jane_1", ["PERS-ACME-JANE"])
        candidate = _entity("entity_jane_2", ["PERS-BETA-JANE"])
        proposal = propose_merge(survivor, candidate, evidence=["same profile"], confidence=0.95)
        decision = decide_merge(proposal, decision="accepted", reviewed_by="alice@acme.example", rationale="confirmed")
        merged_survivor, merged_candidate = apply_accepted_merge(survivor, candidate, decision=decision)

        restored_survivor, restored_candidate = reverse_merge(
            merged_survivor,
            merged_candidate,
            original_candidate_legacy_ids=candidate["legacy_ids"],
        )

        self.assertEqual(["PERS-ACME-JANE"], restored_survivor["legacy_ids"])
        self.assertEqual("active", restored_candidate["status"])
        self.assertIsNone(restored_candidate["merged_into_entity_id"])
        self.assertEqual(["PERS-BETA-JANE"], restored_candidate["legacy_ids"])

    def test_cannot_reverse_a_record_that_was_never_merged(self) -> None:
        never_merged = _entity("entity_a", ["A"])
        with self.assertRaises(IdentityResolutionError):
            reverse_merge(never_merged, never_merged, original_candidate_legacy_ids=["A"])


if __name__ == "__main__":
    unittest.main()
