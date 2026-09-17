"""Workspace-scoped storage for CanonicalEvidenceV1 records (Epic 04 S05)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.artifact_store import ArtifactStore

_RELATIVE_PATH = "data/private/evidence/{workspace_id}/evidence.jsonl"


class EvidenceStoreError(RuntimeError):
    pass


class EvidenceNotFound(EvidenceStoreError):
    pass


def _relative_path(workspace_id: str) -> str:
    return _RELATIVE_PATH.format(workspace_id=workspace_id)


def _read_all(store: ArtifactStore, workspace_id: str) -> list[dict[str, Any]]:
    result = store.read_bytes(_relative_path(workspace_id))
    if result is None:
        return []
    data, _version = result
    return [json.loads(line) for line in data.decode("utf-8").splitlines() if line.strip()]


def put_evidence(root: Path, workspace_id: str, evidence: dict[str, Any]) -> None:
    store = ArtifactStore(root)
    path = _relative_path(workspace_id)

    def _updater(previous: bytes) -> bytes:
        records = [json.loads(line) for line in previous.decode("utf-8").splitlines() if line.strip()]
        records = [r for r in records if r["evidence_id"] != evidence["evidence_id"]]
        records.append(evidence)
        records.sort(key=lambda r: r["evidence_id"])
        return ("\n".join(json.dumps(r, ensure_ascii=False, sort_keys=True) for r in records) + "\n").encode("utf-8")

    store.update_bytes(path, _updater)


def list_evidence(root: Path, workspace_id: str, *, entity_ref: str | None = None) -> list[dict[str, Any]]:
    store = ArtifactStore(root)
    records = _read_all(store, workspace_id)
    if entity_ref is not None:
        records = [r for r in records if entity_ref in r.get("entity_refs", [])]
    records.sort(key=lambda r: r["evidence_id"])
    return records


def get_evidence(root: Path, workspace_id: str, evidence_id: str) -> dict[str, Any]:
    store = ArtifactStore(root)
    for record in _read_all(store, workspace_id):
        if record["evidence_id"] == evidence_id:
            return record
    raise EvidenceNotFound(f"evidence {evidence_id} not found in workspace {workspace_id}")


def find_by_hash(root: Path, workspace_id: str, content_hash: str) -> dict[str, Any] | None:
    """The existing evidence record with this excerpt hash, if any (Epic 14
    S05: a repeated acquisition for the same ResearchCase must not create a
    second evidence record for the same underlying observation)."""
    store = ArtifactStore(root)
    for record in _read_all(store, workspace_id):
        if record["hash"] == content_hash:
            return record
    return None
