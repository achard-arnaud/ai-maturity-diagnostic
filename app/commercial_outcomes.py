"""Epic 11 S06: terminal outcomes, expansion eligibility and learning events."""

from __future__ import annotations


class CommercialOutcomeError(ValueError):
    pass


def record_loss(*, opportunity_id: str, reason: str, decided_at: str) -> dict:
    if not reason.strip():
        raise CommercialOutcomeError("a lost opportunity requires a loss reason")
    return {"opportunity_id": opportunity_id, "outcome": "lost", "reason": reason, "decided_at": decided_at}


def create_expansion(*, expansion_id: str, deal: dict, created_at: str) -> dict:
    if deal["status"] != "won":
        raise CommercialOutcomeError("expansion requires a won deal")
    return {"expansion_id": expansion_id, "workspace_id": deal["workspace_id"], "deal_id": deal["deal_id"], "status": "identified", "created_at": created_at, "updated_at": None}


def create_learning_event(*, event_id: str, workspace_id: str, opportunity_id: str, outcome: str, signal: str, created_at: str) -> dict:
    if outcome not in {"won", "lost", "expanded"}:
        raise CommercialOutcomeError("learning event requires a terminal commercial outcome")
    if not signal.strip():
        raise CommercialOutcomeError("learning event requires an observed signal")
    return {"learning_event_id": event_id, "workspace_id": workspace_id, "opportunity_id": opportunity_id, "outcome": outcome, "signal": signal, "created_at": created_at}
