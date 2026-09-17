from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.artifact_archive_store import archive_artifact, list_archived_ids, restore_artifact


class ArtifactArchiveStoreTests(unittest.TestCase):
    def test_archive_then_list(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive_artifact(root, "ws-a", "artifact:signal:s1", actor="alice", archived_at="2026-06-01T00:00:00+00:00")
            self.assertEqual({"artifact:signal:s1"}, list_archived_ids(root, "ws-a"))

    def test_restore_removes_from_archived_set(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive_artifact(root, "ws-a", "artifact:signal:s1", actor="alice", archived_at="2026-06-01T00:00:00+00:00")
            restore_artifact(root, "ws-a", "artifact:signal:s1")
            self.assertEqual(set(), list_archived_ids(root, "ws-a"))

    def test_isolated_per_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive_artifact(root, "ws-a", "artifact:signal:s1", actor="alice", archived_at="2026-06-01T00:00:00+00:00")
            self.assertEqual(set(), list_archived_ids(root, "ws-b"))

    def test_empty_workspace_returns_empty_set(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(set(), list_archived_ids(Path(tmp), "ws-a"))

    def test_restore_of_never_archived_is_a_no_op(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            restore_artifact(root, "ws-a", "artifact:signal:never-archived")
            self.assertEqual(set(), list_archived_ids(root, "ws-a"))


if __name__ == "__main__":
    unittest.main()
