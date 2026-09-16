"""Append-only technical event journal with idempotency and hash chaining.

Events describe platform mutations and execution lifecycle. They do not replace
the canonical business artifacts referenced by ``object_ref``.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from app.artifact_store import ArtifactStore
from app.execution_context import current_correlation_id


class EventJournalError(RuntimeError):
    pass


class EventJournalIntegrityError(EventJournalError):
    pass


def _canonical(data: dict[str, Any]) -> bytes:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


@dataclass(frozen=True)
class EventJournal:
    root: Path
    relative_path: str = "events/platform.jsonl"

    @property
    def path(self) -> Path:
        return self.root / self.relative_path

    def replay(self, *, verify: bool = True) -> Iterator[dict[str, Any]]:
        if not self.path.is_file():
            return
        previous_hash: str | None = None
        for line_number, raw in enumerate(self.path.read_text(encoding="utf-8").splitlines(), start=1):
            if not raw.strip():
                continue
            try:
                event = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise EventJournalIntegrityError(f"invalid event JSON at line {line_number}") from exc
            if verify:
                claimed_hash = event.get("event_hash")
                body = dict(event)
                body.pop("event_hash", None)
                actual_hash = hashlib.sha256(_canonical(body)).hexdigest()
                if claimed_hash != actual_hash:
                    raise EventJournalIntegrityError(f"event hash mismatch at line {line_number}")
                if event.get("previous_hash") != previous_hash:
                    raise EventJournalIntegrityError(f"event chain mismatch at line {line_number}")
                previous_hash = claimed_hash
            yield event

    def find_by_idempotency_key(self, key: str) -> dict[str, Any] | None:
        for event in self.replay():
            if event.get("idempotency_key") == key:
                return event
        return None

    def append(
        self,
        event_type: str,
        *,
        workspace_id: str,
        actor_id: str,
        object_ref: str | None = None,
        data: dict[str, Any] | None = None,
        correlation_id: str | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        if not event_type.strip():
            raise EventJournalError("event_type is required")
        selected: dict[str, Any] = {}

        def append_to(previous: bytes) -> bytes:
            nonlocal selected
            events: list[dict[str, Any]] = []
            previous_hash: str | None = None
            for line_number, raw in enumerate(previous.decode("utf-8").splitlines(), start=1):
                if not raw.strip():
                    continue
                event = json.loads(raw)
                claimed_hash = event.get("event_hash")
                body = dict(event)
                body.pop("event_hash", None)
                if claimed_hash != hashlib.sha256(_canonical(body)).hexdigest() or event.get("previous_hash") != previous_hash:
                    raise EventJournalIntegrityError(f"event chain mismatch at line {line_number}")
                if idempotency_key and event.get("idempotency_key") == idempotency_key:
                    selected = event
                    return previous
                previous_hash = claimed_hash
                events.append(event)
            selected = {
                "event_id": f"evt_{uuid.uuid4().hex}",
                "event_type": event_type,
                "occurred_at": datetime.now(timezone.utc).isoformat(),
                "workspace_id": workspace_id,
                "actor_id": actor_id,
                "correlation_id": correlation_id or current_correlation_id(),
                "object_ref": object_ref,
                "idempotency_key": idempotency_key,
                "data": data or {},
                "previous_hash": previous_hash,
            }
            selected["event_hash"] = hashlib.sha256(_canonical(selected)).hexdigest()
            return previous + _canonical(selected) + b"\n"

        ArtifactStore(self.root).update_bytes(self.path, append_to)
        return selected
