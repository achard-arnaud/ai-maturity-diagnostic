"""Human "not a duplicate" decisions on top of
`app.network_index.find_potential_duplicates` (red-team-side-story C3).

`find_potential_duplicates` is detection-only and recomputes its groups fresh
on every call from the derived SQLite index -- it has no memory of a past
human decision. This module adds that memory: a small, append/update JSONL
store (`data/private/network/duplicate_dismissals.jsonl`) of dismissed
duplicate groups, following this epic's existing per-record-decision
convention (`app.campaigns.mark_campaign_sent`, `app.nudging.accept_nudge` /
`reject_nudge`): a stable, content-derived id, a read-modify-atomic-rewrite
JSONL file, and an idempotent write.

The dismissal key is derived from the *set* of `person_id`s in a duplicate
group (sorted, so member order never matters) via
`scripts.network_common.stable_id` -- the same group of person_ids always
dismisses to the same id, so re-running detection and dismissing "the same"
group again is a no-op rather than a second record. This module never
mutates `people.jsonl`/`companies.jsonl` or the SQLite index itself; it only
records a human's read-side decision about a detection result, exactly like
`app.network_index.find_potential_duplicates`'s own module docstring
describes for that function ("never merges, deletes or otherwise mutates
anything").

Plain Python only -- no FastAPI/Starlette imports here (see app/server.py's
module docstring on the FastAPI-boundary rule).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.core import ControlPlaneError
from scripts.network_common import read_jsonl, stable_id, utc_now, write_jsonl


def _dismissals_path(root: Path) -> Path:
    return Path(root) / "data" / "private" / "network" / "duplicate_dismissals.jsonl"


def _group_key(person_ids: list[str]) -> str:
    unique_sorted = sorted({str(pid) for pid in person_ids if pid})
    if len(unique_sorted) < 2:
        raise ControlPlaneError("a duplicate group needs at least two distinct person_ids to dismiss")
    return stable_id("DUPDISMISS", *unique_sorted)


def _load(root: Path) -> list[dict[str, Any]]:
    return read_jsonl(_dismissals_path(root))


def list_dismissed_group_keys(root: Path) -> set[str]:
    """All currently-dismissed group keys, for filtering detection output."""
    return {item["group_key"] for item in _load(root) if item.get("group_key")}


def list_dismissals(root: Path) -> list[dict[str, Any]]:
    return sorted(_load(root), key=lambda item: str(item.get("group_key") or ""))


def dismiss_duplicate_group(root: Path, person_ids: list[str], *, actor: str, reason: str | None = None) -> dict[str, Any]:
    """Record that a human reviewed this exact set of person_ids and decided
    they are not duplicates of each other.

    Idempotent: dismissing the same group_key again just refreshes
    `dismissed_at`/`actor`/`reason` on the existing record rather than
    creating a second one (mirrors mark_campaign_sent's/accept_nudge's own
    idempotent-decision convention).
    """
    actor = str(actor or "").strip()
    if not actor:
        raise ControlPlaneError("actor is required to dismiss a duplicate group")
    if not isinstance(person_ids, list) or not person_ids:
        raise ControlPlaneError("person_ids must be a non-empty list")
    group_key = _group_key(person_ids)
    records = [item for item in _load(root) if item.get("group_key") != group_key]
    record = {
        "group_key": group_key,
        "person_ids": sorted({str(pid) for pid in person_ids if pid}),
        "actor": actor,
        "reason": (reason or "").strip() or None,
        "dismissed_at": utc_now(),
    }
    records.append(record)
    write_jsonl(_dismissals_path(root), records, sort_key="group_key")
    return record
