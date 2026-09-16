"""Workspace-scoped storage for CanonicalSequenceV1, CanonicalStepV1,
CanonicalTaskV1 and CanonicalTouchpointV1 (Epic 09 S05). Same
ArtifactStore-backed JSONL shape as the other v1 stores (Epic 02-08).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.artifact_store import ArtifactStore

_SEQUENCE_PATH = "data/private/reach/{workspace_id}/sequences.jsonl"
_STEP_PATH = "data/private/reach/{workspace_id}/steps.jsonl"
_TASK_PATH = "data/private/reach/{workspace_id}/tasks.jsonl"
_TOUCHPOINT_PATH = "data/private/reach/{workspace_id}/touchpoints.jsonl"


class ReachStoreError(RuntimeError):
    pass


class SequenceNotFound(ReachStoreError):
    pass


def _read_all(store: ArtifactStore, path: str) -> list[dict[str, Any]]:
    result = store.read_bytes(path)
    if result is None:
        return []
    data, _version = result
    return [json.loads(line) for line in data.decode("utf-8").splitlines() if line.strip()]


def _put(root: Path, workspace_id: str, path_template: str, record: dict[str, Any], id_field: str) -> None:
    store = ArtifactStore(root)
    path = path_template.format(workspace_id=workspace_id)

    def _updater(previous: bytes) -> bytes:
        records = [json.loads(line) for line in previous.decode("utf-8").splitlines() if line.strip()]
        records = [r for r in records if r[id_field] != record[id_field]]
        records.append(record)
        records.sort(key=lambda r: r[id_field])
        return ("\n".join(json.dumps(r, ensure_ascii=False, sort_keys=True) for r in records) + "\n").encode("utf-8")

    store.update_bytes(path, _updater)


def put_sequence(root: Path, workspace_id: str, sequence: dict[str, Any]) -> None:
    _put(root, workspace_id, _SEQUENCE_PATH, sequence, "sequence_id")


def get_sequence(root: Path, workspace_id: str, sequence_id: str) -> dict[str, Any]:
    store = ArtifactStore(root)
    for record in _read_all(store, _SEQUENCE_PATH.format(workspace_id=workspace_id)):
        if record["sequence_id"] == sequence_id:
            return record
    raise SequenceNotFound(f"sequence {sequence_id} not found in workspace {workspace_id}")


@dataclass(frozen=True)
class SequencePage:
    items: list[dict[str, Any]]
    next_cursor: str | None


def list_sequences(
    root: Path, workspace_id: str, *, status: str | None = None, limit: int = 20, cursor: str | None = None,
) -> SequencePage:
    if limit <= 0:
        raise ReachStoreError("limit must be positive")
    store = ArtifactStore(root)
    records = _read_all(store, _SEQUENCE_PATH.format(workspace_id=workspace_id))
    if status is not None:
        records = [r for r in records if r["status"] == status]
    records.sort(key=lambda r: r["sequence_id"])
    if cursor is not None:
        records = [r for r in records if r["sequence_id"] > cursor]
    page = records[:limit]
    next_cursor = page[-1]["sequence_id"] if len(records) > limit else None
    return SequencePage(items=page, next_cursor=next_cursor)


def put_step(root: Path, workspace_id: str, step: dict[str, Any]) -> None:
    _put(root, workspace_id, _STEP_PATH, step, "step_id")


def list_steps_for_sequence(root: Path, workspace_id: str, sequence_id: str) -> list[dict[str, Any]]:
    store = ArtifactStore(root)
    records = [
        r for r in _read_all(store, _STEP_PATH.format(workspace_id=workspace_id)) if r["sequence_id"] == sequence_id
    ]
    records.sort(key=lambda r: r["order"])
    return records


def put_task(root: Path, workspace_id: str, task: dict[str, Any]) -> None:
    _put(root, workspace_id, _TASK_PATH, task, "task_id")


def list_tasks_for_sequence(root: Path, workspace_id: str, sequence_id: str) -> list[dict[str, Any]]:
    store = ArtifactStore(root)
    records = [
        r for r in _read_all(store, _TASK_PATH.format(workspace_id=workspace_id)) if r["sequence_id"] == sequence_id
    ]
    records.sort(key=lambda r: r["task_id"])
    return records


def put_touchpoint(root: Path, workspace_id: str, touchpoint: dict[str, Any]) -> None:
    _put(root, workspace_id, _TOUCHPOINT_PATH, touchpoint, "touchpoint_id")


def list_touchpoints_for_step(root: Path, workspace_id: str, step_id: str) -> list[dict[str, Any]]:
    store = ArtifactStore(root)
    records = [
        r for r in _read_all(store, _TOUCHPOINT_PATH.format(workspace_id=workspace_id)) if r["step_id"] == step_id
    ]
    records.sort(key=lambda r: r["touchpoint_id"])
    return records
