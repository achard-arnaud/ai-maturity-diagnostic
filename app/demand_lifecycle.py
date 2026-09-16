"""Epic 05 S02: Demand lifecycle and qualification checklist/gates.

Stop condition: "transitions explicables" -- every transition this module
refuses names exactly why, per 08_EVIDENCE_DECISION_AND_GATES.md's
resolver contract (why_blocked/required_state_or_evidence). A qualified
Demand never happens by a status flip alone: qualify_demand always runs
the checklist first, and a failing checklist can never be overridden by
setting status directly (the caller has no other path to "qualified").
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

_TRANSITIONS: dict[str, set[str]] = {
    "observed": {"qualifying", "rejected"},
    "qualifying": {"qualified", "rejected"},
    "qualified": {"stale"},
    "rejected": {"reopened"},
    "stale": {"reopened"},
    "reopened": {"qualifying", "rejected"},
}

# Per the Epic's target state, problem is load-bearing (a Demand cannot be
# qualified without knowing the problem); at least one of the buying-signal
# dimensions must also be known -- otherwise there is nothing to qualify
# against, even if the problem itself is well understood.
REQUIRED_KNOWN_FOR_QUALIFICATION = ("problem",)
BUYING_SIGNAL_FIELDS = ("sponsor", "budget", "timing", "urgency", "initiative")


class DemandLifecycleError(Exception):
    """Always carries an explicable why_blocked reason -- see .reason."""

    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


@dataclass(frozen=True)
class QualificationChecklist:
    passed: bool
    missing: tuple[str, ...]


def run_qualification_checklist(demand: Mapping) -> QualificationChecklist:
    missing = []
    for field in REQUIRED_KNOWN_FOR_QUALIFICATION:
        if not demand.get(field, {}).get("known"):
            missing.append(f"{field} is unknown")
    if not any(demand.get(field, {}).get("known") for field in BUYING_SIGNAL_FIELDS):
        missing.append(
            "no buying signal is known (need at least one of: "
            + ", ".join(BUYING_SIGNAL_FIELDS) + ")"
        )
    return QualificationChecklist(passed=not missing, missing=tuple(missing))


def can_transition(current_status: str, next_status: str) -> bool:
    return next_status in _TRANSITIONS.get(current_status, set())


def _require_transition(demand: Mapping, next_status: str) -> None:
    current = demand["status"]
    if not can_transition(current, next_status):
        raise DemandLifecycleError(
            f"cannot move demand {demand['demand_id']} from status {current!r} to {next_status!r}"
        )


def transition_to_qualifying(demand: Mapping, *, updated_at: str) -> dict:
    _require_transition(demand, "qualifying")
    updated = dict(demand)
    updated["status"] = "qualifying"
    updated["updated_at"] = updated_at
    return updated


def qualify_demand(demand: Mapping, *, updated_at: str) -> dict:
    """The only path to status="qualified" -- always runs the checklist
    first; a demand that fails it is never marked qualified, however the
    caller tries."""
    _require_transition(demand, "qualified")
    checklist = run_qualification_checklist(demand)
    if not checklist.passed:
        raise DemandLifecycleError(
            f"demand {demand['demand_id']} fails qualification: " + "; ".join(checklist.missing)
        )
    updated = dict(demand)
    updated["status"] = "qualified"
    updated["updated_at"] = updated_at
    return updated


def reject_demand(demand: Mapping, *, reason: str, updated_at: str) -> dict:
    _require_transition(demand, "rejected")
    if not reason.strip():
        raise DemandLifecycleError("rejecting a demand requires a reason")
    updated = dict(demand)
    updated["status"] = "rejected"
    updated["updated_at"] = updated_at
    return updated


def mark_stale(demand: Mapping, *, reason: str, updated_at: str) -> dict:
    _require_transition(demand, "stale")
    if not reason.strip():
        raise DemandLifecycleError("marking a demand stale requires a reason")
    updated = dict(demand)
    updated["status"] = "stale"
    updated["updated_at"] = updated_at
    return updated


def reopen_demand(demand: Mapping, *, reason: str, updated_at: str) -> dict:
    _require_transition(demand, "reopened")
    if not reason.strip():
        raise DemandLifecycleError("reopening a demand requires a reason")
    updated = dict(demand)
    updated["status"] = "reopened"
    updated["updated_at"] = updated_at
    return updated
