"""Epic 15 S02: Artifact metadata contract.

Pure, dependency-free shapes and functions -- no storage, no network
(mirrors app.research_policy's/app.acquisition_policy's established
convention). An Artifact is a discovery pointer into an existing
canonical store (contracts/artifact_v1.schema.yaml), never a second
source of truth -- this module only knows how to build/validate that
pointer shape; app.artifact_index (S03) owns actually deriving one from
each canonical store.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

import yaml

CONTRACTS_ROOT = Path(__file__).resolve().parents[1] / "contracts"

# The single source of truth for which canonical object kinds this build
# of the index understands (contracts/artifact_v1.schema.yaml's own
# description: `kind` is a plain string there, not a closed enum, because
# this set is expected to grow without a schema migration each time).
KNOWN_KINDS = frozenset(
    {
        "signal",
        "evidence",
        "research_case",
        "claim",
        "demand",
        "fit_assessment",
        "target_plan",
        "stakeholder_role",
        "sequence",
        "touchpoint",
        "discovery_note",
        "commercial_decision",
        "opportunity",
        "learning_proposal",
        "product_snapshot",
    }
)


class ArtifactPolicyError(RuntimeError):
    pass


def load_artifact_schema() -> dict[str, Any]:
    path = CONTRACTS_ROOT / "artifact_v1.schema.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def build_artifact(
    *,
    artifact_id: str,
    kind: str,
    title: str,
    workspace_id: str,
    created_at: str,
    created_by: str,
    locator: str,
    owner: str | None = None,
    related_ids: tuple[str, ...] = (),
    run_id: str | None = None,
    workflow: str | None = None,
    created_by_agent: str | None = None,
    version: int = 1,
    status: str = "active",
    supersedes: str | None = None,
    superseded_by: str | None = None,
    preview: bool = False,
    export: bool = False,
) -> dict[str, Any]:
    """Build a schema-shaped Artifact dict. Raises on an unknown kind or
    an invalid status -- an index builder that doesn't recognize what it's
    looking at should fail loudly, not silently index garbage."""

    if kind not in KNOWN_KINDS:
        raise ArtifactPolicyError(f"unknown artifact kind: {kind!r} (see app.artifact_policy.KNOWN_KINDS)")
    if not title.strip():
        raise ArtifactPolicyError("title is required")
    if not workspace_id.strip():
        raise ArtifactPolicyError("workspace_id is required")
    if not locator.strip():
        raise ArtifactPolicyError("locator is required")
    if status not in {"active", "archived"}:
        raise ArtifactPolicyError(f"unknown status: {status!r} (expected active or archived)")
    if version < 1:
        raise ArtifactPolicyError("version must be >= 1")

    return {
        "artifact_id": artifact_id,
        "kind": kind,
        "title": title,
        "workspace_id": workspace_id,
        "owner": owner,
        "related_ids": list(related_ids),
        "run_id": run_id,
        "workflow": workflow,
        "created_at": created_at,
        "created_by": created_by,
        "created_by_agent": created_by_agent,
        "version": version,
        "status": status,
        "locator": locator,
        "supersedes": supersedes,
        "superseded_by": superseded_by,
        "capabilities": {"preview": preview, "export": export},
    }


def can_archive(artifact: Mapping[str, Any]) -> bool:
    return artifact["status"] == "active"


def can_restore(artifact: Mapping[str, Any]) -> bool:
    return artifact["status"] == "archived"


def archive(artifact: Mapping[str, Any]) -> dict[str, Any]:
    """Return an archived copy. Never touches anything but this record's
    own status -- see contracts/artifact_v1.schema.yaml's x-rules."""
    if not can_archive(artifact):
        raise ArtifactPolicyError(f"artifact {artifact['artifact_id']} is already {artifact['status']}")
    return {**artifact, "status": "archived"}


def restore(artifact: Mapping[str, Any]) -> dict[str, Any]:
    if not can_restore(artifact):
        raise ArtifactPolicyError(f"artifact {artifact['artifact_id']} is not archived")
    return {**artifact, "status": "active"}
