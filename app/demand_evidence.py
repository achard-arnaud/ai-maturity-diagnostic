"""Epic 05 S03: Claim/Evidence links, confidence and contradiction for
Demand. Stop condition: "provenance complète" -- a Demand with any known
dimension must be traceable to at least one still-active linked Claim; a
Demand whose only linked claims have since been superseded/retracted is
provenance-stale, never silently treated as still grounded.
"""

from __future__ import annotations

from typing import Mapping

from app.demand_policy import KNOWABLE_FIELDS

# Reuses Epic 03/04's P1/P2/U1/W1/N0 evidence_grade scale, best first.
_GRADE_RANK = {"P1": 4, "P2": 3, "U1": 2, "W1": 1, "N0": 0}
_CONFIDENCE_THRESHOLDS = (("high", 3), ("medium", 1))


def link_claim(demand: Mapping, claim_id: str) -> dict:
    """Idempotent: linking an already-linked claim_id is a no-op."""
    claim_ids = list(demand.get("claim_ids", []))
    if claim_id not in claim_ids:
        claim_ids.append(claim_id)
    updated = dict(demand)
    updated["claim_ids"] = claim_ids
    return updated


def unlink_claim(demand: Mapping, claim_id: str) -> dict:
    """Idempotent: unlinking a claim_id not present is a no-op."""
    claim_ids = [c for c in demand.get("claim_ids", []) if c != claim_id]
    updated = dict(demand)
    updated["claim_ids"] = claim_ids
    return updated


def _has_any_known_field(demand: Mapping) -> bool:
    return any(demand.get(field, {}).get("known") for field in KNOWABLE_FIELDS)


def active_linked_claims(demand: Mapping, claims_by_id: Mapping[str, Mapping]) -> list[Mapping]:
    return [
        claims_by_id[cid]
        for cid in demand.get("claim_ids", [])
        if cid in claims_by_id and claims_by_id[cid].get("status") == "active"
    ]


def has_complete_provenance(demand: Mapping, claims_by_id: Mapping[str, Mapping]) -> bool:
    """A Demand with no known dimension trivially has complete (empty)
    provenance -- there is nothing yet to ground. A Demand with any known
    dimension needs at least one still-active linked claim."""
    if not _has_any_known_field(demand):
        return True
    return len(active_linked_claims(demand, claims_by_id)) > 0


def is_provenance_stale(demand: Mapping, claims_by_id: Mapping[str, Mapping]) -> bool:
    """True when the Demand has linked claims, but none of them are
    active anymore (all superseded/retracted, or all missing) -- the
    Demand's grounding has rotted out from under it, even though nothing
    about the Demand record itself changed."""
    claim_ids = demand.get("claim_ids", [])
    if not claim_ids:
        return False
    return len(active_linked_claims(demand, claims_by_id)) == 0


def compute_confidence(demand: Mapping, claims_by_id: Mapping[str, Mapping]) -> str:
    """Confidence derived from the best evidence_grade among the Demand's
    active linked claims' own evidence -- this module doesn't have direct
    evidence access, so it takes the claim's own best-known grade if the
    claim carries one (defensive: claims may not always expose it)."""
    active = active_linked_claims(demand, claims_by_id)
    best_rank = -1
    for claim in active:
        grade = claim.get("evidence_grade")
        if grade in _GRADE_RANK:
            best_rank = max(best_rank, _GRADE_RANK[grade])
    for label, threshold in _CONFIDENCE_THRESHOLDS:
        if best_rank >= threshold:
            return label
    return "low"
