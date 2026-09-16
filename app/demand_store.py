"""Workspace-scoped storage for CanonicalDemandV1 records with optimistic
concurrency (Epic 05 S04). Stop condition: "mutation sûre" -- a mutation
against a stale version is refused (DemandConflict) rather than silently
overwriting a concurrent edit, and creating an already-existing demand_id
is refused (DemandAlreadyExists) rather than silently replacing it.

Storage shape mirrors app.signal_store/app.research_case_store (same
ArtifactStore-backed JSONL layout), with one addition: each stored record
carries an internal "_version" counter (starting at 1, incremented on
every update) that is never part of the CanonicalDemandV1 schema itself
-- callers see it as a separate return value, not a schema field.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from app.artifact_store import ArtifactStore

_RELATIVE_PATH = "data/private/demands/{workspace_id}/demands.jsonl"


class DemandStoreError(RuntimeError):
    pass


class DemandNotFound(DemandStoreError):
    pass


class DemandAlreadyExists(DemandStoreError):
    pass


class DemandConflict(DemandStoreError):
    """Raised when an update's expected_version doesn't match the
    record's current stored version -- the safe-mutation refusal."""


def _relative_path(workspace_id: str) -> str:
    return _RELATIVE_PATH.format(workspace_id=workspace_id)


def _read_all(store: ArtifactStore, workspace_id: str) -> list[dict[str, Any]]:
    result = store.read_bytes(_relative_path(workspace_id))
    if result is None:
        return []
    data, _version = result
    return [json.loads(line) for line in data.decode("utf-8").splitlines() if line.strip()]


def _write_all(store: ArtifactStore, workspace_id: str, records: list[dict[str, Any]]) -> None:
    path = _relative_path(workspace_id)
    records = sorted(records, key=lambda r: r["demand_id"])
    body = ("\n".join(json.dumps(r, ensure_ascii=False, sort_keys=True) for r in records) + "\n").encode("utf-8") if records else b""

    def _updater(_previous: bytes) -> bytes:
        return body

    store.update_bytes(path, _updater)


def create_demand(root: Path, workspace_id: str, demand: dict[str, Any]) -> int:
    """Create a new demand. Refuses (DemandAlreadyExists) if demand_id is
    already present -- never silently replaces an existing record."""
    store = ArtifactStore(root)
    records = _read_all(store, workspace_id)
    if any(r["demand_id"] == demand["demand_id"] for r in records):
        raise DemandAlreadyExists(f"demand {demand['demand_id']} already exists in workspace {workspace_id}")
    records.append({**demand, "_version": 1})
    _write_all(store, workspace_id, records)
    return 1


def get_demand(root: Path, workspace_id: str, demand_id: str) -> tuple[dict[str, Any], int]:
    store = ArtifactStore(root)
    for record in _read_all(store, workspace_id):
        if record["demand_id"] == demand_id:
            version = record["_version"]
            demand = {k: v for k, v in record.items() if k != "_version"}
            return demand, version
    raise DemandNotFound(f"demand {demand_id} not found in workspace {workspace_id}")


def update_demand(
    root: Path,
    workspace_id: str,
    demand_id: str,
    mutator: Callable[[dict[str, Any]], dict[str, Any]],
    *,
    expected_version: int,
) -> tuple[dict[str, Any], int]:
    """Apply mutator to the current demand and persist, but only if
    expected_version matches the record's current stored version.
    Raises DemandConflict otherwise -- the caller must re-fetch and retry,
    same discipline as app.artifact_store's expected_version writes."""
    store = ArtifactStore(root)
    records = _read_all(store, workspace_id)
    for index, record in enumerate(records):
        if record["demand_id"] == demand_id:
            current_version = record["_version"]
            if current_version != expected_version:
                raise DemandConflict(
                    f"demand {demand_id} is at version {current_version}, "
                    f"but update expected version {expected_version}"
                )
            current = {k: v for k, v in record.items() if k != "_version"}
            updated = mutator(current)
            new_version = current_version + 1
            records[index] = {**updated, "_version": new_version}
            _write_all(store, workspace_id, records)
            return updated, new_version
    raise DemandNotFound(f"demand {demand_id} not found in workspace {workspace_id}")


@dataclass(frozen=True)
class DemandPage:
    items: list[dict[str, Any]]
    next_cursor: str | None


def list_demands(
    root: Path,
    workspace_id: str,
    *,
    status: str | None = None,
    company_entity_id: str | None = None,
    limit: int = 20,
    cursor: str | None = None,
) -> DemandPage:
    if limit <= 0:
        raise DemandStoreError("limit must be positive")
    store = ArtifactStore(root)
    records = [{k: v for k, v in r.items() if k != "_version"} for r in _read_all(store, workspace_id)]
    if status is not None:
        records = [r for r in records if r["status"] == status]
    if company_entity_id is not None:
        records = [r for r in records if r["company_entity_id"] == company_entity_id]
    records.sort(key=lambda r: r["demand_id"])
    if cursor is not None:
        records = [r for r in records if r["demand_id"] > cursor]
    page = records[:limit]
    next_cursor = page[-1]["demand_id"] if len(records) > limit else None
    return DemandPage(items=page, next_cursor=next_cursor)
