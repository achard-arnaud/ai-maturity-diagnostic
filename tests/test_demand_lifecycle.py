from __future__ import annotations

import unittest

from app.demand_lifecycle import (
    DemandLifecycleError,
    can_transition,
    mark_stale,
    qualify_demand,
    reject_demand,
    reopen_demand,
    run_qualification_checklist,
    transition_to_qualifying,
)
from app.demand_policy import known, unknown


def _demand(**kwargs) -> dict:
    base = {
        "demand_id": "d1",
        "workspace_id": "ws-a",
        "company_entity_id": "entity_1",
        "status": "observed",
        "problem": known("manual onboarding"),
        "population": unknown(),
        "impact": unknown(),
        "urgency": unknown(),
        "initiative": unknown(),
        "sponsor": known("VP Sales"),
        "budget": unknown(),
        "timing": unknown(),
        "claim_ids": [],
        "origin_profile_ref": None,
        "created_at": "2026-01-01T00:00:00+00:00",
        "updated_at": "2026-01-01T00:00:00+00:00",
    }
    base.update(kwargs)
    return base


class TransitionTableTests(unittest.TestCase):
    def test_observed_to_qualifying_allowed(self) -> None:
        self.assertTrue(can_transition("observed", "qualifying"))

    def test_observed_to_qualified_not_allowed_directly(self) -> None:
        self.assertFalse(can_transition("observed", "qualified"))

    def test_qualified_to_stale_allowed(self) -> None:
        self.assertTrue(can_transition("qualified", "stale"))

    def test_stale_to_reopened_allowed(self) -> None:
        self.assertTrue(can_transition("stale", "reopened"))

    def test_rejected_to_qualified_not_allowed(self) -> None:
        self.assertFalse(can_transition("rejected", "qualified"))


class QualificationChecklistTests(unittest.TestCase):
    def test_problem_and_buying_signal_known_passes(self) -> None:
        checklist = run_qualification_checklist(_demand())
        self.assertTrue(checklist.passed)

    def test_unknown_problem_fails_with_explicit_reason(self) -> None:
        demand = _demand(problem=unknown())
        checklist = run_qualification_checklist(demand)
        self.assertFalse(checklist.passed)
        self.assertTrue(any("problem" in m for m in checklist.missing))

    def test_no_buying_signal_fails_with_explicit_reason(self) -> None:
        demand = _demand(sponsor=unknown())
        checklist = run_qualification_checklist(demand)
        self.assertFalse(checklist.passed)
        self.assertTrue(any("buying signal" in m for m in checklist.missing))


class QualifyDemandTests(unittest.TestCase):
    def test_qualify_requires_qualifying_status(self) -> None:
        with self.assertRaises(DemandLifecycleError):
            qualify_demand(_demand(status="observed"), updated_at="2026-01-05T00:00:00+00:00")

    def test_qualify_succeeds_from_qualifying_when_checklist_passes(self) -> None:
        qualified = qualify_demand(_demand(status="qualifying"), updated_at="2026-01-05T00:00:00+00:00")
        self.assertEqual("qualified", qualified["status"])

    def test_qualify_fails_and_names_missing_dimension(self) -> None:
        demand = _demand(status="qualifying", problem=unknown())
        with self.assertRaises(DemandLifecycleError) as ctx:
            qualify_demand(demand, updated_at="2026-01-05T00:00:00+00:00")
        self.assertIn("problem", str(ctx.exception))

    def test_failing_checklist_cannot_be_bypassed_by_any_other_call(self) -> None:
        # There is no function in this module other than qualify_demand
        # that can produce status="qualified" -- transition_to_qualifying
        # only reaches "qualifying", never "qualified".
        demand = _demand(status="observed", problem=unknown())
        moved = transition_to_qualifying(demand, updated_at="2026-01-02T00:00:00+00:00")
        self.assertEqual("qualifying", moved["status"])
        with self.assertRaises(DemandLifecycleError):
            qualify_demand(moved, updated_at="2026-01-05T00:00:00+00:00")


class RejectStaleReopenTests(unittest.TestCase):
    def test_reject_requires_reason(self) -> None:
        with self.assertRaises(DemandLifecycleError):
            reject_demand(_demand(status="qualifying"), reason="", updated_at="2026-01-05T00:00:00+00:00")

    def test_reject_succeeds_with_reason(self) -> None:
        rejected = reject_demand(_demand(status="qualifying"), reason="not a fit for their org", updated_at="2026-01-05T00:00:00+00:00")
        self.assertEqual("rejected", rejected["status"])

    def test_mark_stale_requires_reason(self) -> None:
        with self.assertRaises(DemandLifecycleError):
            mark_stale(_demand(status="qualified"), reason="", updated_at="2026-01-05T00:00:00+00:00")

    def test_mark_stale_succeeds_with_reason(self) -> None:
        staled = mark_stale(_demand(status="qualified"), reason="sponsor left the company", updated_at="2026-01-05T00:00:00+00:00")
        self.assertEqual("stale", staled["status"])

    def test_reopen_requires_reason(self) -> None:
        with self.assertRaises(DemandLifecycleError):
            reopen_demand(_demand(status="stale"), reason="", updated_at="2026-01-05T00:00:00+00:00")

    def test_reopen_succeeds_with_reason(self) -> None:
        reopened = reopen_demand(_demand(status="stale"), reason="new sponsor identified", updated_at="2026-01-05T00:00:00+00:00")
        self.assertEqual("reopened", reopened["status"])


class ExplicableTransitionsProperty(unittest.TestCase):
    """Property: every DemandLifecycleError this module raises carries a
    non-empty, specific reason -- never a bare/opaque failure."""

    def test_all_rejected_transitions_have_specific_reasons(self) -> None:
        cases = [
            lambda: qualify_demand(_demand(status="observed"), updated_at="x"),
            lambda: qualify_demand(_demand(status="qualifying", problem=unknown()), updated_at="x"),
            lambda: reject_demand(_demand(status="qualifying"), reason="", updated_at="x"),
            lambda: mark_stale(_demand(status="qualified"), reason="", updated_at="x"),
            lambda: reopen_demand(_demand(status="stale"), reason="", updated_at="x"),
        ]
        for case in cases:
            with self.assertRaises(DemandLifecycleError) as ctx:
                case()
            self.assertTrue(len(ctx.exception.reason) > 10)


if __name__ == "__main__":
    unittest.main()
