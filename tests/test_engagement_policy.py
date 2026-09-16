from __future__ import annotations

import unittest

from app.engagement_policy import (
    EngagementPolicyError,
    NotEngagementError,
    close_conversation,
    create_engagement_event,
    is_engagement_kind,
    open_conversation,
)


class IsEngagementKindTests(unittest.TestCase):
    def test_replied_is_engagement(self) -> None:
        self.assertTrue(is_engagement_kind("replied"))

    def test_meeting_booked_is_engagement(self) -> None:
        self.assertTrue(is_engagement_kind("meeting_booked"))

    def test_opted_out_is_engagement(self) -> None:
        self.assertTrue(is_engagement_kind("opted_out"))

    def test_bounced_is_engagement(self) -> None:
        self.assertTrue(is_engagement_kind("bounced"))

    def test_sent_is_not_engagement(self) -> None:
        self.assertFalse(is_engagement_kind("sent"))

    def test_unknown_kind_is_not_engagement(self) -> None:
        self.assertFalse(is_engagement_kind("opened"))


class CreateEngagementEventTests(unittest.TestCase):
    def test_creates_event_from_reply(self) -> None:
        event = create_engagement_event(
            engagement_event_id="ee1", conversation_id="c1", kind="replied", channel="email",
            occurred_at="2026-01-04T00:00:00Z", source_ref="msg-abc",
        )
        self.assertEqual("replied", event["kind"])
        self.assertIsNone(event["touchpoint_id"])

    def test_creates_event_correlated_to_touchpoint(self) -> None:
        event = create_engagement_event(
            engagement_event_id="ee1", conversation_id="c1", kind="replied", channel="email",
            occurred_at="2026-01-04T00:00:00Z", source_ref="msg-abc", touchpoint_id="tp1",
        )
        self.assertEqual("tp1", event["touchpoint_id"])

    def test_refuses_a_sent_kind_gold_case(self) -> None:
        # Gold case: 'outbound ≠ engagement' -- a send is never itself
        # recordable as an EngagementEvent, whatever the caller intends.
        with self.assertRaises(NotEngagementError):
            create_engagement_event(
                engagement_event_id="ee1", conversation_id="c1", kind="sent", channel="email",
                occurred_at="2026-01-04T00:00:00Z", source_ref="msg-abc",
            )

    def test_refuses_an_unknown_kind(self) -> None:
        with self.assertRaises(NotEngagementError):
            create_engagement_event(
                engagement_event_id="ee1", conversation_id="c1", kind="opened", channel="email",
                occurred_at="2026-01-04T00:00:00Z", source_ref="msg-abc",
            )


class ConversationLifecycleTests(unittest.TestCase):
    def test_open_conversation_defaults_no_sequence(self) -> None:
        conv = open_conversation(
            conversation_id="c1", workspace_id="ws-a", target_plan_id="tp1",
            stakeholder_role_id="sr1", created_at="2026-01-01T00:00:00Z",
        )
        self.assertEqual("open", conv["status"])
        self.assertIsNone(conv["sequence_id"])

    def test_open_conversation_with_sequence(self) -> None:
        conv = open_conversation(
            conversation_id="c1", workspace_id="ws-a", target_plan_id="tp1",
            stakeholder_role_id="sr1", created_at="2026-01-01T00:00:00Z", sequence_id="seq1",
        )
        self.assertEqual("seq1", conv["sequence_id"])

    def test_close_open_conversation(self) -> None:
        conv = open_conversation(
            conversation_id="c1", workspace_id="ws-a", target_plan_id="tp1",
            stakeholder_role_id="sr1", created_at="2026-01-01T00:00:00Z",
        )
        closed = close_conversation(conv)
        self.assertEqual("closed", closed["status"])

    def test_close_already_closed_conversation_refused(self) -> None:
        conv = open_conversation(
            conversation_id="c1", workspace_id="ws-a", target_plan_id="tp1",
            stakeholder_role_id="sr1", created_at="2026-01-01T00:00:00Z",
        )
        closed = close_conversation(conv)
        with self.assertRaises(EngagementPolicyError):
            close_conversation(closed)


if __name__ == "__main__":
    unittest.main()
