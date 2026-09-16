"""Epic 10 S04: inbox, follow-up, stop-sequence, next action.

Stop condition: "réponse agit sur reach" (a reply acts on reach) -- an
inbound EngagementEvent must actually pause or cancel the Reach
sequence it correlates to, not just get logged as a passive record.
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from app.reach_queue import cancel_sequence, pause_sequence

_ACTION_FOR_KIND: dict[str, str] = {
    "replied": "pause_sequence",
    "meeting_booked": "pause_sequence",
    "bounced": "pause_sequence",
    "opted_out": "cancel_sequence",
}

_ALREADY_STOPPED_STATUSES = frozenset({"paused", "cancelled", "completed"})


class EngagementInboxError(Exception):
    pass


def next_action_for_kind(kind: str) -> str:
    if kind not in _ACTION_FOR_KIND:
        raise EngagementInboxError(f"no next action defined for engagement kind {kind!r}")
    return _ACTION_FOR_KIND[kind]


def apply_engagement_to_sequence(
    event: Mapping[str, Any],
    sequence: Mapping[str, Any],
    *,
    tasks: Sequence[Mapping[str, Any]] = (),
    steps: Sequence[Mapping[str, Any]] = (),
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], str]:
    """The sole function that lets an inbound EngagementEvent act on a
    Reach sequence. Returns (updated_sequence, updated_tasks,
    updated_steps, action_taken). Idempotent: re-applying an event
    against an already-stopped sequence is a no-op, never an error."""
    action = next_action_for_kind(event["kind"])
    if action == "cancel_sequence":
        if sequence["status"] == "cancelled":
            return dict(sequence), list(tasks), list(steps), "already_cancelled"
        new_sequence, new_tasks, new_steps = cancel_sequence(sequence, tasks=tasks, steps=steps)
        return new_sequence, new_tasks, new_steps, "cancelled"
    if action == "pause_sequence":
        if sequence["status"] in _ALREADY_STOPPED_STATUSES:
            return dict(sequence), list(tasks), list(steps), "no_op"
        return pause_sequence(sequence), list(tasks), list(steps), "paused"
    raise EngagementInboxError(f"unhandled action {action!r}")


def build_engagement_inbox(
    conversations: Sequence[Mapping[str, Any]],
    events: Sequence[Mapping[str, Any]],
    objections: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Deterministic follow-up inbox: open conversations that have at
    least one objection still needing human review, oldest conversation
    first."""
    from app.engagement_classification import needs_human_review

    conversation_id_by_event_id = {e["engagement_event_id"]: e["conversation_id"] for e in events}
    pending_conversation_ids = {
        conversation_id_by_event_id[o["engagement_event_id"]]
        for o in objections
        if needs_human_review(o) and o["engagement_event_id"] in conversation_id_by_event_id
    }
    inbox = [
        dict(c) for c in conversations
        if c["status"] == "open" and c["conversation_id"] in pending_conversation_ids
    ]
    inbox.sort(key=lambda c: c["created_at"])
    return inbox
