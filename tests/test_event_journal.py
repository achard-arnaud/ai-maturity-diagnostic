import json
import tempfile
import threading
import unittest
from pathlib import Path

from app.event_journal import EventJournal, EventJournalIntegrityError
from app.execution_context import correlation_scope


class EventJournalTests(unittest.TestCase):
    def test_append_replay_chain_and_correlation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            journal = EventJournal(Path(tmp))
            with correlation_scope("corr-1"):
                first = journal.append("artifact.written", workspace_id="ws", actor_id="user", object_ref="a")
                second = journal.append("artifact.written", workspace_id="ws", actor_id="user", object_ref="b")
            events = list(journal.replay())
            self.assertEqual([row["event_id"] for row in events], [first["event_id"], second["event_id"]])
            self.assertEqual(first["correlation_id"], "corr-1")
            self.assertEqual(second["previous_hash"], first["event_hash"])

    def test_idempotency_returns_existing_event(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            journal = EventJournal(Path(tmp))
            first = journal.append(
                "run.started", workspace_id="ws", actor_id="user", idempotency_key="same"
            )
            second = journal.append(
                "run.started", workspace_id="ws", actor_id="user", idempotency_key="same"
            )
            self.assertEqual(first, second)
            self.assertEqual(len(list(journal.replay())), 1)

    def test_replay_detects_tampering(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            journal = EventJournal(Path(tmp))
            journal.append("run.started", workspace_id="ws", actor_id="user")
            row = json.loads(journal.path.read_text().strip())
            row["data"] = {"tampered": True}
            journal.path.write_text(json.dumps(row) + "\n")
            with self.assertRaises(EventJournalIntegrityError):
                list(journal.replay())

    def test_concurrent_appends_keep_a_valid_chain(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            journal = EventJournal(Path(tmp))
            threads = [
                threading.Thread(
                    target=journal.append,
                    args=("run.progress",),
                    kwargs={"workspace_id": "ws", "actor_id": "worker", "data": {"i": i}},
                )
                for i in range(20)
            ]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
            self.assertEqual(len(list(journal.replay())), 20)


if __name__ == "__main__":
    unittest.main()
