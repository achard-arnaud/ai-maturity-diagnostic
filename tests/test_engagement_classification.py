from __future__ import annotations

import unittest

from app.engagement_classification import (
    EngagementClassificationError,
    build_review_queue,
    can_act_on_objection,
    classify_objection,
    needs_human_review,
    review_objection,
)


def _objection(objection_id: str, confidence: float, raised_at: str = "2026-01-01T00:00:00Z") -> dict:
    return classify_objection(
        objection_id=objection_id, engagement_event_id="ee1", category="price",
        confidence=confidence, raised_at=raised_at,
    )


class ClassifyObjectionTests(unittest.TestCase):
    def test_always_created_draft(self) -> None:
        objection = _objection("o1", 0.9)
        self.assertEqual("draft", objection["status"])

    def test_refuses_out_of_range_confidence(self) -> None:
        with self.assertRaises(EngagementClassificationError):
            classify_objection(
                objection_id="o1", engagement_event_id="ee1", category="price",
                confidence=1.5, raised_at="2026-01-01T00:00:00Z",
            )


class NeedsHumanReviewTests(unittest.TestCase):
    def test_low_confidence_draft_needs_review(self) -> None:
        self.assertTrue(needs_human_review(_objection("o1", 0.3)))

    def test_high_confidence_draft_does_not_need_review(self) -> None:
        self.assertFalse(needs_human_review(_objection("o1", 0.9)))

    def test_at_threshold_does_not_need_review(self) -> None:
        self.assertFalse(needs_human_review(_objection("o1", 0.7)))

    def test_reviewed_objection_never_needs_review_again(self) -> None:
        objection = review_objection(_objection("o1", 0.2), reviewed_by="alice", reviewed_at="2026-01-02T00:00:00Z")
        self.assertFalse(needs_human_review(objection))


class CanActOnObjectionTests(unittest.TestCase):
    def test_low_confidence_draft_gold_case_blocked(self) -> None:
        # Gold case: 'faible confiance routée' -- a low-confidence
        # draft can never drive downstream action.
        self.assertFalse(can_act_on_objection(_objection("o1", 0.4)))

    def test_high_confidence_draft_allowed_without_review(self) -> None:
        self.assertTrue(can_act_on_objection(_objection("o1", 0.95)))

    def test_low_confidence_becomes_actionable_after_review(self) -> None:
        objection = review_objection(_objection("o1", 0.2), reviewed_by="alice", reviewed_at="2026-01-02T00:00:00Z")
        self.assertTrue(can_act_on_objection(objection))


class ReviewObjectionTests(unittest.TestCase):
    def test_review_sets_reviewer_and_status(self) -> None:
        reviewed = review_objection(_objection("o1", 0.3), reviewed_by="alice", reviewed_at="2026-01-02T00:00:00Z")
        self.assertEqual("reviewed", reviewed["status"])
        self.assertEqual("alice", reviewed["reviewed_by"])

    def test_cannot_review_an_already_reviewed_objection(self) -> None:
        reviewed = review_objection(_objection("o1", 0.3), reviewed_by="alice", reviewed_at="2026-01-02T00:00:00Z")
        with self.assertRaises(EngagementClassificationError):
            review_objection(reviewed, reviewed_by="bob", reviewed_at="2026-01-03T00:00:00Z")


class BuildReviewQueueTests(unittest.TestCase):
    def test_queue_contains_only_low_confidence_drafts(self) -> None:
        objections = [_objection("o1", 0.9), _objection("o2", 0.2), _objection("o3", 0.1)]
        queue = build_review_queue(objections)
        self.assertEqual(["o2", "o3"], [o["objection_id"] for o in queue])

    def test_queue_ordered_oldest_first(self) -> None:
        objections = [
            _objection("o1", 0.2, raised_at="2026-01-03T00:00:00Z"),
            _objection("o2", 0.2, raised_at="2026-01-01T00:00:00Z"),
        ]
        queue = build_review_queue(objections)
        self.assertEqual(["o2", "o1"], [o["objection_id"] for o in queue])

    def test_reviewed_objections_never_reappear_in_queue(self) -> None:
        reviewed = review_objection(_objection("o1", 0.1), reviewed_by="alice", reviewed_at="2026-01-02T00:00:00Z")
        queue = build_review_queue([reviewed])
        self.assertEqual([], queue)


if __name__ == "__main__":
    unittest.main()
