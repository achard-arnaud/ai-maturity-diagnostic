"""Epic 06 S02: draft/review/publish/supersede workflow and RBAC.

Stop condition: "publication contrôlée" (controlled publication) --
publishing is the one privileged, audited step in this whole lifecycle:
only a `product_owner` may do it (ADR-008's authorization model), it is
only reachable from `in_review`, and every publish appends an audited
event to Epic 01's `EventJournal` (same pattern as Epic 04's
`research_review.py`). Publishing a new version also supersedes whatever
version was previously published for the same product, in the same
operation -- there is never a window where two versions are both
"published" for one product.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.event_journal import EventJournal
from app.product_policy import can_transition_version, compute_content_hash

PUBLISH_ROLE = "product_owner"


class ProductWorkflowError(Exception):
    pass


class ProductAuthorizationError(ProductWorkflowError):
    pass


def create_draft_version(
    *,
    product_version_id: str,
    product_id: str,
    version_number: int,
    created_by: str,
    created_at: str,
) -> dict[str, Any]:
    return {
        "product_version_id": product_version_id,
        "product_id": product_id,
        "version_number": version_number,
        "status": "draft",
        "created_at": created_at,
        "created_by": created_by,
        "published_snapshot_id": None,
    }


def submit_for_review(version: dict[str, Any]) -> dict[str, Any]:
    if not can_transition_version(version["status"], "in_review"):
        raise ProductWorkflowError(
            f"cannot submit version {version['product_version_id']} for review from status {version['status']!r}"
        )
    updated = dict(version)
    updated["status"] = "in_review"
    return updated


def publish_version(
    root: Path,
    version: dict[str, Any],
    content: dict[str, Any],
    *,
    owner_scope: dict[str, Any],
    snapshot_id: str,
    evidence_ids: list[str],
    published_by: str,
    actor_role: str | None,
    published_at: str,
    previous_published_version: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any] | None]:
    """Publish version, producing its one-and-only ProductSnapshot.

    Returns (published_version, snapshot, superseded_previous_version).
    Requires actor_role == "product_owner" -- any other role (including
    None/unauthenticated) is refused, never silently downgraded. Requires
    status == "in_review". If previous_published_version is given (the
    product's currently published version, if any), it is transitioned to
    "superseded" in the same call -- never left dangling as "published"
    alongside the new one.
    """
    if actor_role != PUBLISH_ROLE:
        raise ProductAuthorizationError(
            f"publishing requires the {PUBLISH_ROLE!r} role; got {actor_role!r}"
        )
    if not can_transition_version(version["status"], "published"):
        raise ProductWorkflowError(
            f"cannot publish version {version['product_version_id']} from status {version['status']!r}"
        )
    if previous_published_version is not None:
        if not can_transition_version(previous_published_version["status"], "superseded"):
            raise ProductWorkflowError(
                f"previous version {previous_published_version['product_version_id']} "
                f"cannot be superseded from status {previous_published_version['status']!r}"
            )

    snapshot = {
        "snapshot_id": snapshot_id,
        "product_id": version["product_id"],
        "product_version_id": version["product_version_id"],
        "owner_scope": owner_scope,
        "content": content,
        "content_hash": compute_content_hash(content),
        "published_at": published_at,
        "evidence_ids": list(evidence_ids),
        "supersedes_snapshot_id": (
            previous_published_version.get("published_snapshot_id") if previous_published_version else None
        ),
    }

    published_version = dict(version)
    published_version["status"] = "published"
    published_version["published_snapshot_id"] = snapshot_id

    superseded_previous = None
    if previous_published_version is not None:
        superseded_previous = dict(previous_published_version)
        superseded_previous["status"] = "superseded"

    journal = EventJournal(root)
    journal.append(
        "ProductPublished",
        workspace_id=(owner_scope.get("workspace_id") or "shared"),
        actor_id=published_by,
        object_ref=f"product_snapshot:{snapshot_id}",
        data={
            "product_id": version["product_id"],
            "product_version_id": version["product_version_id"],
            "snapshot_id": snapshot_id,
            "supersedes_snapshot_id": snapshot["supersedes_snapshot_id"],
        },
        idempotency_key=f"product-published:{snapshot_id}",
    )

    return published_version, snapshot, superseded_previous
