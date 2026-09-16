from __future__ import annotations

import unittest

from app.reach_channel_policy import ChannelNotAuthorizedError
from app.reach_execution import build_my_day, prepare_touchpoint, send_touchpoint
from app.reach_gate import can_initiate_reach
from app.reach_message_policy import approve_message, draft_message
from app.target_currentness import ReadinessResult
from app.target_plan_policy import assign_stakeholder_role
from app.target_plan_workflow import activate_plan, can_activate_plan, create_target_plan


def _fit() -> dict:
    return {"fit_assessment_id": "fa1", "status": "decided", "verdict": {"verdict": "PURSUE", "override": False}}


def _step(step_id: str = "s1", channel: str = "email") -> dict:
    return {"step_id": step_id, "sequence_id": "seq1", "order": 1, "channel": channel, "status": "pending"}


def _claim(claim_id: str, statement: str) -> dict:
    return {"claim_id": claim_id, "statement": statement, "status": "active"}


class PrepareTouchpointTests(unittest.TestCase):
    def test_prepare_from_approved_message_is_never_sent(self) -> None:
        message = draft_message(content="Hi", citations=[])
        approved = approve_message(message, claims_by_id={}, actor_role="reach_reviewer")
        touchpoint = prepare_touchpoint(_step(), message=approved, touchpoint_id="tp1")
        self.assertEqual("prepared", touchpoint["status"])
        self.assertIsNone(touchpoint["sent_at"])

    def test_prepare_refuses_a_draft_message(self) -> None:
        message = draft_message(content="Hi", citations=[])
        with self.assertRaises(ValueError):
            prepare_touchpoint(_step(), message=message, touchpoint_id="tp1")


class SendTouchpointTests(unittest.TestCase):
    def test_send_email_touchpoint_succeeds(self) -> None:
        message = approve_message(draft_message(content="Hi", citations=[]), claims_by_id={}, actor_role="reach_reviewer")
        touchpoint = prepare_touchpoint(_step(), message=message, touchpoint_id="tp1")
        sent = send_touchpoint(touchpoint, sent_by="alice", sent_at="2026-01-03T00:00:00Z")
        self.assertEqual("sent", sent["status"])
        self.assertEqual("alice", sent["sent_by"])

    def test_send_linkedin_touchpoint_refused(self) -> None:
        message = approve_message(draft_message(content="Hi", citations=[]), claims_by_id={}, actor_role="reach_reviewer")
        touchpoint = prepare_touchpoint(_step(channel="linkedin"), message=message, touchpoint_id="tp1")
        with self.assertRaises(ChannelNotAuthorizedError):
            send_touchpoint(touchpoint, sent_by="alice", sent_at="2026-01-03T00:00:00Z")

    def test_send_refuses_an_already_sent_touchpoint(self) -> None:
        message = approve_message(draft_message(content="Hi", citations=[]), claims_by_id={}, actor_role="reach_reviewer")
        touchpoint = prepare_touchpoint(_step(), message=message, touchpoint_id="tp1")
        sent = send_touchpoint(touchpoint, sent_by="alice", sent_at="2026-01-03T00:00:00Z")
        with self.assertRaises(ValueError):
            send_touchpoint(sent, sent_by="alice", sent_at="2026-01-04T00:00:00Z")


class BuildMyDayTests(unittest.TestCase):
    def _task(self, task_id: str, sequence_id: str, assignee: str = "alice") -> dict:
        return {
            "task_id": task_id, "sequence_id": sequence_id, "assignee": assignee,
            "due_at": "2026-01-01T00:00:00Z", "status": "open", "priority": 0,
        }

    def test_only_own_tasks_from_active_sequences_included(self) -> None:
        tasks = [self._task("t1", "seq1"), self._task("t2", "seq1", assignee="bob"), self._task("t3", "seq2")]
        sequences = {"seq1": {"status": "active"}, "seq2": {"status": "cancelled"}}
        my_day = build_my_day("alice", tasks=tasks, sequences_by_id=sequences, now="2026-01-02T00:00:00Z")
        self.assertEqual(["t1"], [e["task_id"] for e in my_day])

    def test_paused_sequence_tasks_still_included(self) -> None:
        tasks = [self._task("t1", "seq1")]
        sequences = {"seq1": {"status": "paused"}}
        my_day = build_my_day("alice", tasks=tasks, sequences_by_id=sequences, now="2026-01-02T00:00:00Z")
        self.assertEqual(["t1"], [e["task_id"] for e in my_day])


class FullReachExecutionE2ETests(unittest.TestCase):
    """Epic 09 S06's own stop condition: 'opérable sans fichiers' --
    the whole loop from an authorized reach gate through drafting,
    approving, preparing and sending a touchpoint must be drivable
    entirely through these functions."""

    def test_e2e_gated_reach_through_prepare_approve_send(self) -> None:
        plan = create_target_plan(
            _fit(), target_plan_id="tp1", workspace_id="ws-a", company_entity_id="c1",
            created_at="2026-01-01T00:00:00+00:00",
        )
        sponsor = assign_stakeholder_role(
            stakeholder_role_id="sr1", target_plan_id="tp1", person_entity_id="e1",
            role="sponsor", title="VP Sales", assigned_by="alice", assigned_at="2026-01-01T00:00:00+00:00",
        )
        readiness = ReadinessResult(True, ())
        allowed, blockers = can_activate_plan([sponsor], {"sr1": readiness})
        self.assertTrue(allowed, blockers)
        active_plan = activate_plan(plan, activated_at="2026-01-02T00:00:00+00:00", allowed=allowed)
        reach_allowed, reach_reason = can_initiate_reach(active_plan, sponsor, readiness)
        self.assertTrue(reach_allowed, reach_reason)

        claims = {"c1": _claim("c1", "raised a Series B in 2025")}
        message = draft_message(
            content="Congrats on your Series B!", citations=[{"claim_id": "c1", "quoted_text": "Series B"}]
        )
        approved = approve_message(message, claims_by_id=claims, actor_role="reach_reviewer")

        touchpoint = prepare_touchpoint(_step(), message=approved, touchpoint_id="tp-touch1")
        self.assertEqual("prepared", touchpoint["status"])

        sent = send_touchpoint(touchpoint, sent_by="alice", sent_at="2026-01-03T00:00:00Z")
        self.assertEqual("sent", sent["status"])

    def test_e2e_reach_not_gated_blocks_before_any_message_is_drafted(self) -> None:
        plan = create_target_plan(
            _fit(), target_plan_id="tp1", workspace_id="ws-a", company_entity_id="c1",
            created_at="2026-01-01T00:00:00+00:00",
        )
        sponsor = assign_stakeholder_role(
            stakeholder_role_id="sr1", target_plan_id="tp1", person_entity_id="e1",
            role="sponsor", title="VP Sales", assigned_by="alice", assigned_at="2026-01-01T00:00:00+00:00",
        )
        allowed_at_activation, _ = can_activate_plan([sponsor], {"sr1": ReadinessResult(True, ())})
        active_plan = activate_plan(plan, activated_at="2026-01-02T00:00:00+00:00", allowed=allowed_at_activation)

        lapsed_readiness = ReadinessResult(False, ("currentness insufficient",))
        reach_allowed, _ = can_initiate_reach(active_plan, sponsor, lapsed_readiness)
        self.assertFalse(reach_allowed)


if __name__ == "__main__":
    unittest.main()
