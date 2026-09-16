from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.event_journal import EventJournal
from app.signal_handoff import SignalHandoffError, queue_research


def _signal(**overrides) -> dict:
    base = {
        "signal_id": "sig_1",
        "workspace_id": "ws-a",
        "source": {"kind": "public", "ref": "ref"},
        "observed_at": "2026-06-01T00:00:00+00:00",
        "status": "linked",
        "company_entity_id": "entity_1",
        "dedup_key": "key-1",
        "freshness": {"stale_after_days": 30},
        "provenance": {"source_refs": ["ref"], "epistemic_status": "fact", "evidence_grade": "P1"},
    }
    base.update(overrides)
    return base


class QueueResearchTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_linked_signal_can_be_queued(self) -> None:
        event = queue_research(self.root, _signal(), requested_by="alice@example.com")
        self.assertEqual("ResearchQueued", event["event_type"])
        self.assertEqual("sig_1", event["data"]["signal_id"])
        self.assertEqual("entity_1", event["data"]["company_entity_id"])

    def test_unlinked_signal_is_rejected(self) -> None:
        with self.assertRaises(SignalHandoffError):
            queue_research(self.root, _signal(status="new", company_entity_id=None), requested_by="alice@example.com")

    def test_reviewed_but_not_linked_signal_is_rejected(self) -> None:
        with self.assertRaises(SignalHandoffError):
            queue_research(self.root, _signal(status="reviewed", company_entity_id=None), requested_by="alice@example.com")

    def test_missing_requested_by_is_rejected(self) -> None:
        with self.assertRaises(SignalHandoffError):
            queue_research(self.root, _signal(), requested_by="")

    def test_handoff_is_recorded_in_the_event_journal(self) -> None:
        queue_research(self.root, _signal(), requested_by="alice@example.com")
        journal = EventJournal(self.root)
        events = list(journal.replay())
        self.assertEqual(1, len(events))
        self.assertEqual("ResearchQueued", events[0]["event_type"])

    def test_double_queueing_the_same_signal_is_idempotent(self) -> None:
        first = queue_research(self.root, _signal(), requested_by="alice@example.com")
        second = queue_research(self.root, _signal(), requested_by="bob@example.com")
        self.assertEqual(first["event_id"], second["event_id"])
        journal = EventJournal(self.root)
        self.assertEqual(1, len(list(journal.replay())))


if __name__ == "__main__":
    unittest.main()
