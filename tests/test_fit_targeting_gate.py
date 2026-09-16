from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.fit_gates import GateResult, can_compute_score
from app.fit_lifecycle import decide_fit, submit_for_review
from app.fit_policy import create_input_lock
from app.fit_scoring import compute_coverage, compute_explainable_score
from app.fit_store import create_fit, get_fit, update_fit
from app.fit_targeting_gate import can_create_target_plan


def _dimension_checks(problem_covered: bool, impact_covered: bool) -> list[dict]:
    return [
        {"dimension": "problem", "covered": problem_covered, "rationale": "reviewed"},
        {"dimension": "impact", "covered": impact_covered, "rationale": "reviewed"},
    ]


class CanCreateTargetPlanUnitTests(unittest.TestCase):
    def _fit(self, **kwargs) -> dict:
        base = {"fit_assessment_id": "fa1", "status": "draft", "verdict": None}
        base.update(kwargs)
        return base

    def test_not_decided_is_blocked(self) -> None:
        allowed, reason = can_create_target_plan(self._fit(status="in_review"), now="2026-01-01T00:00:00+00:00")
        self.assertFalse(allowed)
        self.assertIn("not decided", reason)

    def test_reject_verdict_is_blocked(self) -> None:
        fit = self._fit(status="decided", verdict={"verdict": "REJECT", "override": False})
        allowed, reason = can_create_target_plan(fit, now="2026-01-01T00:00:00+00:00")
        self.assertFalse(allowed)
        self.assertIn("not PURSUE", reason)

    def test_pursue_verdict_allows_target_plan(self) -> None:
        fit = self._fit(status="decided", verdict={"verdict": "PURSUE", "override": False})
        allowed, reason = can_create_target_plan(fit, now="2026-01-01T00:00:00+00:00")
        self.assertTrue(allowed)
        self.assertIsNone(reason)

    def test_expired_override_blocks_target_plan(self) -> None:
        fit = self._fit(
            status="decided",
            verdict={"verdict": "PURSUE", "override": True, "override_expiry": "2026-01-01T00:00:00+00:00"},
        )
        allowed, reason = can_create_target_plan(fit, now="2026-06-01T00:00:00+00:00")
        self.assertFalse(allowed)
        self.assertIn("expired", reason)

    def test_unexpired_override_allows_target_plan(self) -> None:
        fit = self._fit(
            status="decided",
            verdict={"verdict": "PURSUE", "override": True, "override_expiry": "2026-12-01T00:00:00+00:00"},
        )
        allowed, _ = can_create_target_plan(fit, now="2026-06-01T00:00:00+00:00")
        self.assertTrue(allowed)


class DemandToFitToTargetingE2ETests(unittest.TestCase):
    """Epic 07 S06's own stop condition: 'target creation gated' -- the
    full chain from a locked FitAssessment through gates, scoring,
    review and decision must correctly gate (or authorize) a subsequent
    TargetPlan creation."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _create_draft_fit(self, fit_id: str) -> dict:
        lock = create_input_lock("d1", 2, "snap1")
        assessment = {
            "fit_assessment_id": fit_id,
            "workspace_id": "ws-a",
            "input_lock": {
                "demand_id": lock.demand_id, "demand_version": lock.demand_version,
                "product_snapshot_id": lock.product_snapshot_id, "input_hash": lock.input_hash,
            },
            "status": "draft",
            "gates": [], "coverage": None, "gaps": [], "alternatives": [], "counter_evidence": [],
            "score": None, "verdict": None,
            "created_at": "2026-01-01T00:00:00+00:00", "updated_at": None,
        }
        create_fit(self.root, "ws-a", assessment)
        return assessment

    def test_e2e_gates_pass_score_high_pursue_authorizes_targeting(self) -> None:
        self._create_draft_fit("fa-pass")
        assessment, version = get_fit(self.root, "ws-a", "fa-pass")
        assessment = submit_for_review(assessment)
        update_fit(self.root, "ws-a", "fa-pass", lambda d: assessment, expected_version=version)

        gates = [GateResult("SOC2", "SOC2", True)]
        self.assertTrue(can_compute_score(gates, open_blocker_count=0))

        checks = _dimension_checks(problem_covered=True, impact_covered=True)
        coverage = compute_coverage(checks)
        score = compute_explainable_score(checks)
        self.assertEqual(1.0, coverage.coverage_ratio)

        assessment, version = get_fit(self.root, "ws-a", "fa-pass")
        decided = decide_fit(
            self.root, assessment, verdict="PURSUE", gates=gates, open_blocker_count=0,
            score_value=score.value, decided_by="alice", actor_role="fit_reviewer",
            decided_at="2026-01-05T00:00:00+00:00",
        )
        update_fit(self.root, "ws-a", "fa-pass", lambda d: decided, expected_version=version)

        final, _ = get_fit(self.root, "ws-a", "fa-pass")
        allowed, reason = can_create_target_plan(final, now="2026-01-06T00:00:00+00:00")
        self.assertTrue(allowed, reason)

    def test_e2e_failed_gate_blocks_pursue_and_targeting(self) -> None:
        self._create_draft_fit("fa-fail")
        assessment, version = get_fit(self.root, "ws-a", "fa-fail")
        assessment = submit_for_review(assessment)
        update_fit(self.root, "ws-a", "fa-fail", lambda d: assessment, expected_version=version)

        gates = [GateResult("SOC2", "SOC2", False, reason="no certification")]
        self.assertFalse(can_compute_score(gates, open_blocker_count=0))

        assessment, version = get_fit(self.root, "ws-a", "fa-fail")
        with self.assertRaises(Exception):
            decide_fit(
                self.root, assessment, verdict="PURSUE", gates=gates, open_blocker_count=0,
                score_value=0.9, decided_by="alice", actor_role="fit_reviewer",
                decided_at="2026-01-05T00:00:00+00:00",
            )

        # Reject instead -- always allowed regardless of gate state.
        decided = decide_fit(
            self.root, assessment, verdict="REJECT", gates=gates, open_blocker_count=0,
            score_value=0.0, decided_by="alice", actor_role="fit_reviewer",
            decided_at="2026-01-05T00:00:00+00:00",
        )
        update_fit(self.root, "ws-a", "fa-fail", lambda d: decided, expected_version=version)

        final, _ = get_fit(self.root, "ws-a", "fa-fail")
        allowed, reason = can_create_target_plan(final, now="2026-01-06T00:00:00+00:00")
        self.assertFalse(allowed)
        self.assertIn("not PURSUE", reason)

    def test_e2e_draft_fit_never_authorizes_targeting(self) -> None:
        self._create_draft_fit("fa-draft")
        draft, _ = get_fit(self.root, "ws-a", "fa-draft")
        allowed, reason = can_create_target_plan(draft, now="2026-01-06T00:00:00+00:00")
        self.assertFalse(allowed)
        self.assertIn("not decided", reason)


if __name__ == "__main__":
    unittest.main()
