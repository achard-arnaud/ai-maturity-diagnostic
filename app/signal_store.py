"""Workspace-scoped storage for CanonicalSignalV1 records (Epic 03 S05).

Mirrors app.network_v1_store's shape exactly (same ArtifactStore-backed
JSONL layout, same upsert/pagination contract) so the two read-model
layers stay consistent for anyone building on either.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.artifact_store import ArtifactStore

_RELATIVE_PATH = "data/private/signals/{workspace_id}/signals.jsonl"


class SignalStoreError(RuntimeError):
    pass


class SignalNotFound(SignalStoreError):
    pass


def _relative_path(workspace_id: str) -> str:
    return _RELATIVE_PATH.format(workspace_id=workspace_id)


def _read_all(store: ArtifactStore, workspace_id: str) -> list[dict[str, Any]]:
    result = store.read_bytes(_relative_path(workspace_id))
    if result is None:
        return []
    data, _version = result
    return [json.loads(line) for line in data.decode("utf-8").splitlines() if line.strip()]


def put_signal(root: Path, workspace_id: str, signal: dict[str, Any]) -> None:
    store = ArtifactStore(root)
    path = _relative_path(workspace_id)

    def _updater(previous: bytes) -> bytes:
        records = [json.loads(line) for line in previous.decode("utf-8").splitlines() if line.strip()]
        records = [r for r in records if r["signal_id"] != signal["signal_id"]]
        records.append(signal)
        records.sort(key=lambda r: r["signal_id"])
        return ("\n".join(json.dumps(r, ensure_ascii=False, sort_keys=True) for r in records) + "\n").encode("utf-8")

    store.update_bytes(path, _updater)


@dataclass(frozen=True)
class SignalPage:
    items: list[dict[str, Any]]
    next_cursor: str | None


def list_signals(
    root: Path,
    workspace_id: str,
    *,
    status: str | None = None,
    source_kind: str | None = None,
    limit: int = 20,
    cursor: str | None = None,
) -> SignalPage:
    """List signals for a workspace, filtered and stably sorted by
    signal_id, cursor-paginated. Stable sort means: for a given
    status/source_kind filter and an unchanged underlying signal set,
    repeated calls (with or without a cursor) always return the same
    order -- no ties broken arbitrarily, no implicit recency reordering.
    """

    if limit <= 0:
        raise SignalStoreError("limit must be positive")
    store = ArtifactStore(root)
    records = _read_all(store, workspace_id)
    if status is not None:
        records = [r for r in records if r["status"] == status]
    if source_kind is not None:
        records = [r for r in records if r["source"]["kind"] == source_kind]
    records.sort(key=lambda r: r["signal_id"])
    if cursor is not None:
        records = [r for r in records if r["signal_id"] > cursor]
    page = records[:limit]
    next_cursor = page[-1]["signal_id"] if len(records) > limit else None
    return SignalPage(items=page, next_cursor=next_cursor)


def get_signal(root: Path, workspace_id: str, signal_id: str) -> dict[str, Any]:
    store = ArtifactStore(root)
    for record in _read_all(store, workspace_id):
        if record["signal_id"] == signal_id:
            return record
    raise SignalNotFound(f"signal {signal_id} not found in workspace {workspace_id}")


def find_by_dedup_key(root: Path, workspace_id: str, dedup_key: str) -> dict[str, Any] | None:
    """The existing signal with this dedup_key, if any (Epic 14 S04: a
    harvest must not create a second signal for the same underlying
    observation it, or an earlier run, already recorded)."""
    store = ArtifactStore(root)
    for record in _read_all(store, workspace_id):
        if record["dedup_key"] == dedup_key:
            return record
    return None
