"""Epic 07 S01: FitAssessment input version locking.

Stop condition: "mêmes inputs=même base" (same inputs => same base) --
locking a FitAssessment to an exact (demand_id, demand_version,
product_snapshot_id) triple, and hashing that triple deterministically,
is what lets two assessments over the same locked inputs be proven to
share the identical evidentiary base, and what lets a later re-check
detect that the world has moved on (the demand was edited again, or a
newer product snapshot published) without silently re-basing.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass


@dataclass(frozen=True)
class InputLock:
    demand_id: str
    demand_version: int
    product_snapshot_id: str
    input_hash: str


def compute_input_lock_hash(demand_id: str, demand_version: int, product_snapshot_id: str) -> str:
    canonical = json.dumps(
        {"demand_id": demand_id, "demand_version": demand_version, "product_snapshot_id": product_snapshot_id},
        ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def create_input_lock(demand_id: str, demand_version: int, product_snapshot_id: str) -> InputLock:
    return InputLock(
        demand_id=demand_id,
        demand_version=demand_version,
        product_snapshot_id=product_snapshot_id,
        input_hash=compute_input_lock_hash(demand_id, demand_version, product_snapshot_id),
    )


def is_input_lock_current(lock: InputLock, *, current_demand_version: int, current_snapshot_id: str) -> bool:
    """True only if nothing has moved since this lock was created -- the
    demand is still at the exact version locked, and the product
    snapshot locked is still the one referenced (Epic 06's own
    is_snapshot_stale decides whether *that* snapshot is still the
    product's latest; this function only checks the lock still points
    at what it originally locked)."""
    return lock.demand_version == current_demand_version and lock.product_snapshot_id == current_snapshot_id
