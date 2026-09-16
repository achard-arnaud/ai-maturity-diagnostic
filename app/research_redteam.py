"""Epic 04 S04: contradiction/falsifier/side-story bounded workflows.

Per 08_EVIDENCE_DECISION_AND_GATES.md's "Red-team fonctionnel": every
major decision must look for an alternative explanation, a falsifier,
contradictory evidence, and an unresolved dependency. A "side story" is a
bounded investigation opened to chase one of those -- bounded meaning it
always carries an owner and can only ever close by reconnecting to the
claim it branched from (the "trunk"), never by silently vanishing.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence


class SideStoryError(Exception):
    pass


def open_side_story(
    parent_claim_id: str,
    question: str,
    *,
    owner: str,
    opened_at: str,
    side_story_id: str,
    research_case_id: str,
) -> dict:
    if not owner:
        raise SideStoryError("a side story must have an owner (bounded workflow)")
    return {
        "side_story_id": side_story_id,
        "research_case_id": research_case_id,
        "parent_claim_id": parent_claim_id,
        "question": question,
        "status": "open",
        "owner": owner,
        "opened_at": opened_at,
        "resolution_claim_id": None,
        "resolved_at": None,
        "dismissal_reason": None,
    }


def resolve_side_story(side_story: Mapping, resolution_claim: Mapping, *, resolved_at: str) -> dict:
    """Close a side story by linking it to a claim that reconnects to the
    trunk -- the resolution claim must either supersede the parent claim,
    or explicitly derive from it. A resolution claim with no link back to
    parent_claim_id is rejected: a side story branch must reconnect, never
    dangle disconnected from the claim it was opened to investigate.
    """
    if side_story["status"] != "open":
        raise SideStoryError(f"cannot resolve a side story with status {side_story['status']!r}")

    parent_id = side_story["parent_claim_id"]
    linked = (
        resolution_claim.get("supersedes_claim_id") == parent_id
        or parent_id in resolution_claim.get("derived_from_claim_ids", [])
    )
    if not linked:
        raise SideStoryError(
            "resolution claim does not reconnect to the trunk claim "
            f"{parent_id!r} (branches reliées au tronc)"
        )

    updated = dict(side_story)
    updated["status"] = "resolved"
    updated["resolution_claim_id"] = resolution_claim["claim_id"]
    updated["resolved_at"] = resolved_at
    return updated


def dismiss_side_story(side_story: Mapping, reason: str, *, dismissed_at: str) -> dict:
    if side_story["status"] != "open":
        raise SideStoryError(f"cannot dismiss a side story with status {side_story['status']!r}")
    if not reason:
        raise SideStoryError("dismissing a side story requires a reason")
    updated = dict(side_story)
    updated["status"] = "dismissed"
    updated["dismissal_reason"] = reason
    updated["resolved_at"] = dismissed_at
    return updated


def find_contradictions(claims: Sequence[Mapping]) -> list[tuple[str, str]]:
    """Return (claim_id, contradicting_claim_id) pairs from claims'
    contradicted_by_claim_ids, only among currently active claims."""
    active_ids = {c["claim_id"] for c in claims if c.get("status") == "active"}
    pairs: list[tuple[str, str]] = []
    for claim in claims:
        if claim.get("status") != "active":
            continue
        for other_id in claim.get("contradicted_by_claim_ids", []):
            if other_id in active_ids:
                pairs.append((claim["claim_id"], other_id))
    return pairs


@dataclass(frozen=True)
class RedTeamChecklist:
    claim_id: str
    has_contradictory_evidence: bool
    has_open_side_story: bool
    has_unresolved_dependency: bool


def run_redteam_checklist(
    claim: Mapping,
    *,
    evidence_by_id: Mapping[str, Mapping],
    side_stories: Sequence[Mapping],
) -> RedTeamChecklist:
    """Per-claim checklist covering 3 of the doc's 4 red-team angles
    (contradictory evidence, an open side story chasing an alternative
    explanation/falsifier, an unresolved dependency == any open side
    story on this claim that hasn't reconnected yet)."""
    claim_id = claim["claim_id"]

    has_contradictory_evidence = any(
        claim_id in evidence.get("contests_claim_ids", []) for evidence in evidence_by_id.values()
    )
    relevant_side_stories = [s for s in side_stories if s["parent_claim_id"] == claim_id]
    has_open_side_story = any(s["status"] == "open" for s in relevant_side_stories)

    return RedTeamChecklist(
        claim_id=claim_id,
        has_contradictory_evidence=has_contradictory_evidence,
        has_open_side_story=has_open_side_story,
        has_unresolved_dependency=has_open_side_story,
    )
