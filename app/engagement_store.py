"""Workspace-scoped storage for CanonicalConversationV1,
CanonicalEngagementEventV1 and CanonicalObjectionV1 (Epic 10 S05). Same
ArtifactStore-backed JSONL shape as the other v1 stores (Epic 02-09).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.artifact_store import ArtifactStore

_CONVERSATION_PATH = "data/private/engagement/{workspace_id}/conversations.jsonl"
_EVENT_PATH = "data/private/engagement/{workspace_id}/events.jsonl"
_OBJECTION_PATH = "data/private/engagement/{workspace_id}/objections.jsonl"


class EngagementStoreError(RuntimeError):
    pass


class ConversationNotFound(EngagementStoreError):
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


def put_conversation(root: Path, workspace_id: str, conversation: dict[str, Any]) -> None:
    _put(root, workspace_id, _CONVERSATION_PATH, conversation, "conversation_id")


def get_conversation(root: Path, workspace_id: str, conversation_id: str) -> dict[str, Any]:
    store = ArtifactStore(root)
    for record in _read_all(store, _CONVERSATION_PATH.format(workspace_id=workspace_id)):
        if record["conversation_id"] == conversation_id:
            return record
    raise ConversationNotFound(f"conversation {conversation_id} not found in workspace {workspace_id}")


@dataclass(frozen=True)
class ConversationPage:
    items: list[dict[str, Any]]
    next_cursor: str | None


def list_conversations(
    root: Path, workspace_id: str, *, status: str | None = None, limit: int = 20, cursor: str | None = None,
) -> ConversationPage:
    if limit <= 0:
        raise EngagementStoreError("limit must be positive")
    store = ArtifactStore(root)
    records = _read_all(store, _CONVERSATION_PATH.format(workspace_id=workspace_id))
    if status is not None:
        records = [r for r in records if r["status"] == status]
    records.sort(key=lambda r: r["conversation_id"])
    if cursor is not None:
        records = [r for r in records if r["conversation_id"] > cursor]
    page = records[:limit]
    next_cursor = page[-1]["conversation_id"] if len(records) > limit else None
    return ConversationPage(items=page, next_cursor=next_cursor)


def put_engagement_event(root: Path, workspace_id: str, event: dict[str, Any]) -> None:
    _put(root, workspace_id, _EVENT_PATH, event, "engagement_event_id")


def list_events_for_conversation(root: Path, workspace_id: str, conversation_id: str) -> list[dict[str, Any]]:
    store = ArtifactStore(root)
    records = [
        r for r in _read_all(store, _EVENT_PATH.format(workspace_id=workspace_id))
        if r["conversation_id"] == conversation_id
    ]
    records.sort(key=lambda r: r["occurred_at"])
    return records


def put_objection(root: Path, workspace_id: str, objection: dict[str, Any]) -> None:
    _put(root, workspace_id, _OBJECTION_PATH, objection, "objection_id")


def list_objections_for_event(root: Path, workspace_id: str, engagement_event_id: str) -> list[dict[str, Any]]:
    store = ArtifactStore(root)
    records = [
        r for r in _read_all(store, _OBJECTION_PATH.format(workspace_id=workspace_id))
        if r["engagement_event_id"] == engagement_event_id
    ]
    records.sort(key=lambda r: r["objection_id"])
    return records
