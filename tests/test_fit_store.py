from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.fit_store import (
    FitAlreadyExists,
    FitConflict,
    FitNotFound,
    create_fit,
    get_fit,
    list_fits,
    update_fit,
)


def _assessment(fit_assessment_id: str, *, status: str = "draft", demand_id: str = "d1") -> dict:
    return {
        "fit_assessment_id": fit_assessment_id,
        "workspace_id": "ws-a",
        "input_lock": {"demand_id": demand_id, "demand_version": 1, "product_snapshot_id": "snap1", "input_hash": "h1"},
        "status": status,
        "gates": [],
        "coverage": None,
        "gaps": [],
        "alternatives": [],
        "counter_evidence": [],
        "score": None,
        "verdict": None,
        "created_at": "2026-01-01T00:00:00+00:00",
        "updated_at": None,
    }


class FitStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_create_then_get_round_trips_at_version_1(self) -> None:
        create_fit(self.root, "ws-a", _assessment("fa1"))
        record, version = get_fit(self.root, "ws-a", "fa1")
        self.assertEqual("fa1", record["fit_assessment_id"])
        self.assertEqual(1, version)

    def test_create_existing_id_is_refused(self) -> None:
        create_fit(self.root, "ws-a", _assessment("fa1"))
        with self.assertRaises(FitAlreadyExists):
            create_fit(self.root, "ws-a", _assessment("fa1"))

    def test_get_missing_raises(self) -> None:
        with self.assertRaises(FitNotFound):
            get_fit(self.root, "ws-a", "nope")

    def test_workspaces_are_isolated(self) -> None:
        create_fit(self.root, "ws-a", _assessment("fa1"))
        with self.assertRaises(FitNotFound):
            get_fit(self.root, "ws-b", "fa1")

    def test_update_with_correct_version_bumps_version(self) -> None:
        create_fit(self.root, "ws-a", _assessment("fa1"))
        updated, version = update_fit(self.root, "ws-a", "fa1", lambda d: {**d, "status": "in_review"}, expected_version=1)
        self.assertEqual("in_review", updated["status"])
        self.assertEqual(2, version)

    def test_update_with_stale_version_conflicts(self) -> None:
        create_fit(self.root, "ws-a", _assessment("fa1"))
        update_fit(self.root, "ws-a", "fa1", lambda d: {**d, "status": "in_review"}, expected_version=1)
        with self.assertRaises(FitConflict):
            update_fit(self.root, "ws-a", "fa1", lambda d: {**d, "status": "decided"}, expected_version=1)

    def test_filter_by_status(self) -> None:
        create_fit(self.root, "ws-a", _assessment("fa1", status="draft"))
        create_fit(self.root, "ws-a", _assessment("fa2", status="decided"))
        page = list_fits(self.root, "ws-a", status="decided")
        self.assertEqual(["fa2"], [f["fit_assessment_id"] for f in page.items])

    def test_filter_by_demand_id(self) -> None:
        create_fit(self.root, "ws-a", _assessment("fa1", demand_id="d1"))
        create_fit(self.root, "ws-a", _assessment("fa2", demand_id="d2"))
        page = list_fits(self.root, "ws-a", demand_id="d2")
        self.assertEqual(["fa2"], [f["fit_assessment_id"] for f in page.items])


if __name__ == "__main__":
    unittest.main()
