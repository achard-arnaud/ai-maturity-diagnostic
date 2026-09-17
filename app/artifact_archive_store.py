"""Epic 15 S03/S05: the one piece of state the artifact index persists on
its own -- which artifact_ids are archived (hidden from default listing).

Nothing else about an Artifact is stored here: app.artifact_index derives
every other field live from the canonical stores on every call. This is
deliberately the smallest possible store: a set of archived artifact_ids
plus who archived them and when, never a copy of the artifact itself.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.artifact_store import ArtifactStore

_RELATIVE_PATH = "data/private/artifact_archive/{workspace_id}/archived.jsonl"


class ArtifactArchiveStoreError(RuntimeError):
    pass


def _relative_path(workspace_id: str) -> str:
    return _RELATIVE_PATH.format(workspace_id=workspace_id)


def _read_all(store: ArtifactStore, workspace_id: str) -> list[dict[str, Any]]:
    result = store.read_bytes(_relative_path(workspace_id))
    if result is None:
        return []
    data, _version = result
    return [json.loads(line) for line in data.decode("utf-8").splitlines() if line.strip()]


def list_archived_ids(root: Path, workspace_id: str) -> set[str]:
    store = ArtifactStore(root)
    return {r["artifact_id"] for r in _read_all(store, workspace_id)}


def archive_artifact(root: Path, workspace_id: str, artifact_id: str, *, actor: str, archived_at: str) -> None:
    store = ArtifactStore(root)
    path = _relative_path(workspace_id)

    def _updater(previous: bytes) -> bytes:
        records = [json.loads(line) for line in previous.decode("utf-8").splitlines() if line.strip()]
        records = [r for r in records if r["artifact_id"] != artifact_id]
        records.append({"artifact_id": artifact_id, "archived_by": actor, "archived_at": archived_at})
        records.sort(key=lambda r: r["artifact_id"])
        return ("\n".join(json.dumps(r, ensure_ascii=False, sort_keys=True) for r in records) + "\n").encode("utf-8")

    store.update_bytes(path, _updater)


def restore_artifact(root: Path, workspace_id: str, artifact_id: str) -> None:
    store = ArtifactStore(root)
    path = _relative_path(workspace_id)

    def _updater(previous: bytes) -> bytes:
        records = [json.loads(line) for line in previous.decode("utf-8").splitlines() if line.strip()]
        records = [r for r in records if r["artifact_id"] != artifact_id]
        return ("\n".join(json.dumps(r, ensure_ascii=False, sort_keys=True) for r in records) + "\n").encode("utf-8")

    store.update_bytes(path, _updater)
