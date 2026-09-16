from __future__ import annotations

import unittest

from app.opportunity_policy import (
    OpportunityLifecycleError,
    convert_lead,
    qualify_lead,
    required_exit_criteria,
    transition_opportunity,
)


def _lead(status: str = "qualified") -> dict:
    return {
        "lead_id": "lead-1", "workspace_id": "ws-a", "demand_id": "demand-1", "fit_assessment_id": "fit-1",
        "target_plan_id": "target-1", "source_engagement_event_id": "event-1", "status": status,
    }


def _opportunity(status: str = "draft") -> dict:
    return {
        "opportunity_id": "opp-1", "workspace_id": "ws-a", "lead_id": "lead-1", "demand_id": "demand-1",
        "fit_assessment_id": "fit-1", "target_plan_id": "target-1", "status": status,
    }


class LeadQualificationTests(unittest.TestCase):
    def test_all_upstream_gates_qualify_a_lead(self) -> None:
        qualified = qualify_lead(_lead("disqualified"), fit_verdict="PURSUE", target_plan_status="active", engagement_kind="meeting_booked")
        self.assertEqual("qualified", qualified["status"])

    def test_meeting_without_pursue_fit_cannot_qualify(self) -> None:
        with self.assertRaisesRegex(OpportunityLifecycleError, "PURSUE"):
            qualify_lead(_lead(), fit_verdict="REJECT", target_plan_status="active", engagement_kind="meeting_booked")

    def test_inactive_target_plan_cannot_qualify(self) -> None:
        with self.assertRaisesRegex(OpportunityLifecycleError, "active target"):
            qualify_lead(_lead(), fit_verdict="PURSUE", target_plan_status="stale", engagement_kind="meeting_booked")

    def test_non_meeting_engagement_cannot_qualify(self) -> None:
        with self.assertRaisesRegex(OpportunityLifecycleError, "meeting_booked"):
            qualify_lead(_lead(), fit_verdict="PURSUE", target_plan_status="active", engagement_kind="replied")

    def test_only_qualified_lead_converts(self) -> None:
        self.assertEqual("converted", convert_lead(_lead())["status"])
        with self.assertRaisesRegex(OpportunityLifecycleError, "qualified"):
            convert_lead(_lead("disqualified"))


class OpportunityTransitionTests(unittest.TestCase):
    def test_every_stage_has_explicit_exit_criteria(self) -> None:
        for stage in ("discovery", "proof", "proposal", "closed_won", "closed_lost"):
            self.assertTrue(required_exit_criteria(stage))

    def test_adjacent_transitions_with_all_criteria_are_allowed(self) -> None:
        opportunity = _opportunity()
        for stage in ("discovery", "proof", "proposal", "closed_won"):
            opportunity = transition_opportunity(opportunity, next_stage=stage, completed_criteria=required_exit_criteria(stage))
        self.assertEqual("closed_won", opportunity["status"])

    def test_stage_skip_is_rejected_even_with_future_criteria(self) -> None:
        with self.assertRaisesRegex(OpportunityLifecycleError, "cannot skip"):
            transition_opportunity(_opportunity(), next_stage="proposal", completed_criteria={"lead_converted", "proof_completed", "success_criteria_met"})

    def test_missing_exit_criterion_is_rejected(self) -> None:
        with self.assertRaisesRegex(OpportunityLifecycleError, "stakeholders_confirmed"):
            transition_opportunity(_opportunity("discovery"), next_stage="proof", completed_criteria={"discovery_recorded"})

    def test_closed_stage_is_terminal(self) -> None:
        with self.assertRaisesRegex(OpportunityLifecycleError, "cannot skip"):
            transition_opportunity(_opportunity("closed_lost"), next_stage="discovery", completed_criteria={"lead_converted"})


if __name__ == "__main__":
    unittest.main()
