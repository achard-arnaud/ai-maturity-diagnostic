"""SavedSearch, List, SmartList and Watchlist over signals (Epic 03 S03).

Stop condition is "listes versionnees": every List (including a
materialized SmartList or a Watchlist, which are both just a List with a
different `kind`) carries an integer `version` that increments on every
membership change, and updating a list never mutates the old version in
place -- it returns a new object, so a prior version stays inspectable.

A SavedSearch's matching itself is a pure function over
(signal, criteria): identical inputs always produce an identical member
set in an identical (sorted) order, whatever order the input signals were
supplied in -- that is what "deterministic membership" means here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

ListKind = Literal["list", "smart_list", "watchlist"]


class SignalListError(RuntimeError):
    pass


def matches_criteria(signal: dict[str, Any], criteria: dict[str, Any]) -> bool:
    """Whether one signal satisfies a SavedSearch's criteria.

    Supported keys (all optional, all AND-ed together): source_kind,
    status, workspace_id. Unknown criteria keys are rejected rather than
    silently ignored, so a typo'd filter never silently matches
    everything.
    """

    supported = {"source_kind", "status", "workspace_id"}
    unknown = criteria.keys() - supported
    if unknown:
        raise SignalListError(f"unsupported SavedSearch criteria key(s): {sorted(unknown)}")

    if "source_kind" in criteria and signal["source"]["kind"] != criteria["source_kind"]:
        return False
    if "status" in criteria and signal["status"] != criteria["status"]:
        return False
    if "workspace_id" in criteria and signal["workspace_id"] != criteria["workspace_id"]:
        return False
    return True


def run_saved_search(signals: list[dict[str, Any]], criteria: dict[str, Any]) -> list[dict[str, Any]]:
    """Evaluate a SavedSearch's criteria against a signal set.

    Deterministic: the result is always sorted by signal_id, regardless
    of the input list's order, so running the same search twice against
    the same underlying signals (even if fetched/ordered differently)
    yields the exact same member list.
    """

    matched = [signal for signal in signals if matches_criteria(signal, criteria)]
    return sorted(matched, key=lambda signal: signal["signal_id"])


@dataclass(frozen=True)
class SignalList:
    list_id: str
    workspace_id: str
    kind: ListKind
    version: int
    member_ids: tuple[str, ...]
    criteria: dict[str, Any] | None = field(default=None)


def create_list(list_id: str, workspace_id: str, *, member_ids: list[str] | None = None) -> SignalList:
    return SignalList(
        list_id=list_id,
        workspace_id=workspace_id,
        kind="list",
        version=1,
        member_ids=tuple(sorted(set(member_ids or []))),
    )


def update_list_members(existing: SignalList, member_ids: list[str]) -> SignalList:
    """Return a new SignalList with the given membership and version+1.

    The passed-in `existing` object is never mutated -- callers that want
    history keep a reference to it before calling this.
    """

    if existing.kind != "list":
        raise SignalListError("update_list_members only applies to a plain List; a SmartList is re-materialized, not edited")
    new_members = tuple(sorted(set(member_ids)))
    return SignalList(
        list_id=existing.list_id,
        workspace_id=existing.workspace_id,
        kind="list",
        version=existing.version + 1,
        member_ids=new_members,
    )


def create_watchlist(list_id: str, workspace_id: str, *, company_entity_ids: list[str] | None = None) -> SignalList:
    """A Watchlist is mechanically a List (versioned, same update path)
    whose members are company entity_ids rather than signal_ids.
    """

    return SignalList(
        list_id=list_id,
        workspace_id=workspace_id,
        kind="watchlist",
        version=1,
        member_ids=tuple(sorted(set(company_entity_ids or []))),
    )


def materialize_smart_list(
    existing: SignalList | None,
    list_id: str,
    workspace_id: str,
    criteria: dict[str, Any],
    signals: list[dict[str, Any]],
) -> SignalList:
    """Re-run a SmartList's criteria against the current signal set and
    return a new versioned snapshot. `existing` is the previous
    materialization (None for the first one) -- its version is never
    mutated, only superseded by the returned object.
    """

    matched = run_saved_search(signals, criteria)
    member_ids = tuple(signal["signal_id"] for signal in matched)
    next_version = (existing.version + 1) if existing else 1
    return SignalList(
        list_id=list_id,
        workspace_id=workspace_id,
        kind="smart_list",
        version=next_version,
        member_ids=member_ids,
        criteria=dict(criteria),
    )
