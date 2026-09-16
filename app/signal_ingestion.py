"""Signal ingestion adapters: public, manual, import (Epic 03 S02).

Stop condition is "core sans integration": every adapter here takes
already-obtained content as input (a URL + text already fetched, an
operator's manual note, a batch of pre-parsed rows) rather than reaching
out to a live external service itself. Wiring a real live fetch/premium
connector behind the "public" adapter is explicitly deferred work (see
EPIC_03_SIGNAL_BASED_DISCOVER.md's "Deferred work: sources premium/
connecteurs") -- this Sprint's job is that the core ingestion path (schema
+ dedup + provenance + demand-contamination guard) works correctly and is
fully testable without any such integration existing.

Every adapter produces a CanonicalSignalV1-shaped dict (validated against
contracts/signal_v1.schema.yaml by the caller/tests) via
app.signal_policy, so ingestion and the storage/lifecycle layer never
diverge on shape.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from app.signal_policy import assert_no_demand_fields, compute_dedup_key


class SignalIngestionError(RuntimeError):
    pass


def _new_signal_id() -> str:
    return f"signal_{uuid.uuid4().hex}"


def _base_signal(
    *,
    workspace_id: str,
    source_kind: str,
    source_ref: str,
    content: str,
    observed_at: str,
    stale_after_days: int,
    evidence_grade: str,
    epistemic_status: str,
) -> dict[str, Any]:
    if not workspace_id.strip():
        raise SignalIngestionError("workspace_id is required")
    if not content.strip():
        raise SignalIngestionError("content is required to compute a dedup key and provenance")

    signal = {
        "signal_id": _new_signal_id(),
        "workspace_id": workspace_id,
        "source": {"kind": source_kind, "ref": source_ref},
        "observed_at": observed_at,
        "status": "new",
        "company_entity_id": None,
        "dedup_key": compute_dedup_key(source_kind, source_ref, content),
        "freshness": {"stale_after_days": stale_after_days},
        "provenance": {
            "source_refs": [source_ref],
            "epistemic_status": epistemic_status,
            "evidence_grade": evidence_grade,
        },
    }
    assert_no_demand_fields(signal)
    return signal


def ingest_public(
    workspace_id: str,
    *,
    url: str,
    content: str,
    fetched_at: str | None = None,
    stale_after_days: int = 14,
) -> dict[str, Any]:
    """A publicly-sourced signal. `content` is text already obtained by the
    caller (this Sprint does not fetch it) -- see module docstring.
    """

    if not url.strip():
        raise SignalIngestionError("a public signal requires a URL")
    observed_at = fetched_at or datetime.now(timezone.utc).isoformat()
    return _base_signal(
        workspace_id=workspace_id,
        source_kind="public",
        source_ref=url,
        content=content,
        observed_at=observed_at,
        stale_after_days=stale_after_days,
        evidence_grade="U1",
        epistemic_status="inference",
    )


def ingest_manual(
    workspace_id: str,
    *,
    operator: str,
    note: str,
    observed_at: str | None = None,
    stale_after_days: int = 30,
) -> dict[str, Any]:
    """An operator-entered signal (e.g. something heard in a call).
    `operator` becomes part of the source ref so two operators noting the
    same underlying event at different times don't collide on dedup.
    """

    if not operator.strip():
        raise SignalIngestionError("a manual signal requires the operator's identity")
    observed_at = observed_at or datetime.now(timezone.utc).isoformat()
    return _base_signal(
        workspace_id=workspace_id,
        source_kind="manual",
        source_ref=f"operator:{operator}",
        content=note,
        observed_at=observed_at,
        stale_after_days=stale_after_days,
        evidence_grade="U1",
        epistemic_status="hypothesis",
    )


def ingest_import(
    workspace_id: str,
    *,
    batch_ref: str,
    rows: list[dict[str, str]],
    stale_after_days: int = 60,
) -> list[dict[str, Any]]:
    """A batch import (e.g. a CSV of pre-collected signals). Each row must
    have "content" and "observed_at"; a malformed row fails the whole
    batch rather than silently skipping it, so a partial/corrupt import
    is never promoted as if it were complete.
    """

    if not batch_ref.strip():
        raise SignalIngestionError("an import batch requires a batch_ref")
    if not rows:
        raise SignalIngestionError("an import batch requires at least one row")

    signals: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        content = row.get("content", "").strip()
        observed_at = row.get("observed_at", "").strip()
        if not content:
            raise SignalIngestionError(f"import row {index} is missing content")
        if not observed_at:
            raise SignalIngestionError(f"import row {index} is missing observed_at")
        signals.append(
            _base_signal(
                workspace_id=workspace_id,
                source_kind="import",
                source_ref=f"{batch_ref}#{index}",
                content=content,
                observed_at=observed_at,
                stale_after_days=stale_after_days,
                evidence_grade="U1",
                epistemic_status="unknown",
            )
        )
    return signals
