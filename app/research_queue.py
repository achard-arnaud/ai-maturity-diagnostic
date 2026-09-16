"""Epic 04 S02: ResearchCase queue -- ownership, SLA, blockers, resume.

Pure functions over the CanonicalResearchCaseV1 dict shape (contracts/
research_case_v1.schema.yaml). No storage here -- see
app/research_case_store.py for the persistence layer built on top.
"""

from __future__ import annotations

from datetime import datetime, timedelta

DEFAULT_SLA_DAYS = 5


class OwnershipError(Exception):
    pass


class TransitionError(Exception):
    pass


def _parse(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def claim_ownership(case: dict, owner: str) -> dict:
    """Assign an owner to an unowned case, or confirm the current owner.

    Idempotent: claiming with the same owner twice is a no-op (returns an
    equal dict). Claiming an already-owned case with a *different* owner
    raises -- ownership must be explicitly released first.
    """
    current_owner = case.get("owner")
    if current_owner is not None and current_owner != owner:
        raise OwnershipError(f"case already owned by {current_owner!r}")
    if current_owner == owner:
        return dict(case)
    updated = dict(case)
    updated["owner"] = owner
    return updated


def release_ownership(case: dict) -> dict:
    updated = dict(case)
    updated["owner"] = None
    return updated


def sla_deadline(case: dict, *, sla_days: int = DEFAULT_SLA_DAYS) -> datetime:
    opened_at = _parse(case["created_at"])
    return opened_at + timedelta(days=sla_days)


def is_sla_breached(case: dict, *, now: datetime, sla_days: int = DEFAULT_SLA_DAYS) -> bool:
    if case["status"] in ("accepted", "stale"):
        return False
    return now > sla_deadline(case, sla_days=sla_days)


def add_blocker(case: dict, reason: str, *, opened_at: str) -> dict:
    updated = dict(case)
    blockers = list(case.get("blockers", []))
    blockers.append({"reason": reason, "opened_at": opened_at, "resolved_at": None})
    updated["blockers"] = blockers
    updated["status"] = "blocked"
    return updated


def resolve_blocker(case: dict, reason: str, *, resolved_at: str) -> dict:
    """Resolve the first open blocker matching reason. Idempotent: resolving
    an already-resolved (or absent) blocker leaves the case unchanged."""
    blockers = list(case.get("blockers", []))
    changed = False
    new_blockers = []
    for blocker in blockers:
        if not changed and blocker["reason"] == reason and blocker["resolved_at"] is None:
            blocker = dict(blocker)
            blocker["resolved_at"] = resolved_at
            changed = True
        new_blockers.append(blocker)
    updated = dict(case)
    updated["blockers"] = new_blockers
    return updated


def count_open_blockers(case: dict) -> int:
    return sum(1 for b in case.get("blockers", []) if b.get("resolved_at") is None)


def resume_case(case: dict, *, updated_at: str) -> dict:
    """Move a blocked case back to in_progress, once no blocker is open.

    Raises TransitionError if any blocker is still open, or the case isn't
    currently blocked.
    """
    if case["status"] != "blocked":
        raise TransitionError(f"cannot resume a case with status {case['status']!r}")
    if count_open_blockers(case) > 0:
        raise TransitionError("cannot resume a case with an open blocker")
    updated = dict(case)
    updated["status"] = "in_progress"
    updated["updated_at"] = updated_at
    return updated
