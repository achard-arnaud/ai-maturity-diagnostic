from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.event_journal import EventJournal
from app.research_review import ReviewError, accept_case, mark_stale, reopen_case


def _case(**kwargs) -> dict:
    base = {
        "research_case_id": "rc1",
        "workspace_id": "ws-a",
        "company_entity_id": "entity_1",
        "status": "in_review",
        "owner": "alice",
        "created_at": "2026-01-01T00:00:00+00:00",
        "updated_at": "2026-01-01T00:00:00+00:00",
        "origin_signal_id": None,
        "blockers": [],
    }
    base.update(kwargs)
    return base


def _fact_claim(claim_id: str = "c1") -> dict:
    return {"claim_id": claim_id, "claim_type": "fact", "status": "active"}


class AcceptCaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_accept_requires_reviewer(self) -> None:
        with self.assertRaises(ReviewError):
            accept_case(self.root, _case(), [_fact_claim()], reviewer="", reviewed_at="2026-01-05T00:00:00+00:00")

    def test_accept_requires_reviewer_distinct_from_owner(self) -> None:
        with self.assertRaises(ReviewError):
            accept_case(
                self.root, _case(owner="alice"), [_fact_claim()],
                reviewer="alice", reviewed_at="2026-01-05T00:00:00+00:00",
            )

    def test_accept_requires_completeness(self) -> None:
        with self.assertRaises(ReviewError):
            accept_case(self.root, _case(), [], reviewer="bob", reviewed_at="2026-01-05T00:00:00+00:00")

    def test_accept_requires_no_open_blockers(self) -> None:
        blocked = _case(blockers=[{"reason": "waiting", "opened_at": "2026-01-02T00:00:00+00:00", "resolved_at": None}])
        with self.assertRaises(ReviewError):
            accept_case(self.root, blocked, [_fact_claim()], reviewer="bob", reviewed_at="2026-01-05T00:00:00+00:00")

    def test_accept_requires_in_review_status(self) -> None:
        with self.assertRaises(ReviewError):
            accept_case(self.root, _case(status="open"), [_fact_claim()], reviewer="bob", reviewed_at="2026-01-05T00:00:00+00:00")

    def test_accept_succeeds_and_updates_status(self) -> None:
        accepted = accept_case(self.root, _case(), [_fact_claim()], reviewer="bob", reviewed_at="2026-01-05T00:00:00+00:00")
        self.assertEqual("accepted", accepted["status"])

    def test_accept_writes_audit_event(self) -> None:
        accept_case(self.root, _case(), [_fact_claim()], reviewer="bob", reviewed_at="2026-01-05T00:00:00+00:00")
        journal = EventJournal(self.root)
        events = list(journal.replay())
        self.assertTrue(any(e["event_type"] == "ResearchCaseAccepted" for e in events))
        event = next(e for e in events if e["event_type"] == "ResearchCaseAccepted")
        self.assertEqual("bob", event["actor_id"])


class ReopenCaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_reopen_requires_reason(self) -> None:
        with self.assertRaises(ReviewError):
            reopen_case(self.root, _case(status="stale"), reason="", reopened_by="bob", reopened_at="2026-01-05T00:00:00+00:00")

    def test_reopen_requires_actor(self) -> None:
        with self.assertRaises(ReviewError):
            reopen_case(self.root, _case(status="stale"), reason="new info", reopened_by="", reopened_at="2026-01-05T00:00:00+00:00")

    def test_reopen_from_stale_succeeds(self) -> None:
        reopened = reopen_case(self.root, _case(status="stale"), reason="new info", reopened_by="bob", reopened_at="2026-01-05T00:00:00+00:00")
        self.assertEqual("reopened", reopened["status"])

    def test_reopen_directly_from_accepted_rejected(self) -> None:
        # accepted must go through stale first -- 02_DOMAIN_AND_TRUTH_MODEL's
        # "invalidated or marked stale when a referenced input changes".
        with self.assertRaises(ReviewError):
            reopen_case(self.root, _case(status="accepted"), reason="new info", reopened_by="bob", reopened_at="2026-01-05T00:00:00+00:00")

    def test_reopen_writes_audit_event_with_reason(self) -> None:
        reopen_case(self.root, _case(status="stale"), reason="client merged", reopened_by="bob", reopened_at="2026-01-05T00:00:00+00:00")
        journal = EventJournal(self.root)
        events = list(journal.replay())
        event = next(e for e in events if e["event_type"] == "ResearchCaseReopened")
        self.assertEqual("client merged", event["data"]["reason"])


class MarkStaleTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_mark_stale_requires_reason(self) -> None:
        with self.assertRaises(ReviewError):
            mark_stale(self.root, _case(status="accepted"), stale_reason="", marked_by="bob", marked_at="2026-01-05T00:00:00+00:00")

    def test_mark_stale_from_accepted_succeeds(self) -> None:
        staled = mark_stale(self.root, _case(status="accepted"), stale_reason="input changed", marked_by="bob", marked_at="2026-01-05T00:00:00+00:00")
        self.assertEqual("stale", staled["status"])

    def test_mark_stale_from_open_rejected(self) -> None:
        with self.assertRaises(ReviewError):
            mark_stale(self.root, _case(status="open"), stale_reason="input changed", marked_by="bob", marked_at="2026-01-05T00:00:00+00:00")


if __name__ == "__main__":
    unittest.main()
