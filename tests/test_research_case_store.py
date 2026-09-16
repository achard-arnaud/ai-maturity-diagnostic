from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.research_case_store import (
    ResearchCaseNotFound,
    get_case,
    list_cases,
    put_case,
)


def _case(research_case_id: str, *, status: str = "open", owner: str | None = None) -> dict:
    return {
        "research_case_id": research_case_id,
        "workspace_id": "ws-a",
        "company_entity_id": "entity_1",
        "status": status,
        "owner": owner,
        "created_at": "2026-01-01T00:00:00+00:00",
        "updated_at": "2026-01-01T00:00:00+00:00",
        "origin_signal_id": None,
        "blockers": [],
    }


class ResearchCaseStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_put_then_get_round_trips(self) -> None:
        put_case(self.root, "ws-a", _case("rc1"))
        record = get_case(self.root, "ws-a", "rc1")
        self.assertEqual("rc1", record["research_case_id"])

    def test_get_missing_case_raises(self) -> None:
        with self.assertRaises(ResearchCaseNotFound):
            get_case(self.root, "ws-a", "nope")

    def test_workspaces_are_isolated(self) -> None:
        put_case(self.root, "ws-a", _case("rc1"))
        with self.assertRaises(ResearchCaseNotFound):
            get_case(self.root, "ws-b", "rc1")

    def test_put_upserts_by_id(self) -> None:
        put_case(self.root, "ws-a", _case("rc1", status="open"))
        put_case(self.root, "ws-a", _case("rc1", status="in_progress"))
        record = get_case(self.root, "ws-a", "rc1")
        self.assertEqual("in_progress", record["status"])
        page = list_cases(self.root, "ws-a")
        self.assertEqual(1, len(page.items))

    def test_filter_by_status(self) -> None:
        put_case(self.root, "ws-a", _case("rc1", status="open"))
        put_case(self.root, "ws-a", _case("rc2", status="blocked"))
        page = list_cases(self.root, "ws-a", status="blocked")
        self.assertEqual(["rc2"], [c["research_case_id"] for c in page.items])

    def test_filter_by_owner(self) -> None:
        put_case(self.root, "ws-a", _case("rc1", owner="alice"))
        put_case(self.root, "ws-a", _case("rc2", owner="bob"))
        page = list_cases(self.root, "ws-a", owner="bob")
        self.assertEqual(["rc2"], [c["research_case_id"] for c in page.items])

    def test_stable_sort_is_unaffected_by_insertion_order(self) -> None:
        put_case(self.root, "ws-a", _case("rc3"))
        put_case(self.root, "ws-a", _case("rc1"))
        put_case(self.root, "ws-a", _case("rc2"))
        page = list_cases(self.root, "ws-a")
        self.assertEqual(["rc1", "rc2", "rc3"], [c["research_case_id"] for c in page.items])

    def test_pagination_cursor(self) -> None:
        for i in range(5):
            put_case(self.root, "ws-a", _case(f"rc{i}"))
        page = list_cases(self.root, "ws-a", limit=2)
        self.assertEqual(2, len(page.items))
        self.assertIsNotNone(page.next_cursor)
        next_page = list_cases(self.root, "ws-a", limit=2, cursor=page.next_cursor)
        self.assertNotEqual(page.items, next_page.items)


if __name__ == "__main__":
    unittest.main()
