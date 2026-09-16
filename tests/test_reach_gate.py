from __future__ import annotations

import unittest

from app.reach_gate import can_initiate_reach
from app.target_currentness import ReadinessResult
from app.target_plan_policy import assign_stakeholder_role
from app.target_plan_workflow import activate_plan, can_activate_plan, create_target_plan


def _fit() -> dict:
    return {"fit_assessment_id": "fa1", "status": "decided", "verdict": {"verdict": "PURSUE", "override": False}}


class CanInitiateReachUnitTests(unittest.TestCase):
    def _plan(self, status: str = "active") -> dict:
        return {"target_plan_id": "tp1", "status": status}

    def _stakeholder(self, status: str = "active") -> dict:
        return {"stakeholder_role_id": "sr1", "status": status}

    def test_inactive_plan_blocks(self) -> None:
        allowed, reason = can_initiate_reach(self._plan(status="draft"), self._stakeholder(), ReadinessResult(True, ()))
        self.assertFalse(allowed)
        self.assertIn("not active", reason)

    def test_inactive_stakeholder_blocks(self) -> None:
        allowed, reason = can_initiate_reach(self._plan(), self._stakeholder(status="superseded"), ReadinessResult(True, ()))
        self.assertFalse(allowed)
        self.assertIn("stakeholder is not active", reason)

    def test_not_ready_stakeholder_blocks(self) -> None:
        allowed, reason = can_initiate_reach(
            self._plan(), self._stakeholder(), ReadinessResult(False, ("currentness insufficient",))
        )
        self.assertFalse(allowed)
        self.assertIn("not ready", reason)

    def test_active_plan_active_ready_stakeholder_allowed(self) -> None:
        allowed, reason = can_initiate_reach(self._plan(), self._stakeholder(), ReadinessResult(True, ()))
        self.assertTrue(allowed)
        self.assertIsNone(reason)


class FitToTargetPlanToReachE2ETests(unittest.TestCase):
    """Epic 08 S06's own stop condition: 'reach gated' -- the full chain
    from an authorized Fit through TargetPlan creation, stakeholder
    assignment, activation, and finally the reach gate must hold, and
    must re-block if readiness lapses after activation (refresh-back)."""

    def test_e2e_authorized_fit_to_ready_reach(self) -> None:
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
        self.assertEqual("active", active_plan["status"])

        reach_allowed, reach_reason = can_initiate_reach(active_plan, sponsor, readiness)
        self.assertTrue(reach_allowed, reach_reason)

    def test_e2e_refresh_back_readiness_lapse_reblocks_reach(self) -> None:
        # Same setup as above, but by the time reach is attempted, the
        # stakeholder's currentness has gone stale (e.g. the underlying
        # relationship changed) -- readiness is re-evaluated fresh, not
        # cached from activation time, so reach must now block.
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

        lapsed_readiness = ReadinessResult(False, ("currentness insufficient -- relationship is not current",))
        reach_allowed, reach_reason = can_initiate_reach(active_plan, sponsor, lapsed_readiness)
        self.assertFalse(reach_allowed)
        self.assertIn("not ready", reach_reason)

    def test_e2e_unauthorized_fit_never_reaches_targeting(self) -> None:
        unauthorized_fit = {"fit_assessment_id": "fa2", "status": "in_review", "verdict": None}
        with self.assertRaises(Exception):
            create_target_plan(
                unauthorized_fit, target_plan_id="tp2", workspace_id="ws-a", company_entity_id="c1",
                created_at="2026-01-01T00:00:00+00:00",
            )


if __name__ == "__main__":
    unittest.main()
