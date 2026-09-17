"""Workspace-scoped storage for ExternalIdentityMapping records (Epic 14 S06).

Mirrors app.evidence_store's/app.signal_store's exact shape (same
ArtifactStore-backed JSONL layout). contracts/external_identity_mapping
.schema.yaml has no workspace_id field of its own (and forbids
additionalProperties) -- isolation is by storage path only, same
convention app.execution_policy.BudgetLedger already uses for a record
shape with no workspace_id field embedded in its own YAML content.

Per the schema's own x-rule ("This object is private and must not enter
Git with real identifiers"), records here live under data/private/, same
as every other real-identifier-bearing store in this codebase.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.artifact_store import ArtifactStore

_RELATIVE_PATH = "data/private/identity_mappings/{workspace_id}/mappings.jsonl"


class ExternalIdentityStoreError(RuntimeError):
    pass


class ExternalIdentityMappingNotFound(ExternalIdentityStoreError):
    pass


def _relative_path(workspace_id: str) -> str:
    return _RELATIVE_PATH.format(workspace_id=workspace_id)


def _read_all(store: ArtifactStore, workspace_id: str) -> list[dict[str, Any]]:
    result = store.read_bytes(_relative_path(workspace_id))
    if result is None:
        return []
    data, _version = result
    return [json.loads(line) for line in data.decode("utf-8").splitlines() if line.strip()]


def put_mapping(root: Path, workspace_id: str, mapping: dict[str, Any]) -> None:
    store = ArtifactStore(root)
    path = _relative_path(workspace_id)

    def _updater(previous: bytes) -> bytes:
        records = [json.loads(line) for line in previous.decode("utf-8").splitlines() if line.strip()]
        records = [r for r in records if r["mapping_id"] != mapping["mapping_id"]]
        records.append(mapping)
        records.sort(key=lambda r: r["mapping_id"])
        return ("\n".join(json.dumps(r, ensure_ascii=False, sort_keys=True) for r in records) + "\n").encode("utf-8")

    store.update_bytes(path, _updater)


def list_mappings_for_entity(
    root: Path, workspace_id: str, *, internal_entity_type: str, internal_entity_id: str
) -> list[dict[str, Any]]:
    store = ArtifactStore(root)
    records = _read_all(store, workspace_id)
    records = [
        r
        for r in records
        if r["internal_entity_type"] == internal_entity_type and r["internal_entity_id"] == internal_entity_id
    ]
    records.sort(key=lambda r: r["mapping_id"])
    return records


def find_by_external_subject_ref(
    root: Path, workspace_id: str, *, provider: str, external_subject_ref: str
) -> dict[str, Any] | None:
    """The existing mapping for this provider+external locator, if any
    (Epic 14 S06: a repeated LinkedIn acquisition for the same person must
    not create a second candidate mapping for the same profile hit)."""
    store = ArtifactStore(root)
    for record in _read_all(store, workspace_id):
        if record["provider"] == provider and record["external_subject_ref"] == external_subject_ref:
            return record
    return None
