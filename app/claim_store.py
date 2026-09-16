"""Workspace-scoped storage for CanonicalClaimV1 records (Epic 04 S05)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.artifact_store import ArtifactStore

_RELATIVE_PATH = "data/private/claims/{workspace_id}/claims.jsonl"


class ClaimStoreError(RuntimeError):
    pass


class ClaimNotFound(ClaimStoreError):
    pass


def _relative_path(workspace_id: str) -> str:
    return _RELATIVE_PATH.format(workspace_id=workspace_id)


def _read_all(store: ArtifactStore, workspace_id: str) -> list[dict[str, Any]]:
    result = store.read_bytes(_relative_path(workspace_id))
    if result is None:
        return []
    data, _version = result
    return [json.loads(line) for line in data.decode("utf-8").splitlines() if line.strip()]


def put_claim(root: Path, workspace_id: str, claim: dict[str, Any]) -> None:
    store = ArtifactStore(root)
    path = _relative_path(workspace_id)

    def _updater(previous: bytes) -> bytes:
        records = [json.loads(line) for line in previous.decode("utf-8").splitlines() if line.strip()]
        records = [r for r in records if r["claim_id"] != claim["claim_id"]]
        records.append(claim)
        records.sort(key=lambda r: r["claim_id"])
        return ("\n".join(json.dumps(r, ensure_ascii=False, sort_keys=True) for r in records) + "\n").encode("utf-8")

    store.update_bytes(path, _updater)


def list_claims(
    root: Path,
    workspace_id: str,
    *,
    company_entity_id: str | None = None,
    research_case_id: str | None = None,
) -> list[dict[str, Any]]:
    store = ArtifactStore(root)
    records = _read_all(store, workspace_id)
    if company_entity_id is not None:
        records = [r for r in records if r["company_entity_id"] == company_entity_id]
    if research_case_id is not None:
        records = [r for r in records if r["research_case_id"] == research_case_id]
    records.sort(key=lambda r: r["claim_id"])
    return records


def get_claim(root: Path, workspace_id: str, claim_id: str) -> dict[str, Any]:
    store = ArtifactStore(root)
    for record in _read_all(store, workspace_id):
        if record["claim_id"] == claim_id:
            return record
    raise ClaimNotFound(f"claim {claim_id} not found in workspace {workspace_id}")
