"""Identity resolution: merge proposals and human-audited, reversible merges.

Epic 02 S03. Builds on the v1 contracts from S01 (entity_id/legacy_ids,
status: merged/superseded) and detection-only duplicate-finding that
already exists in app/network_index.find_potential_duplicates. This module
adds the missing piece: an actual merge operation -- but only ever
triggered by an explicit human decision, never automatically, and always
reversible (per ADR-009: "merging never deletes a record, it marks the
losing side and points at the survivor").

Nothing here writes to disk. These are pure functions over in-memory v1
dicts; wiring into ArtifactStore-backed persistence is Epic 02 S06's
migration/backfill work.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Literal

ProposalStatus = Literal["pending_review", "accepted", "rejected"]


class IdentityResolutionError(RuntimeError):
    pass


@dataclass(frozen=True)
class MergeProposal:
    proposal_id: str
    survivor_entity_id: str
    candidate_entity_id: str
    confidence: float
    evidence: list[str]
    status: ProposalStatus = "pending_review"


def propose_merge(
    survivor: dict[str, Any],
    candidate: dict[str, Any],
    *,
    evidence: list[str],
    confidence: float,
) -> MergeProposal:
    """Create a pending merge proposal for two v1 entity records.

    Never mutates either record. A proposal is not a merge -- it only
    becomes one via ``accept_merge`` below, and only a human decision
    (``reviewed_by``) can produce that call.
    """

    if survivor["entity_id"] == candidate["entity_id"]:
        raise IdentityResolutionError("cannot propose merging an entity with itself")
    if not 0.0 <= confidence <= 1.0:
        raise IdentityResolutionError("confidence must be within [0, 1]")
    if not evidence:
        raise IdentityResolutionError("a merge proposal requires at least one evidence reference")
    return MergeProposal(
        proposal_id=f"mergeprop_{uuid.uuid4().hex}",
        survivor_entity_id=survivor["entity_id"],
        candidate_entity_id=candidate["entity_id"],
        confidence=confidence,
        evidence=list(evidence),
    )


@dataclass(frozen=True)
class MergeDecision:
    proposal_id: str
    survivor_entity_id: str
    candidate_entity_id: str
    decision: Literal["accepted", "rejected"]
    reviewed_by: str
    reviewed_at: str
    rationale: str


def decide_merge(
    proposal: MergeProposal,
    *,
    decision: Literal["accepted", "rejected"],
    reviewed_by: str,
    rationale: str,
) -> MergeDecision:
    """Record a human's decision on a proposal. This is the only path that
    can lead to entities actually being merged -- see ``apply_accepted_merge``.
    """

    if not reviewed_by.strip():
        raise IdentityResolutionError("a merge decision requires a named reviewer -- no anonymous merges")
    return MergeDecision(
        proposal_id=proposal.proposal_id,
        survivor_entity_id=proposal.survivor_entity_id,
        candidate_entity_id=proposal.candidate_entity_id,
        decision=decision,
        reviewed_by=reviewed_by,
        reviewed_at=datetime.now(timezone.utc).isoformat(),
        rationale=rationale,
    )


def apply_accepted_merge(
    survivor: dict[str, Any],
    candidate: dict[str, Any],
    *,
    decision: MergeDecision,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Apply an accepted merge decision, returning (updated_survivor, updated_candidate).

    Neither input dict is mutated in place; new dicts are returned. The
    candidate ("loser") is never deleted: it is marked status=merged and
    points at the survivor. The survivor absorbs the candidate's
    legacy_ids so every legacy record that resolved to either entity now
    resolves, through legacy_ids, to one canonical entity_id.
    """

    if decision.decision != "accepted":
        raise IdentityResolutionError("apply_accepted_merge requires an accepted decision")
    if decision.candidate_entity_id != candidate["entity_id"] or decision.survivor_entity_id != survivor["entity_id"]:
        raise IdentityResolutionError("decision does not match the supplied survivor/candidate pair")

    updated_survivor = dict(survivor)
    updated_survivor["legacy_ids"] = sorted(set(survivor["legacy_ids"]) | set(candidate["legacy_ids"]))

    updated_candidate = dict(candidate)
    updated_candidate["status"] = "merged"
    updated_candidate["merged_into_entity_id"] = survivor["entity_id"]

    return updated_survivor, updated_candidate


def reverse_merge(
    survivor: dict[str, Any],
    merged_candidate: dict[str, Any],
    *,
    original_candidate_legacy_ids: list[str],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Undo a merge: the candidate is restored to active/unmerged, and the
    survivor's legacy_ids shrink back to exclude what the candidate
    brought in. This is what "réversible" means in the Epic 02 S03 stop
    condition -- a merge is never a one-way door.
    """

    if merged_candidate.get("status") != "merged":
        raise IdentityResolutionError("only a merged record can be reversed")

    restored_candidate = dict(merged_candidate)
    restored_candidate["status"] = "active"
    restored_candidate["merged_into_entity_id"] = None
    restored_candidate["legacy_ids"] = list(original_candidate_legacy_ids)

    updated_survivor = dict(survivor)
    updated_survivor["legacy_ids"] = sorted(set(survivor["legacy_ids"]) - set(original_candidate_legacy_ids))

    return updated_survivor, restored_candidate
