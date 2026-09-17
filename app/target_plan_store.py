"""Workspace-scoped storage for CanonicalTargetPlanV1 and
CanonicalStakeholderRoleV1 (Epic 08 S05). Same ArtifactStore-backed JSONL
shape as the other v1 stores (Epic 02-07).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.artifact_store import ArtifactStore

_PLAN_PATH = "data/private/target_plans/{workspace_id}/plans.jsonl"
_STAKEHOLDER_PATH = "data/private/target_plans/{workspace_id}/stakeholders.jsonl"


class TargetPlanStoreError(RuntimeError):
    pass


class TargetPlanNotFound(TargetPlanStoreError):
    pass


def _read_all(store: ArtifactStore, path: str) -> list[dict[str, Any]]:
    result = store.read_bytes(path)
    if result is None:
        return []
    data, _version = result
    return [json.loads(line) for line in data.decode("utf-8").splitlines() if line.strip()]


def put_plan(root: Path, workspace_id: str, plan: dict[str, Any]) -> None:
    store = ArtifactStore(root)
    path = _PLAN_PATH.format(workspace_id=workspace_id)

    def _updater(previous: bytes) -> bytes:
        records = [json.loads(line) for line in previous.decode("utf-8").splitlines() if line.strip()]
        records = [r for r in records if r["target_plan_id"] != plan["target_plan_id"]]
        records.append(plan)
        records.sort(key=lambda r: r["target_plan_id"])
        return ("\n".join(json.dumps(r, ensure_ascii=False, sort_keys=True) for r in records) + "\n").encode("utf-8")

    store.update_bytes(path, _updater)


def get_plan(root: Path, workspace_id: str, target_plan_id: str) -> dict[str, Any]:
    store = ArtifactStore(root)
    for record in _read_all(store, _PLAN_PATH.format(workspace_id=workspace_id)):
        if record["target_plan_id"] == target_plan_id:
            return record
    raise TargetPlanNotFound(f"target plan {target_plan_id} not found in workspace {workspace_id}")


@dataclass(frozen=True)
class TargetPlanPage:
    items: list[dict[str, Any]]
    next_cursor: str | None


def list_plans(
    root: Path, workspace_id: str, *, status: str | None = None, limit: int = 20, cursor: str | None = None,
) -> TargetPlanPage:
    if limit <= 0:
        raise TargetPlanStoreError("limit must be positive")
    store = ArtifactStore(root)
    records = _read_all(store, _PLAN_PATH.format(workspace_id=workspace_id))
    if status is not None:
        records = [r for r in records if r["status"] == status]
    records.sort(key=lambda r: r["target_plan_id"])
    if cursor is not None:
        records = [r for r in records if r["target_plan_id"] > cursor]
    page = records[:limit]
    next_cursor = page[-1]["target_plan_id"] if len(records) > limit else None
    return TargetPlanPage(items=page, next_cursor=next_cursor)


def put_stakeholder(root: Path, workspace_id: str, stakeholder: dict[str, Any]) -> None:
    store = ArtifactStore(root)
    path = _STAKEHOLDER_PATH.format(workspace_id=workspace_id)

    def _updater(previous: bytes) -> bytes:
        records = [json.loads(line) for line in previous.decode("utf-8").splitlines() if line.strip()]
        records = [r for r in records if r["stakeholder_role_id"] != stakeholder["stakeholder_role_id"]]
        records.append(stakeholder)
        records.sort(key=lambda r: r["stakeholder_role_id"])
        return ("\n".join(json.dumps(r, ensure_ascii=False, sort_keys=True) for r in records) + "\n").encode("utf-8")

    store.update_bytes(path, _updater)


def list_stakeholders_for_plan(root: Path, workspace_id: str, target_plan_id: str) -> list[dict[str, Any]]:
    store = ArtifactStore(root)
    records = [
        r for r in _read_all(store, _STAKEHOLDER_PATH.format(workspace_id=workspace_id))
        if r["target_plan_id"] == target_plan_id
    ]
    records.sort(key=lambda r: r["stakeholder_role_id"])
    return records


def list_all_stakeholders(root: Path, workspace_id: str) -> list[dict[str, Any]]:
    """Every stakeholder role in the workspace, regardless of target_plan_id
    (Epic 15 S03: the artifact index needs a workspace-wide view; the
    per-plan file is already workspace-scoped, this just skips the
    target_plan_id filter list_stakeholders_for_plan applies)."""
    store = ArtifactStore(root)
    records = _read_all(store, _STAKEHOLDER_PATH.format(workspace_id=workspace_id))
    records.sort(key=lambda r: r["stakeholder_role_id"])
    return records
