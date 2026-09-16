"""Epic 10 S05: opportunity proposal from positive engagement.

A meeting_booked signal is strong enough to propose advancing the
buying process -- but it only ever proposes; nothing here creates or
mutates a TargetPlan/FitAssessment on its own.
"""

from __future__ import annotations

from typing import Any, Mapping


def propose_opportunity(event: Mapping[str, Any]) -> dict[str, Any] | None:
    """Returns a proposal record for a meeting_booked event, None for
    anything else -- never a guess, never auto-applied."""
    if event["kind"] != "meeting_booked":
        return None
    return {
        "conversation_id": event["conversation_id"],
        "engagement_event_id": event["engagement_event_id"],
        "reason": "meeting_booked",
        "status": "proposed",
    }
