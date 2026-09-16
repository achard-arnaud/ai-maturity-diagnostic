"""Epic 07 S04: review/decision/override/stale lifecycle.

Stop condition: "override borné" (bounded override) -- a human may
override the computed score's own recommendation (PURSUE despite a
below-threshold score), but never the hard-gate/blocker check itself,
and never without a reason and a mandatory expiry (an override is a
temporary human judgment call, not a permanent bypass -- it must be
re-reviewed by its expiry).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

from app.event_journal import EventJournal
from app.fit_gates import GateResult, can_compute_score

DECIDE_ROLE = "fit_reviewer"
PURSUE_SCORE_THRESHOLD = 0.5
VERDICTS = ("PURSUE", "REJECT", "HOLD")

_TRANSITIONS: dict[str, set[str]] = {
    "draft": {"in_review"},
    "in_review": {"decided"},
    "decided": {"stale"},
    "stale": {"in_review"},
}


class FitLifecycleError(Exception):
    pass


class FitAuthorizationError(FitLifecycleError):
    pass


def can_transition_fit(current_status: str, next_status: str) -> bool:
    return next_status in _TRANSITIONS.get(current_status, set())


def submit_for_review(assessment: dict[str, Any]) -> dict[str, Any]:
    if not can_transition_fit(assessment["status"], "in_review"):
        raise FitLifecycleError(f"cannot submit fit {assessment['fit_assessment_id']} for review from status {assessment['status']!r}")
    updated = dict(assessment)
    updated["status"] = "in_review"
    return updated


def decide_fit(
    root: Path,
    assessment: dict[str, Any],
    *,
    verdict: str,
    gates: Sequence[GateResult],
    open_blocker_count: int,
    score_value: float,
    decided_by: str,
    actor_role: str | None,
    decided_at: str,
    override_reason: str | None = None,
    override_expiry: str | None = None,
) -> dict[str, Any]:
    if actor_role != DECIDE_ROLE:
        raise FitAuthorizationError(f"deciding a fit requires the {DECIDE_ROLE!r} role; got {actor_role!r}")
    if not can_transition_fit(assessment["status"], "decided"):
        raise FitLifecycleError(f"cannot decide fit {assessment['fit_assessment_id']} from status {assessment['status']!r}")
    if verdict not in VERDICTS:
        raise FitLifecycleError(f"unknown verdict {verdict!r}; must be one of {VERDICTS}")

    is_override = False
    if verdict == "PURSUE":
        # Absolutely non-negotiable: no override parameter can make this
        # true when gates/blockers are unresolved.
        if not can_compute_score(gates, open_blocker_count=open_blocker_count):
            raise FitLifecycleError(
                "cannot verdict PURSUE while hard gates have failed or blockers are open -- "
                "this can never be overridden"
            )
        if score_value < PURSUE_SCORE_THRESHOLD:
            if not override_reason or not override_reason.strip():
                raise FitLifecycleError(
                    f"PURSUE with score {score_value} below threshold {PURSUE_SCORE_THRESHOLD} "
                    "requires a bounded override: a reason and an expiry"
                )
            if not override_expiry:
                raise FitLifecycleError("a score override requires an expiry -- it is never permanent")
            is_override = True

    verdict_record = {
        "verdict": verdict,
        "decided_by": decided_by,
        "decided_at": decided_at,
        "score_value": score_value,
        "override": is_override,
        "override_reason": override_reason if is_override else None,
        "override_expiry": override_expiry if is_override else None,
    }

    updated = dict(assessment)
    updated["status"] = "decided"
    updated["verdict"] = verdict_record
    updated["updated_at"] = decided_at

    journal = EventJournal(root)
    journal.append(
        "FitDecided",
        workspace_id=assessment["workspace_id"],
        actor_id=decided_by,
        object_ref=f"fit_assessment:{assessment['fit_assessment_id']}",
        data={"fit_assessment_id": assessment["fit_assessment_id"], "verdict": verdict, "override": is_override},
        idempotency_key=f"fit-decided:{assessment['fit_assessment_id']}",
    )
    return updated


def mark_stale(assessment: dict[str, Any], *, reason: str, marked_at: str) -> dict[str, Any]:
    if not can_transition_fit(assessment["status"], "stale"):
        raise FitLifecycleError(f"cannot mark fit {assessment['fit_assessment_id']} stale from status {assessment['status']!r}")
    if not reason.strip():
        raise FitLifecycleError("marking a fit stale requires a reason")
    updated = dict(assessment)
    updated["status"] = "stale"
    updated["updated_at"] = marked_at
    return updated


def reopen_fit(assessment: dict[str, Any], *, reason: str, reopened_at: str) -> dict[str, Any]:
    if not can_transition_fit(assessment["status"], "in_review"):
        raise FitLifecycleError(f"cannot reopen fit {assessment['fit_assessment_id']} from status {assessment['status']!r}")
    if not reason.strip():
        raise FitLifecycleError("reopening a fit requires a reason")
    updated = dict(assessment)
    updated["status"] = "in_review"
    updated["updated_at"] = reopened_at
    return updated


def is_override_expired(verdict_record: dict[str, Any], *, now: str) -> bool:
    if not verdict_record.get("override"):
        return False
    expiry = verdict_record.get("override_expiry")
    return bool(expiry) and now > expiry
