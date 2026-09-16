"""Workspace-scoped storage for canonical v1 Person/Company/Relationship
records (Epic 02 S04).

Layout: ``data/private/network_v1/<workspace_id>/{people,companies,
relationships}.jsonl``, one JSON object per line, written through
app.artifact_store.ArtifactStore for atomic, locked writes. This is
intentionally separate from the legacy ``data/private/network/*.jsonl``
files S01's ADR-009 leaves untouched -- the v1 store only ever holds
entity_id-keyed canonical records, populated for real by Epic 02 S06's
migration/backfill.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from app.artifact_store import ArtifactStore

_KINDS = {"person": "people.jsonl", "company": "companies.jsonl", "relationship": "relationships.jsonl"}


class NetworkV1StoreError(RuntimeError):
    pass


class EntityNotFound(NetworkV1StoreError):
    pass


def _relative_path(workspace_id: str, kind: str) -> str:
    if kind not in _KINDS:
        raise NetworkV1StoreError(f"unknown entity kind: {kind}")
    return f"data/private/network_v1/{workspace_id}/{_KINDS[kind]}"


def _id_field(kind: str) -> str:
    return "relationship_entity_id" if kind == "relationship" else "entity_id"


def _read_all(store: ArtifactStore, workspace_id: str, kind: str) -> list[dict[str, Any]]:
    result = store.read_bytes(_relative_path(workspace_id, kind))
    if result is None:
        return []
    data, _version = result
    return [json.loads(line) for line in data.decode("utf-8").splitlines() if line.strip()]


def put_entity(root: Path, workspace_id: str, kind: str, record: dict[str, Any]) -> None:
    """Upsert one record, keyed by its entity id, into the workspace's kind file."""

    store = ArtifactStore(root)
    id_field = _id_field(kind)
    path = _relative_path(workspace_id, kind)

    def _updater(previous: bytes) -> bytes:
        records = [json.loads(line) for line in previous.decode("utf-8").splitlines() if line.strip()]
        records = [r for r in records if r[id_field] != record[id_field]]
        records.append(record)
        records.sort(key=lambda r: r[id_field])
        return ("\n".join(json.dumps(r, ensure_ascii=False, sort_keys=True) for r in records) + "\n").encode("utf-8")

    store.update_bytes(path, _updater)


@dataclass(frozen=True)
class Page:
    items: list[dict[str, Any]]
    next_cursor: str | None


def list_entities(
    root: Path,
    workspace_id: str,
    kind: str,
    *,
    limit: int = 20,
    cursor: str | None = None,
) -> Page:
    """List entities for a workspace, sorted by entity id, cursor-paginated.

    The cursor is simply the last-seen entity id on the previous page
    (opaque to the caller, stable as long as no record with a lexically
    earlier id is inserted between calls).
    """

    if limit <= 0:
        raise NetworkV1StoreError("limit must be positive")
    store = ArtifactStore(root)
    id_field = _id_field(kind)
    records = sorted(_read_all(store, workspace_id, kind), key=lambda r: r[id_field])
    if cursor is not None:
        records = [r for r in records if r[id_field] > cursor]
    page = records[:limit]
    next_cursor = page[-1][id_field] if len(records) > limit else None
    return Page(items=page, next_cursor=next_cursor)


def get_entity(root: Path, workspace_id: str, kind: str, entity_id: str) -> dict[str, Any]:
    store = ArtifactStore(root)
    id_field = _id_field(kind)
    for record in _read_all(store, workspace_id, kind):
        if record[id_field] == entity_id:
            return record
    raise EntityNotFound(f"{kind} {entity_id} not found in workspace {workspace_id}")


def iter_all_workspaces_for_entity(root: Path, kind: str, entity_id: str) -> Iterable[str]:
    """Yield workspace_ids that (currently) contain this entity id, for IDOR
    tests and cross-workspace audits -- deliberately not used by the read
    routes themselves, which must always take workspace_id from the
    authenticated path, never discover it by searching.
    """

    network_v1_root = root / "data" / "private" / "network_v1"
    if not network_v1_root.is_dir():
        return
    for workspace_dir in sorted(network_v1_root.iterdir()):
        if not workspace_dir.is_dir():
            continue
        try:
            get_entity(root, workspace_dir.name, kind, entity_id)
        except EntityNotFound:
            continue
        yield workspace_dir.name
