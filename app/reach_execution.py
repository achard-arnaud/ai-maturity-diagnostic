"""Epic 09 S06: prepare/approve/send execution, and the "my day"
projection. Stop condition: "opérable sans fichiers" (operable without
files) -- the whole prepare -> approve -> send loop, and the queue a
user works from, must be driven entirely through these functions
(and the routes/store built on top of them), never by hand-editing
JSONL files.
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from app.reach_channel_policy import assert_channel_authorized_to_send, assert_no_implicit_creation_as_sent
from app.reach_queue import build_priority_queue


def prepare_touchpoint(step: Mapping[str, Any], *, message: Mapping[str, Any], touchpoint_id: str) -> dict[str, Any]:
    """Turn an approved message into a prepared (never pre-sent)
    Touchpoint for a step."""
    if message["status"] != "approved":
        raise ValueError(f"cannot prepare a touchpoint from a message in status={message['status']!r}")
    touchpoint = {
        "touchpoint_id": touchpoint_id,
        "step_id": step["step_id"],
        "channel": step["channel"],
        "content_ref": message.get("content", ""),
        "status": "prepared",
        "sent_at": None,
        "sent_by": None,
    }
    assert_no_implicit_creation_as_sent(touchpoint, record_kind="touchpoint")
    return touchpoint


def send_touchpoint(touchpoint: Mapping[str, Any], *, sent_by: str, sent_at: str) -> dict[str, Any]:
    """Mark a prepared touchpoint sent -- always a distinct, later,
    explicitly-audited action, and always refused on a channel that
    isn't authorized to send (LinkedIn, absent a dedicated ADR)."""
    if touchpoint["status"] != "prepared":
        raise ValueError(f"cannot send a touchpoint in status={touchpoint['status']!r}")
    assert_channel_authorized_to_send(touchpoint["channel"])
    updated = dict(touchpoint)
    updated["status"] = "sent"
    updated["sent_at"] = sent_at
    updated["sent_by"] = sent_by
    return updated


def build_my_day(
    assignee: str,
    *,
    tasks: Sequence[Mapping[str, Any]],
    sequences_by_id: Mapping[str, Mapping[str, Any]],
    now: str,
) -> list[dict[str, Any]]:
    """The single queue a user works from: their own open tasks, only
    from sequences that are still active/paused (never from a
    cancelled or completed sequence), in the same deterministic
    priority order as the underlying execution queue."""
    own_tasks = [
        t for t in tasks
        if t["assignee"] == assignee and sequences_by_id.get(t["sequence_id"], {}).get("status") in ("active", "paused")
    ]
    queue = build_priority_queue(own_tasks, now=now)
    tasks_by_id = {t["task_id"]: t for t in own_tasks}
    return [
        {
            "task_id": entry.task_id,
            "priority": entry.priority,
            "due_at": entry.due_at,
            "overdue": entry.overdue,
            "sequence_id": tasks_by_id[entry.task_id]["sequence_id"],
        }
        for entry in queue
    ]
