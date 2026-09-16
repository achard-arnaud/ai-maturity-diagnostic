from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.target_plan_store import (
    TargetPlanNotFound,
    get_plan,
    list_plans,
    list_stakeholders_for_plan,
    put_plan,
    put_stakeholder,
)


def _plan(target_plan_id: str, *, status: str = "draft") -> dict:
    return {
        "target_plan_id": target_plan_id, "workspace_id": "ws-a", "company_entity_id": "c1",
        "fit_assessment_id": "fa1", "status": status, "created_at": "2026-01-01T00:00:00+00:00", "updated_at": None,
    }


def _stakeholder(sid: str, target_plan_id: str) -> dict:
    return {
        "stakeholder_role_id": sid, "target_plan_id": target_plan_id, "person_entity_id": "e1",
        "role": "sponsor", "title": "VP", "status": "active", "assigned_at": "2026-01-01T00:00:00+00:00",
        "assigned_by": "alice", "supersedes_stakeholder_role_id": None,
    }


class TargetPlanStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_put_then_get_round_trips(self) -> None:
        put_plan(self.root, "ws-a", _plan("tp1"))
        record = get_plan(self.root, "ws-a", "tp1")
        self.assertEqual("tp1", record["target_plan_id"])

    def test_get_missing_raises(self) -> None:
        with self.assertRaises(TargetPlanNotFound):
            get_plan(self.root, "ws-a", "nope")

    def test_workspaces_are_isolated(self) -> None:
        put_plan(self.root, "ws-a", _plan("tp1"))
        with self.assertRaises(TargetPlanNotFound):
            get_plan(self.root, "ws-b", "tp1")

    def test_filter_by_status(self) -> None:
        put_plan(self.root, "ws-a", _plan("tp1", status="draft"))
        put_plan(self.root, "ws-a", _plan("tp2", status="active"))
        page = list_plans(self.root, "ws-a", status="active")
        self.assertEqual(["tp2"], [p["target_plan_id"] for p in page.items])

    def test_pagination_cursor(self) -> None:
        for i in range(5):
            put_plan(self.root, "ws-a", _plan(f"tp{i}"))
        page = list_plans(self.root, "ws-a", limit=2)
        self.assertEqual(2, len(page.items))
        self.assertIsNotNone(page.next_cursor)

    def test_stakeholders_scoped_to_plan(self) -> None:
        put_stakeholder(self.root, "ws-a", _stakeholder("sr1", "tp1"))
        put_stakeholder(self.root, "ws-a", _stakeholder("sr2", "tp2"))
        stakeholders = list_stakeholders_for_plan(self.root, "ws-a", "tp1")
        self.assertEqual(["sr1"], [s["stakeholder_role_id"] for s in stakeholders])


if __name__ == "__main__":
    unittest.main()
