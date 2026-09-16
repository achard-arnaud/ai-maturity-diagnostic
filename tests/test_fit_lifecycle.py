from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.event_journal import EventJournal
from app.fit_gates import GateResult
from app.fit_lifecycle import (
    FitAuthorizationError,
    FitLifecycleError,
    decide_fit,
    is_override_expired,
    mark_stale,
    reopen_fit,
    submit_for_review,
)


def _assessment(**kwargs) -> dict:
    base = {
        "fit_assessment_id": "fa1",
        "workspace_id": "ws-a",
        "status": "in_review",
        "verdict": None,
    }
    base.update(kwargs)
    return base


def _passing_gates() -> list[GateResult]:
    return [GateResult("g1", "g1", True)]


def _failing_gates() -> list[GateResult]:
    return [GateResult("g1", "g1", False, reason="not met")]


class SubmitForReviewTests(unittest.TestCase):
    def test_draft_to_in_review_allowed(self) -> None:
        submitted = submit_for_review(_assessment(status="draft"))
        self.assertEqual("in_review", submitted["status"])

    def test_already_in_review_rejected(self) -> None:
        with self.assertRaises(FitLifecycleError):
            submit_for_review(_assessment(status="in_review"))


class DecideFitTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_requires_fit_reviewer_role(self) -> None:
        with self.assertRaises(FitAuthorizationError):
            decide_fit(
                self.root, _assessment(), verdict="REJECT", gates=_failing_gates(), open_blocker_count=0,
                score_value=0.0, decided_by="alice", actor_role="standard_user", decided_at="2026-01-05T00:00:00+00:00",
            )

    def test_pursue_blocked_by_failed_gate_cannot_be_overridden(self) -> None:
        with self.assertRaises(FitLifecycleError):
            decide_fit(
                self.root, _assessment(), verdict="PURSUE", gates=_failing_gates(), open_blocker_count=0,
                score_value=0.9, decided_by="alice", actor_role="fit_reviewer", decided_at="2026-01-05T00:00:00+00:00",
                override_reason="I really think so", override_expiry="2026-02-01T00:00:00+00:00",
            )

    def test_pursue_blocked_by_open_blocker_cannot_be_overridden(self) -> None:
        with self.assertRaises(FitLifecycleError):
            decide_fit(
                self.root, _assessment(), verdict="PURSUE", gates=_passing_gates(), open_blocker_count=1,
                score_value=0.9, decided_by="alice", actor_role="fit_reviewer", decided_at="2026-01-05T00:00:00+00:00",
                override_reason="reason", override_expiry="2026-02-01T00:00:00+00:00",
            )

    def test_pursue_with_high_score_and_clear_gates_succeeds(self) -> None:
        decided = decide_fit(
            self.root, _assessment(), verdict="PURSUE", gates=_passing_gates(), open_blocker_count=0,
            score_value=0.8, decided_by="alice", actor_role="fit_reviewer", decided_at="2026-01-05T00:00:00+00:00",
        )
        self.assertEqual("decided", decided["status"])
        self.assertFalse(decided["verdict"]["override"])

    def test_pursue_below_threshold_requires_override_reason_and_expiry(self) -> None:
        with self.assertRaises(FitLifecycleError):
            decide_fit(
                self.root, _assessment(), verdict="PURSUE", gates=_passing_gates(), open_blocker_count=0,
                score_value=0.2, decided_by="alice", actor_role="fit_reviewer", decided_at="2026-01-05T00:00:00+00:00",
            )

    def test_pursue_below_threshold_with_reason_but_no_expiry_rejected(self) -> None:
        with self.assertRaises(FitLifecycleError):
            decide_fit(
                self.root, _assessment(), verdict="PURSUE", gates=_passing_gates(), open_blocker_count=0,
                score_value=0.2, decided_by="alice", actor_role="fit_reviewer", decided_at="2026-01-05T00:00:00+00:00",
                override_reason="strategic account",
            )

    def test_pursue_below_threshold_with_bounded_override_succeeds(self) -> None:
        decided = decide_fit(
            self.root, _assessment(), verdict="PURSUE", gates=_passing_gates(), open_blocker_count=0,
            score_value=0.2, decided_by="alice", actor_role="fit_reviewer", decided_at="2026-01-05T00:00:00+00:00",
            override_reason="strategic account", override_expiry="2026-02-01T00:00:00+00:00",
        )
        self.assertTrue(decided["verdict"]["override"])
        self.assertEqual("2026-02-01T00:00:00+00:00", decided["verdict"]["override_expiry"])

    def test_reject_never_requires_gates_or_score(self) -> None:
        decided = decide_fit(
            self.root, _assessment(), verdict="REJECT", gates=_failing_gates(), open_blocker_count=3,
            score_value=0.0, decided_by="alice", actor_role="fit_reviewer", decided_at="2026-01-05T00:00:00+00:00",
        )
        self.assertEqual("REJECT", decided["verdict"]["verdict"])

    def test_unknown_verdict_rejected(self) -> None:
        with self.assertRaises(FitLifecycleError):
            decide_fit(
                self.root, _assessment(), verdict="MAYBE", gates=_passing_gates(), open_blocker_count=0,
                score_value=0.8, decided_by="alice", actor_role="fit_reviewer", decided_at="2026-01-05T00:00:00+00:00",
            )

    def test_decide_writes_audit_event(self) -> None:
        decide_fit(
            self.root, _assessment(), verdict="REJECT", gates=_failing_gates(), open_blocker_count=0,
            score_value=0.0, decided_by="alice", actor_role="fit_reviewer", decided_at="2026-01-05T00:00:00+00:00",
        )
        journal = EventJournal(self.root)
        events = list(journal.replay())
        event = next(e for e in events if e["event_type"] == "FitDecided")
        self.assertEqual("alice", event["actor_id"])


class StaleAndReopenTests(unittest.TestCase):
    def test_mark_stale_requires_reason(self) -> None:
        with self.assertRaises(FitLifecycleError):
            mark_stale(_assessment(status="decided"), reason="", marked_at="2026-01-05T00:00:00+00:00")

    def test_mark_stale_succeeds(self) -> None:
        staled = mark_stale(_assessment(status="decided"), reason="demand changed", marked_at="2026-01-05T00:00:00+00:00")
        self.assertEqual("stale", staled["status"])

    def test_reopen_requires_reason(self) -> None:
        with self.assertRaises(FitLifecycleError):
            reopen_fit(_assessment(status="stale"), reason="", reopened_at="2026-01-05T00:00:00+00:00")

    def test_reopen_succeeds(self) -> None:
        reopened = reopen_fit(_assessment(status="stale"), reason="new snapshot published", reopened_at="2026-01-05T00:00:00+00:00")
        self.assertEqual("in_review", reopened["status"])


class OverrideExpiryTests(unittest.TestCase):
    def test_non_override_verdict_never_expires(self) -> None:
        verdict = {"override": False}
        self.assertFalse(is_override_expired(verdict, now="2030-01-01T00:00:00+00:00"))

    def test_override_before_expiry_is_not_expired(self) -> None:
        verdict = {"override": True, "override_expiry": "2026-02-01T00:00:00+00:00"}
        self.assertFalse(is_override_expired(verdict, now="2026-01-15T00:00:00+00:00"))

    def test_override_past_expiry_is_expired(self) -> None:
        verdict = {"override": True, "override_expiry": "2026-02-01T00:00:00+00:00"}
        self.assertTrue(is_override_expired(verdict, now="2026-03-01T00:00:00+00:00"))


if __name__ == "__main__":
    unittest.main()
