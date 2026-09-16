from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.reach_store import (
    SequenceNotFound,
    get_sequence,
    list_sequences,
    list_steps_for_sequence,
    list_tasks_for_sequence,
    list_touchpoints_for_step,
    put_sequence,
    put_step,
    put_task,
    put_touchpoint,
)


def _sequence(sequence_id: str, status: str = "active") -> dict:
    return {
        "sequence_id": sequence_id, "workspace_id": "ws-a", "target_plan_id": "tp1",
        "stakeholder_role_id": "sr1", "status": status, "created_at": "2026-01-01T00:00:00Z",
    }


def _step(step_id: str, sequence_id: str, order: int) -> dict:
    return {"step_id": step_id, "sequence_id": sequence_id, "order": order, "channel": "email", "status": "pending"}


def _task(task_id: str, sequence_id: str, step_id: str) -> dict:
    return {
        "task_id": task_id, "sequence_id": sequence_id, "step_id": step_id, "assignee": "alice",
        "due_at": "2026-01-02T00:00:00Z", "status": "open", "created_at": "2026-01-01T00:00:00Z",
    }


def _touchpoint(touchpoint_id: str, step_id: str) -> dict:
    return {
        "touchpoint_id": touchpoint_id, "step_id": step_id, "channel": "email", "content_ref": "msg-1",
        "status": "prepared", "prepared_at": "2026-01-01T00:00:00Z", "sent_at": None, "sent_by": None,
    }


class ReachStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_put_and_get_sequence(self) -> None:
        put_sequence(self.root, "ws-a", _sequence("seq1"))
        record = get_sequence(self.root, "ws-a", "seq1")
        self.assertEqual("seq1", record["sequence_id"])

    def test_get_missing_sequence_raises(self) -> None:
        with self.assertRaises(SequenceNotFound):
            get_sequence(self.root, "ws-a", "missing")

    def test_put_sequence_upserts(self) -> None:
        put_sequence(self.root, "ws-a", _sequence("seq1", status="draft"))
        put_sequence(self.root, "ws-a", _sequence("seq1", status="active"))
        record = get_sequence(self.root, "ws-a", "seq1")
        self.assertEqual("active", record["status"])

    def test_list_sequences_filters_by_status(self) -> None:
        put_sequence(self.root, "ws-a", _sequence("seq1", status="active"))
        put_sequence(self.root, "ws-a", _sequence("seq2", status="paused"))
        page = list_sequences(self.root, "ws-a", status="active")
        self.assertEqual(["seq1"], [r["sequence_id"] for r in page.items])

    def test_list_sequences_workspace_isolated(self) -> None:
        put_sequence(self.root, "ws-a", _sequence("seq1"))
        page = list_sequences(self.root, "ws-b")
        self.assertEqual([], page.items)

    def test_list_sequences_rejects_nonpositive_limit(self) -> None:
        with self.assertRaises(Exception):
            list_sequences(self.root, "ws-a", limit=0)

    def test_steps_ordered_by_order_field(self) -> None:
        put_step(self.root, "ws-a", _step("s2", "seq1", 2))
        put_step(self.root, "ws-a", _step("s1", "seq1", 1))
        steps = list_steps_for_sequence(self.root, "ws-a", "seq1")
        self.assertEqual(["s1", "s2"], [s["step_id"] for s in steps])

    def test_tasks_scoped_to_sequence(self) -> None:
        put_task(self.root, "ws-a", _task("t1", "seq1", "s1"))
        put_task(self.root, "ws-a", _task("t2", "seq2", "s2"))
        tasks = list_tasks_for_sequence(self.root, "ws-a", "seq1")
        self.assertEqual(["t1"], [t["task_id"] for t in tasks])

    def test_touchpoints_scoped_to_step(self) -> None:
        put_touchpoint(self.root, "ws-a", _touchpoint("tp1", "s1"))
        put_touchpoint(self.root, "ws-a", _touchpoint("tp2", "s2"))
        touchpoints = list_touchpoints_for_step(self.root, "ws-a", "s1")
        self.assertEqual(["tp1"], [t["touchpoint_id"] for t in touchpoints])


if __name__ == "__main__":
    unittest.main()
