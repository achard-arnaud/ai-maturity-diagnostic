"""Epic 06 S03: snapshot storage with enforced immutability and stale
propagation. Stop condition: "fit reproductible" -- a snapshot_id, once
stored, always reproduces the exact same content; and any reference to a
non-latest snapshot for its product is detectably stale, so a future
consumer (Fit, Epic 07) never silently reasons from an outdated product
truth.

Workspace/overlay isolation (ADR-008's shared-core-vs-overlay visibility
model) is explicitly out of scope here -- S04 builds that. This store is
a flat, product_id-keyed index.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.artifact_store import ArtifactStore
from app.product_policy import assert_snapshot_immutable

_RELATIVE_PATH = "data/private/product_snapshots/snapshots.jsonl"


class ProductSnapshotStoreError(RuntimeError):
    pass


class ProductSnapshotNotFound(ProductSnapshotStoreError):
    pass


def _read_all(store: ArtifactStore) -> list[dict[str, Any]]:
    result = store.read_bytes(_RELATIVE_PATH)
    if result is None:
        return []
    data, _version = result
    return [json.loads(line) for line in data.decode("utf-8").splitlines() if line.strip()]


def put_snapshot(root: Path, snapshot: dict[str, Any]) -> None:
    """Store a snapshot. Idempotent for identical content re-put under
    the same snapshot_id; raises SnapshotImmutabilityError (never
    silently overwrites) if a *different* content is submitted under an
    already-stored snapshot_id."""
    store = ArtifactStore(root)
    records = _read_all(store)
    for existing in records:
        if existing["snapshot_id"] == snapshot["snapshot_id"]:
            assert_snapshot_immutable(existing, snapshot["content"])
            return  # identical content already stored -- no-op

    records.append(snapshot)
    records.sort(key=lambda r: r["snapshot_id"])
    body = ("\n".join(json.dumps(r, ensure_ascii=False, sort_keys=True) for r in records) + "\n").encode("utf-8")

    def _updater(_previous: bytes) -> bytes:
        return body

    store.update_bytes(_RELATIVE_PATH, _updater)


def get_snapshot(root: Path, snapshot_id: str) -> dict[str, Any]:
    store = ArtifactStore(root)
    for record in _read_all(store):
        if record["snapshot_id"] == snapshot_id:
            return record
    raise ProductSnapshotNotFound(f"snapshot {snapshot_id} not found")


def list_snapshots_for_product(root: Path, product_id: str) -> list[dict[str, Any]]:
    store = ArtifactStore(root)
    records = [r for r in _read_all(store) if r["product_id"] == product_id]
    records.sort(key=lambda r: r["published_at"])
    return records


def get_latest_snapshot(root: Path, product_id: str) -> dict[str, Any] | None:
    records = list_snapshots_for_product(root, product_id)
    return records[-1] if records else None


def is_snapshot_stale(root: Path, snapshot_id: str) -> bool:
    """A snapshot is stale the instant it is no longer its product's
    latest published snapshot -- staleness propagates automatically from
    a later publish, never requires a separate manual flag."""
    snapshot = get_snapshot(root, snapshot_id)
    latest = get_latest_snapshot(root, snapshot["product_id"])
    return latest is not None and latest["snapshot_id"] != snapshot_id
