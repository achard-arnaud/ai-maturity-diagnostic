"""Epic 04 S01: ResearchCase/Claim/Evidence policy.

Pure, dependency-free functions -- no storage, no network. Encodes the
truth-typing rules from 02_DOMAIN_AND_TRUTH_MODEL.md and the evidence/claim
lineage rules from 08_EVIDENCE_DECISION_AND_GATES.md.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Sequence

NON_FACT_EVIDENCE_GRADE = "N0"

_CASE_TRANSITIONS: dict[str, set[str]] = {
    "open": {"in_progress", "blocked"},
    "in_progress": {"blocked", "in_review"},
    "blocked": {"in_progress"},
    "in_review": {"accepted", "reopened", "in_progress"},
    "accepted": {"stale"},
    "reopened": {"in_progress", "blocked"},
    "stale": {"reopened"},
}


def can_transition_case(current_status: str, next_status: str, *, open_blockers: int) -> bool:
    """Whether a ResearchCase may move from current_status to next_status.

    A case with any unresolved blocker can never reach "accepted" --
    08_EVIDENCE_DECISION_AND_GATES.md's "a score never turns ... an open
    critical blocker into PURSUE" generalizes to case acceptance too.
    """
    if next_status == "accepted" and open_blockers > 0:
        return False
    return next_status in _CASE_TRANSITIONS.get(current_status, set())


@dataclass(frozen=True)
class ClaimLineageError:
    claim_id: str
    reason: str


def validate_claim_lineage(
    claim: Mapping,
    *,
    evidence_by_id: Mapping[str, Mapping],
    claims_by_id: Mapping[str, Mapping],
) -> ClaimLineageError | None:
    """Validate a single claim's typed lineage rules.

    Returns None if valid, or a ClaimLineageError describing the first
    violation found. Callers should re-check whenever a claim is created or
    an evidence/claim it depends on changes.
    """
    claim_id = claim["claim_id"]
    claim_type = claim["claim_type"]
    evidence_ids: Sequence[str] = claim.get("evidence_ids", [])
    derived_from: Sequence[str] = claim.get("derived_from_claim_ids", [])

    for evidence_id in evidence_ids:
        if evidence_id not in evidence_by_id:
            return ClaimLineageError(claim_id, f"evidence_id {evidence_id!r} does not exist")
    for parent_id in derived_from:
        if parent_id not in claims_by_id:
            return ClaimLineageError(claim_id, f"derived_from_claim_ids {parent_id!r} does not exist")

    if claim_type == "fact":
        if not evidence_ids:
            return ClaimLineageError(claim_id, "a fact claim requires at least one evidence_id")
        graded = [evidence_by_id[e]["evidence_grade"] for e in evidence_ids]
        if all(grade == NON_FACT_EVIDENCE_GRADE for grade in graded):
            return ClaimLineageError(
                claim_id, "a fact claim requires at least one non-N0-grade evidence_id"
            )
    elif claim_type == "inference":
        if not evidence_ids and not derived_from:
            return ClaimLineageError(
                claim_id, "an inference claim requires evidence_ids or derived_from_claim_ids"
            )
    elif claim_type == "hypothesis":
        if not claim.get("hypothesis_owner"):
            return ClaimLineageError(claim_id, "a hypothesis claim requires hypothesis_owner")
        if not claim.get("hypothesis_due_at"):
            return ClaimLineageError(claim_id, "a hypothesis claim requires hypothesis_due_at")
    else:
        return ClaimLineageError(claim_id, f"unknown claim_type {claim_type!r}")

    return None


def is_claim_type_promotion(old_type: str, new_type: str) -> bool:
    """Whether moving from old_type to new_type is a "promotion" toward fact.

    Per 02_DOMAIN_AND_TRUTH_MODEL.md, no automated process may promote a
    claim's type -- this is a pure predicate for callers/tests to assert
    against; it never performs the promotion itself.
    """
    rank = {"hypothesis": 0, "inference": 1, "fact": 2}
    return rank[new_type] > rank[old_type]


@dataclass(frozen=True)
class CompletenessResult:
    is_complete: bool
    missing: tuple[str, ...] = field(default_factory=tuple)


REQUIRED_CLAIM_TYPES_FOR_COMPLETE = ("fact",)


def compute_completeness(claims: Sequence[Mapping]) -> CompletenessResult:
    """Minimal completeness policy for a ResearchCase's claim set.

    Per 08_EVIDENCE_DECISION_AND_GATES.md's gate order, "completeness et
    provenance" is gate #1, evaluated before freshness or scoring. A case is
    complete once it has at least one active fact claim (every other typed
    claim -- inference/hypothesis -- may remain open).
    """
    active = [c for c in claims if c.get("status") == "active"]
    missing = []
    for required_type in REQUIRED_CLAIM_TYPES_FOR_COMPLETE:
        if not any(c["claim_type"] == required_type for c in active):
            missing.append(f"no active {required_type} claim")
    return CompletenessResult(is_complete=not missing, missing=tuple(missing))
