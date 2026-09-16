"""Epic 11 S03: bounded discovery notes and append-only decisions."""

from __future__ import annotations

from typing import Mapping

MAX_DISCOVERY_SUMMARY_CHARS = 4000
MAX_DECISION_RATIONALE_CHARS = 2000
NOTE_ROLES = frozenset({"commercial_reviewer", "admin"})
DECISION_ROLES = frozenset({"commercial_decider", "admin"})


class CommercialNoteError(ValueError):
    pass


class CommercialAccessError(PermissionError):
    pass


def create_discovery_note(
    *, discovery_note_id: str, workspace_id: str, opportunity_id: str, conversation_id: str, author_id: str,
    actor_role: str, occurred_at: str, summary: str, evidence_refs: list[str], created_at: str,
) -> dict:
    """Create a bounded, provenance-required note without modifying its inputs."""
    if actor_role not in NOTE_ROLES:
        raise CommercialAccessError("creating a discovery note requires a commercial_reviewer role")
    if not summary.strip() or len(summary) > MAX_DISCOVERY_SUMMARY_CHARS:
        raise CommercialNoteError("discovery summary must be between 1 and 4000 characters")
    if not evidence_refs or any(not ref.strip() for ref in evidence_refs):
        raise CommercialNoteError("discovery notes require at least one evidence reference")
    return {
        "discovery_note_id": discovery_note_id, "workspace_id": workspace_id, "opportunity_id": opportunity_id,
        "conversation_id": conversation_id, "author_id": author_id, "occurred_at": occurred_at,
        "summary": summary, "evidence_refs": list(evidence_refs), "created_at": created_at,
    }


def record_commercial_decision(
    *, commercial_decision_id: str, workspace_id: str, opportunity_id: str, decision: str, rationale: str,
    evidence_refs: list[str], decided_by: str, actor_role: str, decided_at: str,
) -> dict:
    """Build an attributed decision record. Existing records are never updated."""
    if actor_role not in DECISION_ROLES:
        raise CommercialAccessError("recording a commercial decision requires a commercial_decider role")
    if decision not in {"advance", "hold", "stop"}:
        raise CommercialNoteError(f"unknown commercial decision {decision!r}")
    if not rationale.strip() or len(rationale) > MAX_DECISION_RATIONALE_CHARS:
        raise CommercialNoteError("decision rationale must be between 1 and 2000 characters")
    if not evidence_refs or any(not ref.strip() for ref in evidence_refs):
        raise CommercialNoteError("commercial decisions require at least one evidence reference")
    return {
        "commercial_decision_id": commercial_decision_id, "workspace_id": workspace_id,
        "opportunity_id": opportunity_id, "decision": decision, "rationale": rationale,
        "evidence_refs": list(evidence_refs), "decided_by": decided_by, "decided_at": decided_at,
    }


def validate_note_opportunity_workspace(note: Mapping[str, object], opportunity: Mapping[str, object]) -> None:
    """Reject a note that attempts to cross workspace boundaries."""
    if note["workspace_id"] != opportunity["workspace_id"] or note["opportunity_id"] != opportunity["opportunity_id"]:
        raise CommercialNoteError("notes must reference an opportunity in the same workspace")
