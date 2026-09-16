"""Currentness policy for CanonicalRelationshipV1 (Epic 02 S02).

A relationship's "is this current" question must never be answered from
current_status alone: current_status is a state enum a writer can leave
stale, while valid_from/valid_to is the actual temporal-validity interval
introduced in Epic 02 S01 (contracts/relationship_v1.schema.yaml). This
module is the single place that combines the two, so no caller has to
reimplement (or forget) the conflict rule.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


class CurrentnessConflict(Exception):
    """Raised when current_status and the validity interval disagree
    in a way that cannot be silently resolved -- a human decision is
    required, per Epic 02's "role courant explicable" stop condition.
    """


@dataclass(frozen=True)
class CurrentnessResult:
    is_current: bool
    reason: str


def evaluate_currentness(relationship: dict, *, as_of: date) -> CurrentnessResult:
    """Decide whether a v1 relationship record is current as_of a given date.

    Rules (in order):
    valid_to is inclusive: it is the last day the relationship is still
    valid, not the first day it stops being valid.

    1. status invalidated -> never current, regardless of dates.
    2. valid_to in the past (< as_of) -> not current, regardless of
       current_status. A relationship a writer forgot to mark "former"
       does not become current again just because current_status says so.
    3. valid_from in the future (> as_of) -> not current yet.
    4. status former with no valid_to set -> conflict: the interval says
       still open-ended but the status says it ended. This is exactly the
       kind of stale/contradictory record Epic 02 S02 must surface rather
       than guess at -- raises CurrentnessConflict.
    5. Otherwise: current iff current_status in {current, unverified}.
    """

    status = relationship["current_status"]
    valid_from = date.fromisoformat(relationship["valid_from"])
    valid_to_raw = relationship.get("valid_to")
    valid_to = date.fromisoformat(valid_to_raw) if valid_to_raw else None

    if status == "invalidated":
        return CurrentnessResult(False, "status is invalidated")

    if valid_to is not None and valid_to < as_of:
        return CurrentnessResult(False, "valid_to has passed")

    if valid_from > as_of:
        return CurrentnessResult(False, "valid_from is in the future")

    if status == "former" and valid_to is None:
        raise CurrentnessConflict(
            "current_status is 'former' but valid_to is not set -- "
            "requires human resolution, not an automatic guess"
        )

    if status in ("current", "unverified"):
        return CurrentnessResult(True, f"status={status}, within validity interval")

    return CurrentnessResult(False, f"status={status}")
