"""Explicit Signal -> ResearchQueued handoff (Epic 03 S06).

Per the lifecycle doc's handoff rule ("ResearchCompleted peut creer/
proposer une Demand, jamais un Fit"), the symmetric rule for this Epic is:
a Signal can only ever hand off into research priority (a ResearchQueued
event), never directly into a Demand or a Fit -- those don't exist as
objects a signal can reach; only Epic 04's ResearchCase, built from this
event, may later propose a Demand.

This module does not create a ResearchCase (that object belongs to
Epic 04, not yet built) -- it appends a ResearchQueued event to Epic 01's
EventJournal, which is exactly the "handoff is an explicit event" pattern
03_GTM_LIFECYCLE_AND_STATE_MACHINES.md specifies. Epic 04 S02's queue
consumes these events; this Sprint only proves the handoff itself is
sound and gated correctly.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.event_journal import EventJournal
from app.signal_policy import assert_no_demand_fields


class SignalHandoffError(RuntimeError):
    pass


def queue_research(
    root: Path,
    signal: dict[str, Any],
    *,
    requested_by: str,
) -> dict[str, Any]:
    """Hand a signal off to research priority. Requires the signal to
    already be `linked` to a company (i.e. reviewed and connected, not a
    raw unreviewed signal) -- queuing research from an unreviewed signal
    would defeat the point of the review step Epic 03's lifecycle exists
    for.
    """

    if signal["status"] != "linked":
        raise SignalHandoffError(
            f"signal {signal['signal_id']} has status {signal['status']!r}; "
            "only a linked signal (reviewed and connected to a company) can be queued for research"
        )
    if not signal.get("company_entity_id"):
        raise SignalHandoffError(f"signal {signal['signal_id']} is linked but has no company_entity_id")
    if not requested_by.strip():
        raise SignalHandoffError("requested_by is required -- no anonymous handoffs")

    handoff_data = {
        "signal_id": signal["signal_id"],
        "company_entity_id": signal["company_entity_id"],
        "requested_by": requested_by,
    }
    # Defense-in-depth: the handoff payload itself must never carry a
    # demand-only field, exactly like the signal it comes from.
    assert_no_demand_fields(handoff_data)

    journal = EventJournal(root)
    return journal.append(
        "ResearchQueued",
        workspace_id=signal["workspace_id"],
        actor_id=requested_by,
        object_ref=f"signal:{signal['signal_id']}",
        data=handoff_data,
        idempotency_key=f"research-queued:{signal['signal_id']}",
    )
