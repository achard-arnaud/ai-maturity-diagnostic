from __future__ import annotations

import unittest

from app.engagement_classification import build_review_queue, can_act_on_objection, classify_objection, review_objection
from app.engagement_inbox import apply_engagement_to_sequence, build_engagement_inbox
from app.engagement_ingestion import correlate_touchpoint, ingest_engagement_event
from app.engagement_opportunity import propose_opportunity
from app.engagement_policy import open_conversation


def _sequence(status: str = "active") -> dict:
    return {"sequence_id": "seq1", "status": status}


def _touchpoint(touchpoint_id: str, sent_at: str) -> dict:
    return {"touchpoint_id": touchpoint_id, "channel": "email", "status": "sent", "sent_at": sent_at}


class ClosedLoopE2ETests(unittest.TestCase):
    """Epic 10 S05's own stop condition: 'boucle fermée' -- a reply
    must flow all the way from ingestion through classification,
    follow-up and back onto the Reach sequence it came from."""

    def test_e2e_low_confidence_reply_pauses_reach_then_review_unblocks_action(self) -> None:
        conversation = open_conversation(
            conversation_id="c1", workspace_id="ws-a", target_plan_id="tp1",
            stakeholder_role_id="sr1", created_at="2026-01-01T00:00:00Z", sequence_id="seq1",
        )
        sent_touchpoints = [_touchpoint("tp1", "2026-01-02T00:00:00Z")]

        ingestion = ingest_engagement_event(
            engagement_event_id="ee1", conversation_id="c1", kind="replied", channel="email",
            occurred_at="2026-01-04T00:00:00Z", source_ref="msg-abc", existing_events=[],
        )
        self.assertTrue(ingestion.created)
        event = ingestion.event

        correlated_touchpoint_id = correlate_touchpoint(
            channel=event["channel"], occurred_at=event["occurred_at"], candidate_touchpoints=sent_touchpoints,
        )
        self.assertEqual("tp1", correlated_touchpoint_id)

        objection = classify_objection(
            objection_id="o1", engagement_event_id="ee1", category="price",
            confidence=0.3, raised_at="2026-01-04T00:00:00Z",
        )
        self.assertFalse(can_act_on_objection(objection))

        sequence, _, _, action = apply_engagement_to_sequence(event, _sequence("active"))
        self.assertEqual("paused", sequence["status"])
        self.assertEqual("paused", action)

        inbox = build_engagement_inbox([conversation], [event], [objection])
        self.assertEqual(["c1"], [c["conversation_id"] for c in inbox])

        reviewed = review_objection(objection, reviewed_by="alice", reviewed_at="2026-01-05T00:00:00Z")
        self.assertTrue(can_act_on_objection(reviewed))
        self.assertEqual([], build_review_queue([reviewed]))

    def test_e2e_meeting_booked_pauses_reach_and_proposes_opportunity(self) -> None:
        ingestion = ingest_engagement_event(
            engagement_event_id="ee2", conversation_id="c1", kind="meeting_booked", channel="email",
            occurred_at="2026-01-04T00:00:00Z", source_ref="msg-xyz", existing_events=[],
        )
        event = ingestion.event

        sequence, _, _, action = apply_engagement_to_sequence(event, _sequence("active"))
        self.assertEqual("paused", sequence["status"])
        self.assertEqual("paused", action)

        proposal = propose_opportunity(event)
        self.assertIsNotNone(proposal)
        self.assertEqual("proposed", proposal["status"])

    def test_e2e_opt_out_cancels_reach_and_reingesting_it_is_idempotent(self) -> None:
        first = ingest_engagement_event(
            engagement_event_id="ee3", conversation_id="c1", kind="opted_out", channel="email",
            occurred_at="2026-01-04T00:00:00Z", source_ref="msg-optout", existing_events=[],
        )
        sequence, tasks, steps, action = apply_engagement_to_sequence(
            first.event, _sequence("active"),
            tasks=[{"task_id": "t1", "status": "open"}], steps=[{"step_id": "s1", "status": "pending"}],
        )
        self.assertEqual("cancelled", sequence["status"])
        self.assertEqual("cancelled", action)
        self.assertEqual("skipped", tasks[0]["status"])

        second = ingest_engagement_event(
            engagement_event_id="ee-dup", conversation_id="c1", kind="opted_out", channel="email",
            occurred_at="2026-01-05T00:00:00Z", source_ref="msg-optout", existing_events=[first.event],
        )
        self.assertFalse(second.created)

        re_applied_sequence, _, _, re_action = apply_engagement_to_sequence(second.event, sequence)
        self.assertEqual("cancelled", re_applied_sequence["status"])
        self.assertEqual("already_cancelled", re_action)


if __name__ == "__main__":
    unittest.main()
