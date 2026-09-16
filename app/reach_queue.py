"""Epic 09 S03: execution queue, priorities, SLA, pause/cancel.

Stop condition: "retry sans doublon" (retry without duplication) -- a
retry attempt on a task/step must never create a second in-flight
attempt for the same unit of work; pausing or cancelling a sequence
must cascade deterministically to its still-pending tasks and steps
without touching anything already sent/done.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

_TERMINAL_TASK_STATUSES = frozenset({"done", "skipped"})
_TERMINAL_STEP_STATUSES = frozenset({"sent", "skipped", "cancelled"})
_ACTIVE_SEQUENCE_STATUSES = frozenset({"active", "paused"})


class ReachQueueError(Exception):
    pass


class DuplicateRetryError(ReachQueueError):
    pass


class InvalidTransitionError(ReachQueueError):
    pass


@dataclass(frozen=True)
class QueueEntry:
    task_id: str
    priority: int
    due_at: str
    overdue: bool


def build_priority_queue(tasks: Sequence[Mapping[str, Any]], *, now: str) -> list[QueueEntry]:
    """Order open tasks by (overdue first, priority desc, due_at asc,
    task_id asc) for a deterministic, stable queue regardless of input
    order. Terminal tasks (done/skipped) are excluded."""
    entries = [
        QueueEntry(
            task_id=task["task_id"],
            priority=task.get("priority", 0),
            due_at=task["due_at"],
            overdue=task["due_at"] < now,
        )
        for task in tasks
        if task["status"] not in _TERMINAL_TASK_STATUSES
    ]
    entries.sort(key=lambda e: (not e.overdue, -e.priority, e.due_at, e.task_id))
    return entries


def retry_step(step: Mapping[str, Any], *, attempts: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Return a new retry attempt record for a step, refusing to create
    a duplicate if an attempt is already in-flight (status in
    prepared/sent) for this step."""
    if step["status"] in _TERMINAL_STEP_STATUSES:
        raise InvalidTransitionError(f"cannot retry a step in terminal status {step['status']!r}")
    in_flight = [a for a in attempts if a["step_id"] == step["step_id"] and a["status"] in ("prepared", "sent")]
    if in_flight:
        raise DuplicateRetryError(
            f"step {step['step_id']!r} already has an in-flight attempt -- retry must not duplicate it"
        )
    return {"step_id": step["step_id"], "status": "prepared", "attempt_number": len(attempts) + 1}


def pause_sequence(sequence: Mapping[str, Any]) -> dict[str, Any]:
    if sequence["status"] != "active":
        raise InvalidTransitionError(f"can only pause an active sequence, got status={sequence['status']!r}")
    updated = dict(sequence)
    updated["status"] = "paused"
    return updated


def resume_sequence(sequence: Mapping[str, Any]) -> dict[str, Any]:
    if sequence["status"] != "paused":
        raise InvalidTransitionError(f"can only resume a paused sequence, got status={sequence['status']!r}")
    updated = dict(sequence)
    updated["status"] = "active"
    return updated


def cancel_sequence(
    sequence: Mapping[str, Any],
    *,
    tasks: Sequence[Mapping[str, Any]],
    steps: Sequence[Mapping[str, Any]],
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    """Cancel a sequence and cascade to its still-open tasks/steps.
    Tasks/steps already terminal (done/skipped/sent/cancelled) are left
    untouched -- cancellation never rewrites history."""
    if sequence["status"] not in _ACTIVE_SEQUENCE_STATUSES and sequence["status"] != "draft":
        raise InvalidTransitionError(f"cannot cancel a sequence already status={sequence['status']!r}")
    updated_sequence = dict(sequence)
    updated_sequence["status"] = "cancelled"

    updated_tasks = []
    for task in tasks:
        if task["status"] in _TERMINAL_TASK_STATUSES:
            updated_tasks.append(dict(task))
        else:
            new_task = dict(task)
            new_task["status"] = "skipped"
            updated_tasks.append(new_task)

    updated_steps = []
    for step in steps:
        if step["status"] in _TERMINAL_STEP_STATUSES:
            updated_steps.append(dict(step))
        else:
            new_step = dict(step)
            new_step["status"] = "cancelled"
            updated_steps.append(new_step)

    return updated_sequence, updated_tasks, updated_steps


def is_task_overdue(task: Mapping[str, Any], *, now: str) -> bool:
    return task["status"] not in _TERMINAL_TASK_STATUSES and task["due_at"] < now
