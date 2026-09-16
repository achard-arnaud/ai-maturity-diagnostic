from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.signal_store import SignalNotFound, get_signal, list_signals, put_signal


def _signal(signal_id: str, *, status: str = "new", source_kind: str = "public") -> dict:
    return {
        "signal_id": signal_id,
        "workspace_id": "ws-a",
        "source": {"kind": source_kind, "ref": "ref"},
        "observed_at": "2026-06-01T00:00:00+00:00",
        "status": status,
        "company_entity_id": None,
        "dedup_key": f"key-{signal_id}",
        "freshness": {"stale_after_days": 30},
        "provenance": {"source_refs": ["ref"], "epistemic_status": "fact", "evidence_grade": "P1"},
    }


class SignalStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_put_then_get_round_trips(self) -> None:
        put_signal(self.root, "ws-a", _signal("s1"))
        record = get_signal(self.root, "ws-a", "s1")
        self.assertEqual("s1", record["signal_id"])

    def test_get_missing_signal_raises(self) -> None:
        with self.assertRaises(SignalNotFound):
            get_signal(self.root, "ws-a", "nope")

    def test_workspaces_are_isolated(self) -> None:
        put_signal(self.root, "ws-a", _signal("s1"))
        with self.assertRaises(SignalNotFound):
            get_signal(self.root, "ws-b", "s1")

    def test_filter_by_status(self) -> None:
        put_signal(self.root, "ws-a", _signal("s1", status="new"))
        put_signal(self.root, "ws-a", _signal("s2", status="reviewed"))
        page = list_signals(self.root, "ws-a", status="new")
        self.assertEqual(["s1"], [s["signal_id"] for s in page.items])

    def test_filter_by_source_kind(self) -> None:
        put_signal(self.root, "ws-a", _signal("s1", source_kind="public"))
        put_signal(self.root, "ws-a", _signal("s2", source_kind="manual"))
        page = list_signals(self.root, "ws-a", source_kind="manual")
        self.assertEqual(["s2"], [s["signal_id"] for s in page.items])

    def test_stable_sort_is_unaffected_by_insertion_order(self) -> None:
        put_signal(self.root, "ws-a", _signal("s3"))
        put_signal(self.root, "ws-a", _signal("s1"))
        put_signal(self.root, "ws-a", _signal("s2"))
        page = list_signals(self.root, "ws-a")
        self.assertEqual(["s1", "s2", "s3"], [s["signal_id"] for s in page.items])

    def test_pagination_cursor(self) -> None:
        for i in range(5):
            put_signal(self.root, "ws-a", _signal(f"s{i}"))
        page = list_signals(self.root, "ws-a", limit=2)
        self.assertEqual(2, len(page.items))
        self.assertIsNotNone(page.next_cursor)
        next_page = list_signals(self.root, "ws-a", limit=2, cursor=page.next_cursor)
        self.assertNotEqual(page.items, next_page.items)


if __name__ == "__main__":
    unittest.main()
