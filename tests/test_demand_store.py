from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.demand_store import (
    DemandAlreadyExists,
    DemandConflict,
    DemandNotFound,
    create_demand,
    get_demand,
    list_demands,
    update_demand,
)
from app.demand_policy import known, unknown


def _demand(demand_id: str, *, status: str = "observed", company_entity_id: str = "entity_1") -> dict:
    return {
        "demand_id": demand_id,
        "workspace_id": "ws-a",
        "company_entity_id": company_entity_id,
        "status": status,
        "problem": known("manual onboarding"),
        "population": unknown(),
        "impact": unknown(),
        "urgency": unknown(),
        "initiative": unknown(),
        "sponsor": unknown(),
        "budget": unknown(),
        "timing": unknown(),
        "claim_ids": [],
        "origin_profile_ref": None,
        "created_at": "2026-01-01T00:00:00+00:00",
        "updated_at": "2026-01-01T00:00:00+00:00",
    }


class DemandStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_create_then_get_round_trips_at_version_1(self) -> None:
        create_demand(self.root, "ws-a", _demand("d1"))
        demand, version = get_demand(self.root, "ws-a", "d1")
        self.assertEqual("d1", demand["demand_id"])
        self.assertEqual(1, version)

    def test_create_existing_id_is_refused(self) -> None:
        create_demand(self.root, "ws-a", _demand("d1"))
        with self.assertRaises(DemandAlreadyExists):
            create_demand(self.root, "ws-a", _demand("d1"))

    def test_get_missing_demand_raises(self) -> None:
        with self.assertRaises(DemandNotFound):
            get_demand(self.root, "ws-a", "nope")

    def test_workspaces_are_isolated(self) -> None:
        create_demand(self.root, "ws-a", _demand("d1"))
        with self.assertRaises(DemandNotFound):
            get_demand(self.root, "ws-b", "d1")

    def test_update_with_correct_version_succeeds_and_bumps_version(self) -> None:
        create_demand(self.root, "ws-a", _demand("d1"))
        updated, new_version = update_demand(
            self.root, "ws-a", "d1", lambda d: {**d, "status": "qualifying"}, expected_version=1,
        )
        self.assertEqual("qualifying", updated["status"])
        self.assertEqual(2, new_version)

    def test_update_with_stale_version_is_refused(self) -> None:
        create_demand(self.root, "ws-a", _demand("d1"))
        update_demand(self.root, "ws-a", "d1", lambda d: {**d, "status": "qualifying"}, expected_version=1)
        with self.assertRaises(DemandConflict):
            update_demand(self.root, "ws-a", "d1", lambda d: {**d, "status": "rejected"}, expected_version=1)

    def test_update_missing_demand_raises(self) -> None:
        with self.assertRaises(DemandNotFound):
            update_demand(self.root, "ws-a", "nope", lambda d: d, expected_version=1)

    def test_concurrent_edits_second_one_conflicts(self) -> None:
        create_demand(self.root, "ws-a", _demand("d1"))
        _demand_v1, version = get_demand(self.root, "ws-a", "d1")
        update_demand(self.root, "ws-a", "d1", lambda d: {**d, "status": "qualifying"}, expected_version=version)
        with self.assertRaises(DemandConflict):
            update_demand(self.root, "ws-a", "d1", lambda d: {**d, "status": "rejected"}, expected_version=version)

    def test_filter_by_status(self) -> None:
        create_demand(self.root, "ws-a", _demand("d1", status="observed"))
        create_demand(self.root, "ws-a", _demand("d2", status="qualified"))
        page = list_demands(self.root, "ws-a", status="qualified")
        self.assertEqual(["d2"], [d["demand_id"] for d in page.items])

    def test_filter_by_company(self) -> None:
        create_demand(self.root, "ws-a", _demand("d1", company_entity_id="entity_1"))
        create_demand(self.root, "ws-a", _demand("d2", company_entity_id="entity_2"))
        page = list_demands(self.root, "ws-a", company_entity_id="entity_2")
        self.assertEqual(["d2"], [d["demand_id"] for d in page.items])

    def test_pagination_cursor(self) -> None:
        for i in range(5):
            create_demand(self.root, "ws-a", _demand(f"d{i}"))
        page = list_demands(self.root, "ws-a", limit=2)
        self.assertEqual(2, len(page.items))
        self.assertIsNotNone(page.next_cursor)
        next_page = list_demands(self.root, "ws-a", limit=2, cursor=page.next_cursor)
        self.assertNotEqual(page.items, next_page.items)


if __name__ == "__main__":
    unittest.main()
