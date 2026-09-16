"""Epic 10 S01: Conversation/EngagementEvent/Objection policy.

Stop condition: "outbound ≠ engagement" -- sending a Touchpoint (Epic
09) proves outreach happened, never that the recipient responded. An
EngagementEvent can only ever be constructed from an inbound-originated
signal; there is no path that lets a send itself count as engagement.
"""

from __future__ import annotations

from typing import Any

ENGAGEMENT_KINDS = frozenset({"replied", "meeting_booked", "opted_out", "bounced"})


class EngagementPolicyError(Exception):
    pass


class NotEngagementError(EngagementPolicyError):
    pass


def is_engagement_kind(kind: str) -> bool:
    return kind in ENGAGEMENT_KINDS


def create_engagement_event(
    *,
    engagement_event_id: str,
    conversation_id: str,
    kind: str,
    channel: str,
    occurred_at: str,
    source_ref: str,
    touchpoint_id: str | None = None,
    raw_ref: str | None = None,
) -> dict[str, Any]:
    """The sole constructor for an EngagementEvent. Refuses outright if
    `kind` is not an inbound-originated signal -- a Touchpoint's own
    `sent` status (Epic 09) is never wrapped into this model."""
    if not is_engagement_kind(kind):
        raise NotEngagementError(
            f"{kind!r} is not an inbound engagement signal -- a send is tracked on the Touchpoint itself, "
            "never recorded as an EngagementEvent"
        )
    return {
        "engagement_event_id": engagement_event_id,
        "conversation_id": conversation_id,
        "touchpoint_id": touchpoint_id,
        "kind": kind,
        "channel": channel,
        "occurred_at": occurred_at,
        "source_ref": source_ref,
        "raw_ref": raw_ref,
    }


def open_conversation(
    *,
    conversation_id: str,
    workspace_id: str,
    target_plan_id: str,
    stakeholder_role_id: str,
    created_at: str,
    sequence_id: str | None = None,
) -> dict[str, Any]:
    return {
        "conversation_id": conversation_id,
        "workspace_id": workspace_id,
        "target_plan_id": target_plan_id,
        "stakeholder_role_id": stakeholder_role_id,
        "sequence_id": sequence_id,
        "status": "open",
        "created_at": created_at,
    }


def close_conversation(conversation: dict[str, Any]) -> dict[str, Any]:
    if conversation["status"] != "open":
        raise EngagementPolicyError(f"cannot close a conversation in status={conversation['status']!r}")
    updated = dict(conversation)
    updated["status"] = "closed"
    return updated
