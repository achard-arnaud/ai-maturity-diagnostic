"""Research review/accept/reopen/stale lifecycle (Epic 04 S06).

Every state-changing action here is an explicit, role-checked, audited
step -- it appends an event to Epic 01's EventJournal (the same
"handoff/decision is an explicit event" pattern as Epic 03's
signal_handoff.queue_research) and never silently flips a case's status
as a side effect of something else.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

from app.event_journal import EventJournal
from app.research_policy import can_transition_case, compute_completeness
from app.research_queue import count_open_blockers


class ReviewError(RuntimeError):
    pass


def accept_case(
    root: Path,
    case: dict[str, Any],
    claims: Sequence[dict[str, Any]],
    *,
    reviewer: str,
    reviewed_at: str,
) -> dict[str, Any]:
    """Explicitly accept a case: requires status in_review, a reviewer
    distinct from the case's own owner (separation of duties -- the person
    who did the research does not also sign off on it), gate-1
    completeness (at least one active fact claim), and zero open
    blockers. Appends a ResearchCaseAccepted audit event.
    """
    if not reviewer.strip():
        raise ReviewError("reviewer is required -- no anonymous review")
    if case.get("owner") and reviewer == case["owner"]:
        raise ReviewError("reviewer must be distinct from the case owner")

    open_blockers = count_open_blockers(case)
    if not can_transition_case(case["status"], "accepted", open_blockers=open_blockers):
        raise ReviewError(
            f"cannot accept case {case['research_case_id']} from status "
            f"{case['status']!r} with {open_blockers} open blocker(s)"
        )

    completeness = compute_completeness(claims)
    if not completeness.is_complete:
        raise ReviewError(f"case is not complete: {', '.join(completeness.missing)}")

    updated = dict(case)
    updated["status"] = "accepted"
    updated["updated_at"] = reviewed_at

    journal = EventJournal(root)
    journal.append(
        "ResearchCaseAccepted",
        workspace_id=case["workspace_id"],
        actor_id=reviewer,
        object_ref=f"research_case:{case['research_case_id']}",
        data={"research_case_id": case["research_case_id"], "reviewer": reviewer},
        idempotency_key=f"research-case-accepted:{case['research_case_id']}",
    )
    return updated


def reopen_case(
    root: Path,
    case: dict[str, Any],
    *,
    reason: str,
    reopened_by: str,
    reopened_at: str,
) -> dict[str, Any]:
    """Reopen an accepted or stale case. Always requires an explicit
    reason and actor -- appends a ResearchCaseReopened audit event."""
    if not reason.strip():
        raise ReviewError("reopening a case requires a reason")
    if not reopened_by.strip():
        raise ReviewError("reopened_by is required -- no anonymous reopen")
    if not can_transition_case(case["status"], "reopened", open_blockers=0):
        raise ReviewError(f"cannot reopen case {case['research_case_id']} from status {case['status']!r}")

    updated = dict(case)
    updated["status"] = "reopened"
    updated["updated_at"] = reopened_at

    journal = EventJournal(root)
    journal.append(
        "ResearchCaseReopened",
        workspace_id=case["workspace_id"],
        actor_id=reopened_by,
        object_ref=f"research_case:{case['research_case_id']}",
        data={"research_case_id": case["research_case_id"], "reason": reason},
    )
    return updated


def mark_stale(
    root: Path,
    case: dict[str, Any],
    *,
    stale_reason: str,
    marked_by: str,
    marked_at: str,
) -> dict[str, Any]:
    """Mark an accepted case stale (an input it was built on has since
    changed -- 02_DOMAIN_AND_TRUTH_MODEL.md: 'a fit is invalidated or
    marked stale when a referenced input changes', generalized here to
    ResearchCase). Requires an explicit reason and actor; appends a
    ResearchCaseMarkedStale audit event."""
    if not stale_reason.strip():
        raise ReviewError("marking a case stale requires a reason")
    if not marked_by.strip():
        raise ReviewError("marked_by is required -- no anonymous staleness marking")
    if not can_transition_case(case["status"], "stale", open_blockers=0):
        raise ReviewError(f"cannot mark case {case['research_case_id']} stale from status {case['status']!r}")

    updated = dict(case)
    updated["status"] = "stale"
    updated["updated_at"] = marked_at

    journal = EventJournal(root)
    journal.append(
        "ResearchCaseMarkedStale",
        workspace_id=case["workspace_id"],
        actor_id=marked_by,
        object_ref=f"research_case:{case['research_case_id']}",
        data={"research_case_id": case["research_case_id"], "reason": stale_reason},
    )
    return updated
