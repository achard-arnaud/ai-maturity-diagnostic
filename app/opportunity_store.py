"""Epic 11 S05: workspace-scoped Opportunity persistence and Pipeline reads."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.artifact_store import ArtifactStore

_PATH = "data/private/opportunities/{workspace_id}/opportunities.jsonl"
PIPELINE_STAGES = ("draft", "discovery", "proof", "proposal", "closed_won", "closed_lost")


class OpportunityNotFound(KeyError):
    pass


def _read(root: Path, workspace_id: str) -> list[dict[str, Any]]:
    result = ArtifactStore(root).read_bytes(_PATH.format(workspace_id=workspace_id))
    return [] if result is None else [json.loads(line) for line in result[0].decode("utf-8").splitlines() if line]


def put_opportunity(root: Path, workspace_id: str, opportunity: dict[str, Any]) -> None:
    if opportunity["workspace_id"] != workspace_id:
        raise ValueError("opportunity workspace does not match storage workspace")
    store = ArtifactStore(root)
    path = _PATH.format(workspace_id=workspace_id)
    def update(previous: bytes) -> bytes:
        records = [json.loads(line) for line in previous.decode("utf-8").splitlines() if line]
        records = [record for record in records if record["opportunity_id"] != opportunity["opportunity_id"]]
        records.append(dict(opportunity))
        records.sort(key=lambda record: record["opportunity_id"])
        return ("\n".join(json.dumps(record, sort_keys=True) for record in records) + "\n").encode("utf-8")
    store.update_bytes(path, update)


def get_opportunity(root: Path, workspace_id: str, opportunity_id: str) -> dict[str, Any]:
    for record in _read(root, workspace_id):
        if record["opportunity_id"] == opportunity_id:
            return record
    raise OpportunityNotFound(opportunity_id)


@dataclass(frozen=True)
class OpportunityPage:
    items: list[dict[str, Any]]
    next_cursor: str | None


def list_opportunities(root: Path, workspace_id: str, *, stage: str | None = None, limit: int = 20, cursor: str | None = None) -> OpportunityPage:
    if not 1 <= limit <= 100:
        raise ValueError("limit must be between 1 and 100")
    records = _read(root, workspace_id)
    if stage is not None:
        records = [record for record in records if record["status"] == stage]
    records.sort(key=lambda record: record["opportunity_id"])
    if cursor is not None:
        records = [record for record in records if record["opportunity_id"] > cursor]
    page = records[:limit]
    return OpportunityPage(page, page[-1]["opportunity_id"] if len(records) > limit else None)


def build_pipeline_board(root: Path, workspace_id: str) -> dict[str, list[dict[str, Any]]]:
    """Return a deterministic projection; empty stages remain visible to clients."""
    board = {stage: [] for stage in PIPELINE_STAGES}
    for record in _read(root, workspace_id):
        board[record["status"]].append(record)
    for stage in PIPELINE_STAGES:
        board[stage].sort(key=lambda record: record["opportunity_id"])
    return board
