from __future__ import annotations

import unittest

from app.target_currentness import evaluate_readiness


class ReadinessGoldCasesTests(unittest.TestCase):
    """Stop condition: 'ready strict' -- these are the gold cases named
    in the Epic's own invariants."""

    def test_current_relationship_and_strong_confidence_sponsor_is_ready(self) -> None:
        result = evaluate_readiness(
            role="sponsor", currentness_is_current=True, currentness_requires_review=False,
            influence_confidence="high",
        )
        self.assertTrue(result.ready)
        self.assertEqual((), result.reasons)

    def test_stale_relationship_blocks_regardless_of_role(self) -> None:
        result = evaluate_readiness(
            role="user", currentness_is_current=False, currentness_requires_review=False,
            influence_confidence="high",
        )
        self.assertFalse(result.ready)
        self.assertIn("currentness insufficient -- relationship is not current", result.reasons)

    def test_currentness_conflict_requiring_review_blocks(self) -> None:
        result = evaluate_readiness(
            role="user", currentness_is_current=None, currentness_requires_review=True,
            influence_confidence="high",
        )
        self.assertFalse(result.ready)
        self.assertIn("currentness conflict requires human review", result.reasons)

    def test_title_alone_never_proves_authority_gold_case(self) -> None:
        # Current relationship, sponsor role, but confidence is only
        # "unknown" -- i.e. the only "evidence" of authority is the
        # person's title. Must be blocked.
        result = evaluate_readiness(
            role="sponsor", currentness_is_current=True, currentness_requires_review=False,
            influence_confidence="unknown",
        )
        self.assertFalse(result.ready)
        self.assertTrue(any("title alone never proves authority" in r for r in result.reasons))

    def test_low_confidence_champion_also_blocked(self) -> None:
        result = evaluate_readiness(
            role="champion", currentness_is_current=True, currentness_requires_review=False,
            influence_confidence="low",
        )
        self.assertFalse(result.ready)

    def test_non_authority_role_does_not_need_strong_confidence(self) -> None:
        result = evaluate_readiness(
            role="technique", currentness_is_current=True, currentness_requires_review=False,
            influence_confidence="unknown",
        )
        self.assertTrue(result.ready)

    def test_blocker_role_current_relationship_is_ready_regardless_of_confidence(self) -> None:
        result = evaluate_readiness(
            role="blocker", currentness_is_current=True, currentness_requires_review=False,
            influence_confidence="low",
        )
        self.assertTrue(result.ready)

    def test_medium_confidence_sponsor_is_sufficient(self) -> None:
        result = evaluate_readiness(
            role="sponsor", currentness_is_current=True, currentness_requires_review=False,
            influence_confidence="medium",
        )
        self.assertTrue(result.ready)

    def test_conflict_and_weak_confidence_both_reported(self) -> None:
        result = evaluate_readiness(
            role="sponsor", currentness_is_current=None, currentness_requires_review=True,
            influence_confidence="low",
        )
        self.assertFalse(result.ready)
        self.assertEqual(2, len(result.reasons))


if __name__ == "__main__":
    unittest.main()
