from __future__ import annotations

import unittest
from datetime import datetime, timezone

from app.research_queue import (
    OwnershipError,
    TransitionError,
    add_blocker,
    claim_ownership,
    count_open_blockers,
    is_sla_breached,
    release_ownership,
    resolve_blocker,
    resume_case,
    sla_deadline,
)


def _case(**kwargs) -> dict:
    base = {
        "research_case_id": "rc1",
        "workspace_id": "ws-a",
        "company_entity_id": "entity_1",
        "status": "open",
        "owner": None,
        "created_at": "2026-01-01T00:00:00+00:00",
        "updated_at": "2026-01-01T00:00:00+00:00",
        "origin_signal_id": None,
        "blockers": [],
    }
    base.update(kwargs)
    return base


class OwnershipTests(unittest.TestCase):
    def test_claim_unowned_case(self) -> None:
        updated = claim_ownership(_case(), "alice")
        self.assertEqual("alice", updated["owner"])

    def test_claim_is_idempotent_for_same_owner(self) -> None:
        owned = claim_ownership(_case(), "alice")
        reclaimed = claim_ownership(owned, "alice")
        self.assertEqual(owned, reclaimed)

    def test_claim_by_different_owner_raises(self) -> None:
        owned = claim_ownership(_case(), "alice")
        with self.assertRaises(OwnershipError):
            claim_ownership(owned, "bob")

    def test_release_then_reclaim_by_new_owner(self) -> None:
        owned = claim_ownership(_case(), "alice")
        released = release_ownership(owned)
        reclaimed = claim_ownership(released, "bob")
        self.assertEqual("bob", reclaimed["owner"])


class SLATests(unittest.TestCase):
    def test_sla_deadline_is_created_at_plus_default_days(self) -> None:
        case = _case(created_at="2026-01-01T00:00:00+00:00")
        deadline = sla_deadline(case)
        self.assertEqual(datetime(2026, 1, 6, tzinfo=timezone.utc), deadline)

    def test_not_breached_before_deadline(self) -> None:
        case = _case(created_at="2026-01-01T00:00:00+00:00")
        now = datetime(2026, 1, 3, tzinfo=timezone.utc)
        self.assertFalse(is_sla_breached(case, now=now))

    def test_breached_after_deadline(self) -> None:
        case = _case(created_at="2026-01-01T00:00:00+00:00")
        now = datetime(2026, 1, 10, tzinfo=timezone.utc)
        self.assertTrue(is_sla_breached(case, now=now))

    def test_accepted_case_never_breaches(self) -> None:
        case = _case(created_at="2026-01-01T00:00:00+00:00", status="accepted")
        now = datetime(2026, 6, 1, tzinfo=timezone.utc)
        self.assertFalse(is_sla_breached(case, now=now))


class BlockerAndResumeTests(unittest.TestCase):
    def test_add_blocker_sets_status_blocked(self) -> None:
        blocked = add_blocker(_case(status="in_progress"), "waiting on data", opened_at="2026-01-02T00:00:00+00:00")
        self.assertEqual("blocked", blocked["status"])
        self.assertEqual(1, count_open_blockers(blocked))

    def test_resolve_blocker_closes_it(self) -> None:
        blocked = add_blocker(_case(status="in_progress"), "waiting on data", opened_at="2026-01-02T00:00:00+00:00")
        resolved = resolve_blocker(blocked, "waiting on data", resolved_at="2026-01-03T00:00:00+00:00")
        self.assertEqual(0, count_open_blockers(resolved))

    def test_resolve_blocker_is_idempotent(self) -> None:
        blocked = add_blocker(_case(status="in_progress"), "waiting on data", opened_at="2026-01-02T00:00:00+00:00")
        resolved_once = resolve_blocker(blocked, "waiting on data", resolved_at="2026-01-03T00:00:00+00:00")
        resolved_twice = resolve_blocker(resolved_once, "waiting on data", resolved_at="2026-01-04T00:00:00+00:00")
        self.assertEqual(resolved_once, resolved_twice)

    def test_resume_requires_blocked_status(self) -> None:
        with self.assertRaises(TransitionError):
            resume_case(_case(status="open"), updated_at="2026-01-05T00:00:00+00:00")

    def test_resume_requires_no_open_blockers(self) -> None:
        blocked = add_blocker(_case(status="in_progress"), "waiting", opened_at="2026-01-02T00:00:00+00:00")
        with self.assertRaises(TransitionError):
            resume_case(blocked, updated_at="2026-01-05T00:00:00+00:00")

    def test_resume_succeeds_once_blocker_resolved(self) -> None:
        blocked = add_blocker(_case(status="in_progress"), "waiting", opened_at="2026-01-02T00:00:00+00:00")
        resolved = resolve_blocker(blocked, "waiting", resolved_at="2026-01-03T00:00:00+00:00")
        resumed = resume_case(resolved, updated_at="2026-01-04T00:00:00+00:00")
        self.assertEqual("in_progress", resumed["status"])


if __name__ == "__main__":
    unittest.main()
