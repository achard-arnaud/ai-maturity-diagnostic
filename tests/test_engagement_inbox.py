from __future__ import annotations

import unittest

from app.engagement_classification import classify_objection
from app.engagement_inbox import EngagementInboxError, apply_engagement_to_sequence, build_engagement_inbox, next_action_for_kind


def _sequence(status: str = "active") -> dict:
    return {"sequence_id": "seq1", "status": status}


def _event(kind: str, conversation_id: str = "c1", engagement_event_id: str = "ee1") -> dict:
    return {"engagement_event_id": engagement_event_id, "conversation_id": conversation_id, "kind": kind}


class NextActionForKindTests(unittest.TestCase):
    def test_replied_pauses(self) -> None:
        self.assertEqual("pause_sequence", next_action_for_kind("replied"))

    def test_meeting_booked_pauses(self) -> None:
        self.assertEqual("pause_sequence", next_action_for_kind("meeting_booked"))

    def test_bounced_pauses(self) -> None:
        self.assertEqual("pause_sequence", next_action_for_kind("bounced"))

    def test_opted_out_cancels(self) -> None:
        self.assertEqual("cancel_sequence", next_action_for_kind("opted_out"))

    def test_unknown_kind_rejected(self) -> None:
        with self.assertRaises(EngagementInboxError):
            next_action_for_kind("sent")


class ApplyEngagementToSequenceTests(unittest.TestCase):
    def test_reply_pauses_an_active_sequence_gold_case(self) -> None:
        # Gold case: 'réponse agit sur reach' -- a reply must actually
        # pause the sequence, not just get logged.
        seq, tasks, steps, action = apply_engagement_to_sequence(_event("replied"), _sequence("active"))
        self.assertEqual("paused", seq["status"])
        self.assertEqual("paused", action)

    def test_opt_out_cancels_an_active_sequence(self) -> None:
        seq, _, _, action = apply_engagement_to_sequence(
            _event("opted_out"), _sequence("active"),
            tasks=[{"task_id": "t1", "status": "open"}], steps=[{"step_id": "s1", "status": "pending"}],
        )
        self.assertEqual("cancelled", seq["status"])
        self.assertEqual("cancelled", action)

    def test_reply_against_an_already_paused_sequence_is_a_noop(self) -> None:
        seq, _, _, action = apply_engagement_to_sequence(_event("replied"), _sequence("paused"))
        self.assertEqual("paused", seq["status"])
        self.assertEqual("no_op", action)

    def test_opt_out_against_an_already_cancelled_sequence_is_idempotent(self) -> None:
        seq, _, _, action = apply_engagement_to_sequence(_event("opted_out"), _sequence("cancelled"))
        self.assertEqual("cancelled", seq["status"])
        self.assertEqual("already_cancelled", action)

    def test_meeting_booked_pauses_too(self) -> None:
        _, _, _, action = apply_engagement_to_sequence(_event("meeting_booked"), _sequence("active"))
        self.assertEqual("paused", action)


class BuildEngagementInboxTests(unittest.TestCase):
    def _conversation(self, conversation_id: str, status: str = "open", created_at: str = "2026-01-01T00:00:00Z") -> dict:
        return {"conversation_id": conversation_id, "status": status, "created_at": created_at}

    def test_conversation_with_pending_objection_is_in_inbox(self) -> None:
        conversations = [self._conversation("c1")]
        events = [_event("replied", conversation_id="c1", engagement_event_id="ee1")]
        objections = [classify_objection(
            objection_id="o1", engagement_event_id="ee1", category="price",
            confidence=0.2, raised_at="2026-01-01T00:00:00Z",
        )]
        inbox = build_engagement_inbox(conversations, events, objections)
        self.assertEqual(["c1"], [c["conversation_id"] for c in inbox])

    def test_conversation_with_only_high_confidence_objection_excluded(self) -> None:
        conversations = [self._conversation("c1")]
        events = [_event("replied", conversation_id="c1", engagement_event_id="ee1")]
        objections = [classify_objection(
            objection_id="o1", engagement_event_id="ee1", category="price",
            confidence=0.95, raised_at="2026-01-01T00:00:00Z",
        )]
        inbox = build_engagement_inbox(conversations, events, objections)
        self.assertEqual([], inbox)

    def test_closed_conversation_excluded_even_with_pending_objection(self) -> None:
        conversations = [self._conversation("c1", status="closed")]
        events = [_event("replied", conversation_id="c1", engagement_event_id="ee1")]
        objections = [classify_objection(
            objection_id="o1", engagement_event_id="ee1", category="price",
            confidence=0.2, raised_at="2026-01-01T00:00:00Z",
        )]
        inbox = build_engagement_inbox(conversations, events, objections)
        self.assertEqual([], inbox)

    def test_inbox_ordered_oldest_conversation_first(self) -> None:
        conversations = [
            self._conversation("c1", created_at="2026-01-05T00:00:00Z"),
            self._conversation("c2", created_at="2026-01-01T00:00:00Z"),
        ]
        events = [
            _event("replied", conversation_id="c1", engagement_event_id="ee1"),
            _event("replied", conversation_id="c2", engagement_event_id="ee2"),
        ]
        objections = [
            classify_objection(objection_id="o1", engagement_event_id="ee1", category="price", confidence=0.1, raised_at="2026-01-05T00:00:00Z"),
            classify_objection(objection_id="o2", engagement_event_id="ee2", category="price", confidence=0.1, raised_at="2026-01-01T00:00:00Z"),
        ]
        inbox = build_engagement_inbox(conversations, events, objections)
        self.assertEqual(["c2", "c1"], [c["conversation_id"] for c in inbox])


if __name__ == "__main__":
    unittest.main()
