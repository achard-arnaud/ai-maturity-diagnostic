"""Workspace-scoped storage for CanonicalResearchCaseV1 records (Epic 04 S02).

Mirrors app.signal_store's shape exactly (same ArtifactStore-backed JSONL
layout, same upsert/pagination contract).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.artifact_store import ArtifactStore

_RELATIVE_PATH = "data/private/research_cases/{workspace_id}/cases.jsonl"


class ResearchCaseStoreError(RuntimeError):
    pass


class ResearchCaseNotFound(ResearchCaseStoreError):
    pass


def _relative_path(workspace_id: str) -> str:
    return _RELATIVE_PATH.format(workspace_id=workspace_id)


def _read_all(store: ArtifactStore, workspace_id: str) -> list[dict[str, Any]]:
    result = store.read_bytes(_relative_path(workspace_id))
    if result is None:
        return []
    data, _version = result
    return [json.loads(line) for line in data.decode("utf-8").splitlines() if line.strip()]


def put_case(root: Path, workspace_id: str, case: dict[str, Any]) -> None:
    store = ArtifactStore(root)
    path = _relative_path(workspace_id)

    def _updater(previous: bytes) -> bytes:
        records = [json.loads(line) for line in previous.decode("utf-8").splitlines() if line.strip()]
        records = [r for r in records if r["research_case_id"] != case["research_case_id"]]
        records.append(case)
        records.sort(key=lambda r: r["research_case_id"])
        return ("\n".join(json.dumps(r, ensure_ascii=False, sort_keys=True) for r in records) + "\n").encode("utf-8")

    store.update_bytes(path, _updater)


@dataclass(frozen=True)
class ResearchCasePage:
    items: list[dict[str, Any]]
    next_cursor: str | None


def list_cases(
    root: Path,
    workspace_id: str,
    *,
    status: str | None = None,
    owner: str | None = None,
    limit: int = 20,
    cursor: str | None = None,
) -> ResearchCasePage:
    """List cases for a workspace, filtered and stably sorted by
    research_case_id, cursor-paginated (same contract as
    app.signal_store.list_signals)."""

    if limit <= 0:
        raise ResearchCaseStoreError("limit must be positive")
    store = ArtifactStore(root)
    records = _read_all(store, workspace_id)
    if status is not None:
        records = [r for r in records if r["status"] == status]
    if owner is not None:
        records = [r for r in records if r.get("owner") == owner]
    records.sort(key=lambda r: r["research_case_id"])
    if cursor is not None:
        records = [r for r in records if r["research_case_id"] > cursor]
    page = records[:limit]
    next_cursor = page[-1]["research_case_id"] if len(records) > limit else None
    return ResearchCasePage(items=page, next_cursor=next_cursor)


def get_case(root: Path, workspace_id: str, research_case_id: str) -> dict[str, Any]:
    store = ArtifactStore(root)
    for record in _read_all(store, workspace_id):
        if record["research_case_id"] == research_case_id:
            return record
    raise ResearchCaseNotFound(
        f"research case {research_case_id} not found in workspace {workspace_id}"
    )
