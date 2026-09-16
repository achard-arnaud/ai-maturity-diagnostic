from __future__ import annotations

import unittest

from app.target_currentness import ReadinessResult
from app.target_plan_workflow import (
    TargetPlanWorkflowError,
    activate_plan,
    build_stakeholder_blockers,
    can_activate_plan,
    create_target_plan,
    mark_plan_stale,
)


def _fit(status: str = "decided", verdict_verdict: str = "PURSUE") -> dict:
    return {
        "fit_assessment_id": "fa1",
        "status": status,
        "verdict": {"verdict": verdict_verdict, "override": False} if verdict_verdict else None,
    }


def _stakeholder(sid: str, role: str) -> dict:
    return {"stakeholder_role_id": sid, "role": role, "person_entity_id": f"entity_{sid}", "status": "active"}


class CreateTargetPlanTests(unittest.TestCase):
    def test_create_requires_authorized_fit(self) -> None:
        with self.assertRaises(TargetPlanWorkflowError):
            create_target_plan(
                _fit(status="draft"), target_plan_id="tp1", workspace_id="ws-a",
                company_entity_id="c1", created_at="2026-01-01T00:00:00+00:00",
            )

    def test_create_succeeds_with_authorized_fit(self) -> None:
        plan = create_target_plan(
            _fit(), target_plan_id="tp1", workspace_id="ws-a",
            company_entity_id="c1", created_at="2026-01-01T00:00:00+00:00",
        )
        self.assertEqual("draft", plan["status"])
        self.assertEqual("fa1", plan["fit_assessment_id"])

    def test_create_rejects_rejected_verdict(self) -> None:
        with self.assertRaises(TargetPlanWorkflowError):
            create_target_plan(
                _fit(verdict_verdict="REJECT"), target_plan_id="tp1", workspace_id="ws-a",
                company_entity_id="c1", created_at="2026-01-01T00:00:00+00:00",
            )


class BlockersTests(unittest.TestCase):
    def test_no_blockers_when_all_ready(self) -> None:
        stakeholders = [_stakeholder("sr1", "sponsor")]
        readiness = {"sr1": ReadinessResult(True, ())}
        blockers = build_stakeholder_blockers(stakeholders, readiness)
        self.assertEqual([], blockers)

    def test_actionable_blocker_for_not_ready_stakeholder(self) -> None:
        stakeholders = [_stakeholder("sr1", "sponsor")]
        readiness = {"sr1": ReadinessResult(False, ("currentness insufficient -- relationship is not current",))}
        blockers = build_stakeholder_blockers(stakeholders, readiness)
        self.assertEqual(1, len(blockers))
        self.assertIn("currentness insufficient", blockers[0].why_blocked)
        self.assertTrue(blockers[0].cta)


class CanActivatePlanTests(unittest.TestCase):
    def test_ready_sponsor_allows_activation(self) -> None:
        stakeholders = [_stakeholder("sr1", "sponsor")]
        readiness = {"sr1": ReadinessResult(True, ())}
        allowed, blockers = can_activate_plan(stakeholders, readiness)
        self.assertTrue(allowed)
        self.assertEqual([], blockers)

    def test_no_authority_stakeholder_blocks_with_actionable_reason(self) -> None:
        stakeholders = [_stakeholder("sr1", "technique")]
        readiness = {"sr1": ReadinessResult(True, ())}
        allowed, blockers = can_activate_plan(stakeholders, readiness)
        self.assertFalse(allowed)
        self.assertEqual(1, len(blockers))
        self.assertIn("no ready sponsor or champion", blockers[0].why_blocked)
        self.assertTrue(blockers[0].cta)

    def test_not_ready_sponsor_blocks(self) -> None:
        stakeholders = [_stakeholder("sr1", "sponsor")]
        readiness = {"sr1": ReadinessResult(False, ("authority not evidenced",))}
        allowed, blockers = can_activate_plan(stakeholders, readiness)
        self.assertFalse(allowed)
        self.assertTrue(any("no ready sponsor or champion" in b.why_blocked for b in blockers))
        self.assertTrue(any("authority not evidenced" in b.why_blocked for b in blockers))

    def test_ready_champion_alone_is_sufficient(self) -> None:
        stakeholders = [_stakeholder("sr1", "champion")]
        readiness = {"sr1": ReadinessResult(True, ())}
        allowed, _ = can_activate_plan(stakeholders, readiness)
        self.assertTrue(allowed)

    def test_not_ready_non_authority_stakeholder_still_reported_even_when_activation_allowed(self) -> None:
        stakeholders = [_stakeholder("sr1", "sponsor"), _stakeholder("sr2", "technique")]
        readiness = {"sr1": ReadinessResult(True, ()), "sr2": ReadinessResult(False, ("currentness insufficient",))}
        allowed, blockers = can_activate_plan(stakeholders, readiness)
        self.assertTrue(allowed)
        self.assertEqual(1, len(blockers))
        self.assertEqual("sr2", blockers[0].stakeholder_role_id)


class ActivateAndStaleTests(unittest.TestCase):
    def test_activate_requires_draft_status(self) -> None:
        plan = {"target_plan_id": "tp1", "status": "active"}
        with self.assertRaises(TargetPlanWorkflowError):
            activate_plan(plan, activated_at="2026-01-05T00:00:00+00:00", allowed=True)

    def test_activate_requires_allowed_true(self) -> None:
        plan = {"target_plan_id": "tp1", "status": "draft"}
        with self.assertRaises(TargetPlanWorkflowError):
            activate_plan(plan, activated_at="2026-01-05T00:00:00+00:00", allowed=False)

    def test_activate_succeeds(self) -> None:
        plan = {"target_plan_id": "tp1", "status": "draft"}
        activated = activate_plan(plan, activated_at="2026-01-05T00:00:00+00:00", allowed=True)
        self.assertEqual("active", activated["status"])

    def test_mark_stale_requires_reason(self) -> None:
        plan = {"target_plan_id": "tp1", "status": "active"}
        with self.assertRaises(TargetPlanWorkflowError):
            mark_plan_stale(plan, reason="", marked_at="2026-01-05T00:00:00+00:00")

    def test_mark_stale_succeeds(self) -> None:
        plan = {"target_plan_id": "tp1", "status": "active"}
        staled = mark_plan_stale(plan, reason="fit reopened", marked_at="2026-01-05T00:00:00+00:00")
        self.assertEqual("stale", staled["status"])


if __name__ == "__main__":
    unittest.main()
