"""Epic 10 S02: manual/import ingestion, dedup and touchpoint
correlation. Stop condition: "events idempotents" -- re-ingesting the
same raw record (identified by its source_ref) must never create a
second EngagementEvent; ingestion is safe to retry or re-run an import
file without duplicating history.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from app.engagement_policy import create_engagement_event


class EngagementIngestionError(Exception):
    pass


@dataclass(frozen=True)
class IngestResult:
    event: dict[str, Any]
    created: bool


def ingest_engagement_event(
    *,
    engagement_event_id: str,
    conversation_id: str,
    kind: str,
    channel: str,
    occurred_at: str,
    source_ref: str,
    existing_events: Sequence[Mapping[str, Any]],
    touchpoint_id: str | None = None,
    raw_ref: str | None = None,
) -> IngestResult:
    """The sole ingestion entry point. Looks up `source_ref` among
    already-ingested events first -- a match is returned as-is
    (created=False), never re-created, so ingestion is idempotent
    under retries or a re-run import file."""
    for existing in existing_events:
        if existing["source_ref"] == source_ref:
            return IngestResult(event=dict(existing), created=False)
    event = create_engagement_event(
        engagement_event_id=engagement_event_id,
        conversation_id=conversation_id,
        kind=kind,
        channel=channel,
        occurred_at=occurred_at,
        source_ref=source_ref,
        touchpoint_id=touchpoint_id,
        raw_ref=raw_ref,
    )
    return IngestResult(event=event, created=True)


def ingest_batch(
    raw_records: Sequence[Mapping[str, Any]], *, existing_events: Sequence[Mapping[str, Any]],
) -> list[IngestResult]:
    """Ingest a batch (e.g. one import file), each record checked
    against both already-stored events and every record already
    processed earlier in this same batch -- a batch containing the
    same source_ref twice still yields exactly one created event."""
    seen = list(existing_events)
    results: list[IngestResult] = []
    for record in raw_records:
        result = ingest_engagement_event(existing_events=seen, **record)
        results.append(result)
        if result.created:
            seen.append(result.event)
    return results


def correlate_touchpoint(
    *,
    channel: str,
    occurred_at: str,
    candidate_touchpoints: Sequence[Mapping[str, Any]],
) -> str | None:
    """Best-effort correlation to the outbound Touchpoint an inbound
    signal is most likely replying to: the most recently sent
    touchpoint on the same channel, sent at or before the event's
    occurred_at. Returns None (never a guess) if no candidate
    qualifies."""
    candidates = [
        tp for tp in candidate_touchpoints
        if tp["channel"] == channel and tp["status"] == "sent" and tp["sent_at"] is not None
        and tp["sent_at"] <= occurred_at
    ]
    if not candidates:
        return None
    candidates.sort(key=lambda tp: tp["sent_at"], reverse=True)
    return candidates[0]["touchpoint_id"]
