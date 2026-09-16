# STOP — Epic 06 / Sprint S03

## Objective

Snapshot hash, immutability et stale propagation. Stop condition: "fit
reproductible" (fit reproducible) -- mutation/repro tests.

## Outputs

- `app/product_snapshot_store.py`: flat, product_id-keyed
  `ArtifactStore`-backed storage.
  - `put_snapshot`: idempotent no-op when re-putting *identical* content
    under an already-stored `snapshot_id`; raises
    `SnapshotImmutabilityError` (S01's guard, enforced here at the store
    layer) the instant *different* content is submitted under an
    existing id -- a mutation attempt is refused, never silently applied.
  - `get_snapshot`/`list_snapshots_for_product`/`get_latest_snapshot`:
    plain reads, sorted by `published_at`.
  - `is_snapshot_stale(root, snapshot_id)`: true the instant a snapshot
    is no longer its product's latest published one -- staleness
    propagates automatically the moment a newer version publishes,
    scoped strictly per `product_id` (a newer snapshot for a *different*
    product never marks another product's current snapshot stale).
  - Workspace/overlay visibility isolation (ADR-008) is explicitly out of
    scope here -- S04 builds that on top of this flat index.
- `tests/test_product_snapshot_store.py`: 10 tests -- round-trip, missing
  snapshot, re-put-identical-is-noop, re-put-different-is-rejected, and
  the Sprint's core reproducibility property
  (`test_fetching_same_snapshot_repeatedly_is_reproducible`: three
  fetches of the same snapshot_id always return the identical
  content_hash, and that hash is independently recomputable from the
  content); plus staleness propagation (only snapshot isn't stale,
  latest-snapshot lookup, older snapshot becomes stale once superseded,
  staleness scoped per product, and a stale snapshot's own content stays
  intact and reproducible -- it's flagged stale, never mutated or
  deleted).

## Evidence

`python -m unittest tests.test_product_snapshot_store -v`: 10/10 pass.
Full `python scripts/check_release.py`: 0 errors.
