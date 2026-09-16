"""Epic 06 S01: Product/Version/Snapshot semantics.

Stop condition: "semantics figées" (frozen semantics) -- this module
draws the line between the three objects precisely and provably:
Product is bare durable identity, ProductVersion is the mutable draft
lifecycle, ProductSnapshot is the one immutable, hashed, published
artifact a version ever produces. Once published, a snapshot's
content_hash is a permanent fingerprint: recomputing the hash from the
same content must always match, and a snapshot already recorded under a
given snapshot_id can never be replaced with different content under
that same id (see assert_snapshot_immutable).
"""

from __future__ import annotations

import hashlib
import json
from typing import Mapping

_VERSION_TRANSITIONS: dict[str, set[str]] = {
    "draft": {"in_review", "archived"},
    "in_review": {"published", "draft"},
    "published": {"superseded"},
    "superseded": set(),
    "archived": set(),
}


class ProductPolicyError(Exception):
    pass


class SnapshotImmutabilityError(ProductPolicyError):
    pass


def can_transition_version(current_status: str, next_status: str) -> bool:
    return next_status in _VERSION_TRANSITIONS.get(current_status, set())


def compute_content_hash(content: Mapping) -> str:
    """Deterministic hash of a snapshot's content -- same content, same
    hash, regardless of key insertion order (sort_keys=True)."""
    canonical = json.dumps(content, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def assert_snapshot_immutable(existing_snapshot: Mapping, new_content: Mapping) -> None:
    """Raise if new_content would change what's already published under
    existing_snapshot's snapshot_id -- a published snapshot's content_hash
    is permanent; only a *new* snapshot_id (from a new ProductVersion) may
    carry different content."""
    new_hash = compute_content_hash(new_content)
    if new_hash != existing_snapshot["content_hash"]:
        raise SnapshotImmutabilityError(
            f"snapshot {existing_snapshot['snapshot_id']} is published and immutable -- "
            "publish a new ProductVersion instead of altering it"
        )


def next_version_number(existing_version_numbers: list[int]) -> int:
    """Monotonically increasing, never reused even if versions are
    archived -- always one past the highest number ever assigned."""
    return (max(existing_version_numbers) + 1) if existing_version_numbers else 1
