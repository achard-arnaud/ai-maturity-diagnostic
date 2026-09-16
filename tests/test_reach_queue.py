from __future__ import annotations

import unittest

from app.reach_queue import (
    DuplicateRetryError,
    InvalidTransitionError,
    build_priority_queue,
    cancel_sequence,
    is_task_overdue,
    pause_sequence,
    resume_sequence,
    retry_step,
)


def _task(task_id: str, *, status: str = "open", priority: int = 0, due_at: str = "2026-01-01T00:00:00Z") -> dict:
    return {"task_id": task_id, "status": status, "priority": priority, "due_at": due_at}


def _step(step_id: str, *, status: str = "pending") -> dict:
    return {"step_id": step_id, "status": status}


def _sequence(status: str = "active") -> dict:
    return {"sequence_id": "seq-1", "status": status}


class BuildPriorityQueueTests(unittest.TestCase):
    def test_terminal_tasks_excluded(self) -> None:
        tasks = [_task("t1", status="done"), _task("t2", status="open")]
        queue = build_priority_queue(tasks, now="2026-01-02T00:00:00Z")
        self.assertEqual(["t2"], [e.task_id for e in queue])

    def test_overdue_ranked_before_non_overdue(self) -> None:
        tasks = [
            _task("t1", due_at="2026-01-05T00:00:00Z"),
            _task("t2", due_at="2026-01-01T00:00:00Z"),
        ]
        queue = build_priority_queue(tasks, now="2026-01-03T00:00:00Z")
        self.assertEqual(["t2", "t1"], [e.task_id for e in queue])

    def test_higher_priority_ranked_first_within_same_overdue_bucket(self) -> None:
        tasks = [
            _task("t1", priority=1, due_at="2026-02-01T00:00:00Z"),
            _task("t2", priority=5, due_at="2026-02-01T00:00:00Z"),
        ]
        queue = build_priority_queue(tasks, now="2026-01-01T00:00:00Z")
        self.assertEqual(["t2", "t1"], [e.task_id for e in queue])

    def test_deterministic_ordering_stable_regardless_of_input_order(self) -> None:
        tasks_a = [_task("t1"), _task("t2"), _task("t3")]
        tasks_b = [_task("t3"), _task("t1"), _task("t2")]
        now = "2026-01-01T00:00:00Z"
        self.assertEqual(
            [e.task_id for e in build_priority_queue(tasks_a, now=now)],
            [e.task_id for e in build_priority_queue(tasks_b, now=now)],
        )


class RetryStepTests(unittest.TestCase):
    def test_retry_allowed_with_no_prior_attempts(self) -> None:
        result = retry_step(_step("s1"), attempts=[])
        self.assertEqual("prepared", result["status"])
        self.assertEqual(1, result["attempt_number"])

    def test_retry_refused_when_attempt_already_prepared(self) -> None:
        attempts = [{"step_id": "s1", "status": "prepared"}]
        with self.assertRaises(DuplicateRetryError):
            retry_step(_step("s1"), attempts=attempts)

    def test_retry_refused_when_attempt_already_sent(self) -> None:
        attempts = [{"step_id": "s1", "status": "sent"}]
        with self.assertRaises(DuplicateRetryError):
            retry_step(_step("s1"), attempts=attempts)

    def test_retry_allowed_after_prior_attempt_failed(self) -> None:
        attempts = [{"step_id": "s1", "status": "failed"}]
        result = retry_step(_step("s1"), attempts=attempts)
        self.assertEqual(2, result["attempt_number"])

    def test_retry_refused_on_terminal_step(self) -> None:
        with self.assertRaises(InvalidTransitionError):
            retry_step(_step("s1", status="sent"), attempts=[])

    def test_retry_only_matches_same_step_id(self) -> None:
        attempts = [{"step_id": "other", "status": "sent"}]
        result = retry_step(_step("s1"), attempts=attempts)
        self.assertEqual("prepared", result["status"])


class PauseResumeTests(unittest.TestCase):
    def test_pause_active_sequence(self) -> None:
        result = pause_sequence(_sequence("active"))
        self.assertEqual("paused", result["status"])

    def test_pause_refused_when_not_active(self) -> None:
        with self.assertRaises(InvalidTransitionError):
            pause_sequence(_sequence("draft"))

    def test_resume_paused_sequence(self) -> None:
        result = resume_sequence(_sequence("paused"))
        self.assertEqual("active", result["status"])

    def test_resume_refused_when_not_paused(self) -> None:
        with self.assertRaises(InvalidTransitionError):
            resume_sequence(_sequence("active"))


class CancelSequenceTests(unittest.TestCase):
    def test_cancel_cascades_to_open_tasks_and_steps(self) -> None:
        tasks = [_task("t1", status="open")]
        steps = [_step("s1", status="pending")]
        seq, updated_tasks, updated_steps = cancel_sequence(_sequence("active"), tasks=tasks, steps=steps)
        self.assertEqual("cancelled", seq["status"])
        self.assertEqual("skipped", updated_tasks[0]["status"])
        self.assertEqual("cancelled", updated_steps[0]["status"])

    def test_cancel_leaves_terminal_tasks_and_steps_untouched(self) -> None:
        tasks = [_task("t1", status="done")]
        steps = [_step("s1", status="sent")]
        _, updated_tasks, updated_steps = cancel_sequence(_sequence("active"), tasks=tasks, steps=steps)
        self.assertEqual("done", updated_tasks[0]["status"])
        self.assertEqual("sent", updated_steps[0]["status"])

    def test_cancel_refused_on_already_cancelled_sequence(self) -> None:
        with self.assertRaises(InvalidTransitionError):
            cancel_sequence(_sequence("cancelled"), tasks=[], steps=[])

    def test_cancel_allowed_from_draft(self) -> None:
        seq, _, _ = cancel_sequence(_sequence("draft"), tasks=[], steps=[])
        self.assertEqual("cancelled", seq["status"])


class OverdueTests(unittest.TestCase):
    def test_open_task_past_due_is_overdue(self) -> None:
        self.assertTrue(is_task_overdue(_task("t1", due_at="2026-01-01T00:00:00Z"), now="2026-01-02T00:00:00Z"))

    def test_done_task_is_never_overdue(self) -> None:
        self.assertFalse(
            is_task_overdue(_task("t1", status="done", due_at="2026-01-01T00:00:00Z"), now="2026-01-02T00:00:00Z")
        )


if __name__ == "__main__":
    unittest.main()
