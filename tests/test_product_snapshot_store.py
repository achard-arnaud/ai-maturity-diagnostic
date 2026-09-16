from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.product_policy import SnapshotImmutabilityError, compute_content_hash
from app.product_snapshot_store import (
    ProductSnapshotNotFound,
    get_latest_snapshot,
    get_snapshot,
    is_snapshot_stale,
    put_snapshot,
)


def _snapshot(snapshot_id: str, product_id: str, *, description: str = "Core", published_at: str = "2026-01-01T00:00:00+00:00") -> dict:
    content = {"name": "Acme", "description": description, "exclusions": [], "hard_gates": []}
    return {
        "snapshot_id": snapshot_id,
        "product_id": product_id,
        "product_version_id": f"{snapshot_id}-v",
        "owner_scope": {"kind": "shared", "workspace_id": None},
        "content": content,
        "content_hash": compute_content_hash(content),
        "published_at": published_at,
        "evidence_ids": [],
        "supersedes_snapshot_id": None,
    }


class SnapshotStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_put_then_get_round_trips(self) -> None:
        put_snapshot(self.root, _snapshot("snap1", "p1"))
        record = get_snapshot(self.root, "snap1")
        self.assertEqual("snap1", record["snapshot_id"])

    def test_get_missing_snapshot_raises(self) -> None:
        with self.assertRaises(ProductSnapshotNotFound):
            get_snapshot(self.root, "nope")

    def test_reput_identical_content_is_a_noop(self) -> None:
        snap = _snapshot("snap1", "p1")
        put_snapshot(self.root, snap)
        put_snapshot(self.root, snap)  # should not raise
        record = get_snapshot(self.root, "snap1")
        self.assertEqual(snap["content_hash"], record["content_hash"])

    def test_reput_with_different_content_is_rejected(self) -> None:
        put_snapshot(self.root, _snapshot("snap1", "p1", description="Core"))
        with self.assertRaises(SnapshotImmutabilityError):
            put_snapshot(self.root, _snapshot("snap1", "p1", description="Mutated!"))

    def test_fetching_same_snapshot_repeatedly_is_reproducible(self) -> None:
        put_snapshot(self.root, _snapshot("snap1", "p1"))
        first = get_snapshot(self.root, "snap1")
        second = get_snapshot(self.root, "snap1")
        third = get_snapshot(self.root, "snap1")
        self.assertEqual(first["content_hash"], second["content_hash"])
        self.assertEqual(second["content_hash"], third["content_hash"])
        self.assertEqual(compute_content_hash(first["content"]), first["content_hash"])


class StalenessPropagationTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_only_snapshot_is_not_stale(self) -> None:
        put_snapshot(self.root, _snapshot("snap1", "p1", published_at="2026-01-01T00:00:00+00:00"))
        self.assertFalse(is_snapshot_stale(self.root, "snap1"))

    def test_latest_snapshot_is_returned(self) -> None:
        put_snapshot(self.root, _snapshot("snap1", "p1", published_at="2026-01-01T00:00:00+00:00"))
        put_snapshot(self.root, _snapshot("snap2", "p1", description="v2", published_at="2026-02-01T00:00:00+00:00"))
        latest = get_latest_snapshot(self.root, "p1")
        self.assertEqual("snap2", latest["snapshot_id"])

    def test_older_snapshot_becomes_stale_once_superseded(self) -> None:
        put_snapshot(self.root, _snapshot("snap1", "p1", published_at="2026-01-01T00:00:00+00:00"))
        self.assertFalse(is_snapshot_stale(self.root, "snap1"))
        put_snapshot(self.root, _snapshot("snap2", "p1", description="v2", published_at="2026-02-01T00:00:00+00:00"))
        self.assertTrue(is_snapshot_stale(self.root, "snap1"))
        self.assertFalse(is_snapshot_stale(self.root, "snap2"))

    def test_staleness_is_scoped_per_product(self) -> None:
        put_snapshot(self.root, _snapshot("snap1", "p1", published_at="2026-01-01T00:00:00+00:00"))
        put_snapshot(self.root, _snapshot("snap-other", "p2", published_at="2026-03-01T00:00:00+00:00"))
        # A newer snapshot for a *different* product never makes p1's
        # own current snapshot stale.
        self.assertFalse(is_snapshot_stale(self.root, "snap1"))

    def test_stale_snapshot_content_is_still_intact_and_reproducible(self) -> None:
        put_snapshot(self.root, _snapshot("snap1", "p1", description="v1", published_at="2026-01-01T00:00:00+00:00"))
        put_snapshot(self.root, _snapshot("snap2", "p1", description="v2", published_at="2026-02-01T00:00:00+00:00"))
        stale = get_snapshot(self.root, "snap1")
        self.assertEqual("v1", stale["content"]["description"])
        self.assertEqual(compute_content_hash(stale["content"]), stale["content_hash"])


if __name__ == "__main__":
    unittest.main()
