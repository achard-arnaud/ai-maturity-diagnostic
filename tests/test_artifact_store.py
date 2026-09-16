import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from app.artifact_store import ArtifactPathError, ArtifactStore, ArtifactVersionConflict


class ArtifactStoreTests(unittest.TestCase):
    def test_atomic_write_and_optimistic_version(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = ArtifactStore(Path(tmp))
            first = store.write_text("items/a.txt", "one")
            second = store.write_text("items/a.txt", "two", expected_version=first.version)
            self.assertEqual((Path(tmp) / "items/a.txt").read_text(), "two")
            self.assertEqual(second.previous_version, first.version)
            with self.assertRaises(ArtifactVersionConflict):
                store.write_text("items/a.txt", "stale", expected_version=first.version)

    def test_replace_failure_keeps_previous_content(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = ArtifactStore(Path(tmp))
            target = Path(tmp) / "a.txt"
            store.write_text(target, "safe")
            with patch("app.artifact_store.os.replace", side_effect=OSError("crash")):
                with self.assertRaises(OSError):
                    store.write_text(target, "partial")
            self.assertEqual(target.read_text(), "safe")
            self.assertEqual(list(target.parent.glob(".a.txt.*.tmp")), [])

    def test_concurrent_jsonl_appends_do_not_lose_records(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = ArtifactStore(Path(tmp), lock_timeout_seconds=2)
            threads = [threading.Thread(target=store.append_jsonl, args=("events.jsonl", {"i": i})) for i in range(20)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
            lines = (Path(tmp) / "events.jsonl").read_text().splitlines()
            self.assertEqual(len(lines), 20)

    def test_rejects_escape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = ArtifactStore(Path(tmp))
            with self.assertRaises(ArtifactPathError):
                store.write_text(Path(tmp).parent / "escape.txt", "no")


if __name__ == "__main__":
    unittest.main()
