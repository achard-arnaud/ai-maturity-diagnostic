"""Workspace-scoped storage for CanonicalFitAssessmentV1 with optimistic
concurrency (Epic 07 S05). Same shape as app.demand_store (Epic 05 S04):
create refuses an existing fit_assessment_id, update requires a matching
expected_version and raises FitConflict on a stale one.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from app.artifact_store import ArtifactStore

_RELATIVE_PATH = "data/private/fit_assessments/{workspace_id}/assessments.jsonl"


class FitStoreError(RuntimeError):
    pass


class FitNotFound(FitStoreError):
    pass


class FitAlreadyExists(FitStoreError):
    pass


class FitConflict(FitStoreError):
    pass


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
    records = sorted(records, key=lambda r: r["fit_assessment_id"])
    body = ("\n".join(json.dumps(r, ensure_ascii=False, sort_keys=True) for r in records) + "\n").encode("utf-8") if records else b""

    def _updater(_previous: bytes) -> bytes:
        return body

    store.update_bytes(path, _updater)


def create_fit(root: Path, workspace_id: str, assessment: dict[str, Any]) -> int:
    store = ArtifactStore(root)
    records = _read_all(store, workspace_id)
    if any(r["fit_assessment_id"] == assessment["fit_assessment_id"] for r in records):
        raise FitAlreadyExists(f"fit assessment {assessment['fit_assessment_id']} already exists")
    records.append({**assessment, "_version": 1})
    _write_all(store, workspace_id, records)
    return 1


def get_fit(root: Path, workspace_id: str, fit_assessment_id: str) -> tuple[dict[str, Any], int]:
    store = ArtifactStore(root)
    for record in _read_all(store, workspace_id):
        if record["fit_assessment_id"] == fit_assessment_id:
            version = record["_version"]
            return {k: v for k, v in record.items() if k != "_version"}, version
    raise FitNotFound(f"fit assessment {fit_assessment_id} not found")


def update_fit(
    root: Path,
    workspace_id: str,
    fit_assessment_id: str,
    mutator: Callable[[dict[str, Any]], dict[str, Any]],
    *,
    expected_version: int,
) -> tuple[dict[str, Any], int]:
    store = ArtifactStore(root)
    records = _read_all(store, workspace_id)
    for index, record in enumerate(records):
        if record["fit_assessment_id"] == fit_assessment_id:
            current_version = record["_version"]
            if current_version != expected_version:
                raise FitConflict(
                    f"fit assessment {fit_assessment_id} is at version {current_version}, "
                    f"but update expected version {expected_version}"
                )
            current = {k: v for k, v in record.items() if k != "_version"}
            updated = mutator(current)
            new_version = current_version + 1
            records[index] = {**updated, "_version": new_version}
            _write_all(store, workspace_id, records)
            return updated, new_version
    raise FitNotFound(f"fit assessment {fit_assessment_id} not found")


@dataclass(frozen=True)
class FitPage:
    items: list[dict[str, Any]]
    next_cursor: str | None


def list_fits(
    root: Path,
    workspace_id: str,
    *,
    status: str | None = None,
    demand_id: str | None = None,
    limit: int = 20,
    cursor: str | None = None,
) -> FitPage:
    if limit <= 0:
        raise FitStoreError("limit must be positive")
    store = ArtifactStore(root)
    records = [{k: v for k, v in r.items() if k != "_version"} for r in _read_all(store, workspace_id)]
    if status is not None:
        records = [r for r in records if r["status"] == status]
    if demand_id is not None:
        records = [r for r in records if r["input_lock"]["demand_id"] == demand_id]
    records.sort(key=lambda r: r["fit_assessment_id"])
    if cursor is not None:
        records = [r for r in records if r["fit_assessment_id"] > cursor]
    page = records[:limit]
    next_cursor = page[-1]["fit_assessment_id"] if len(records) > limit else None
    return FitPage(items=page, next_cursor=next_cursor)
