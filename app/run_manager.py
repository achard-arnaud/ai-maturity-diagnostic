"""Durable, resumable execution run state for local-first workflows."""

from __future__ import annotations

import hashlib
import hmac
import secrets
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from app.artifact_store import ArtifactStore, ArtifactVersionConflict
from app.event_journal import EventJournal


RUN_STATES = {"prepared", "started", "checkpointed", "completed", "blocked", "failed", "cancelled"}
TERMINAL_STATES = {"completed", "cancelled"}


class RunError(RuntimeError):
    pass


class RunStateError(RunError):
    pass


class InvalidResumeToken(RunError):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class PreparedRun:
    run: dict[str, Any]
    resume_token: str


@dataclass(frozen=True)
class RunManager:
    root: Path
    workspace_id: str
    actor_id: str

    @property
    def store(self) -> ArtifactStore:
        return ArtifactStore(self.root)

    @property
    def journal(self) -> EventJournal:
        return EventJournal(self.root)

    def _path(self, run_id: str) -> Path:
        if not run_id.startswith("run_") or not run_id[4:].isalnum():
            raise RunError("invalid run_id")
        return self.root / "runtime" / "runs" / f"{run_id}.yaml"

    def get(self, run_id: str) -> tuple[dict[str, Any], str]:
        path = self._path(run_id)
        current = self.store.read_bytes(path)
        if current is None:
            raise RunError(f"unknown run: {run_id}")
        data, version = current
        run = yaml.safe_load(data.decode("utf-8"))
        if not isinstance(run, dict):
            raise RunError(f"invalid run document: {run_id}")
        return run, version

    def prepare(
        self,
        capability: str,
        *,
        input_ref: str | None = None,
        idempotency_key: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> PreparedRun:
        if idempotency_key:
            existing = self.journal.find_by_idempotency_key(f"run.prepare:{idempotency_key}")
            if existing:
                run, _ = self.get(str(existing["object_ref"]).split(":", 1)[1])
                return PreparedRun(run, "")
        run_id = f"run_{uuid.uuid4().hex}"
        resume_token = secrets.token_urlsafe(32)
        now = _now()
        run = {
            "schema_version": "1.0",
            "run_id": run_id,
            "workspace_id": self.workspace_id,
            "capability": capability,
            "input_ref": input_ref,
            "status": "prepared",
            "attempt": 0,
            "checkpoint": None,
            "resume_token_hash": _token_hash(resume_token),
            "created_at": now,
            "updated_at": now,
            "metadata": metadata or {},
            "error": None,
            "output_refs": [],
        }
        self.store.write_yaml(self._path(run_id), run)
        self.journal.append(
            "run.prepared",
            workspace_id=self.workspace_id,
            actor_id=self.actor_id,
            object_ref=f"run:{run_id}",
            idempotency_key=f"run.prepare:{idempotency_key}" if idempotency_key else None,
            data={"capability": capability},
        )
        return PreparedRun(run, resume_token)

    def _transition(
        self,
        run_id: str,
        allowed: set[str],
        status: str,
        *,
        changes: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if status not in RUN_STATES:
            raise RunStateError(f"unknown run status: {status}")
        run, version = self.get(run_id)
        if run["status"] not in allowed:
            raise RunStateError(f"cannot transition {run_id} from {run['status']} to {status}")
        run.update(changes or {})
        run["status"] = status
        run["updated_at"] = _now()
        try:
            self.store.write_yaml(self._path(run_id), run, expected_version=version)
        except ArtifactVersionConflict as exc:
            raise RunStateError(f"concurrent update for {run_id}") from exc
        self.journal.append(
            f"run.{status}",
            workspace_id=self.workspace_id,
            actor_id=self.actor_id,
            object_ref=f"run:{run_id}",
            data={"attempt": run["attempt"], "checkpoint": run.get("checkpoint")},
        )
        return run

    def start(self, run_id: str) -> dict[str, Any]:
        run, _ = self.get(run_id)
        return self._transition(
            run_id,
            {"prepared", "checkpointed", "blocked", "failed"},
            "started",
            changes={"attempt": int(run.get("attempt") or 0) + 1, "error": None},
        )

    def checkpoint(self, run_id: str, checkpoint: dict[str, Any]) -> dict[str, Any]:
        return self._transition(run_id, {"started"}, "checkpointed", changes={"checkpoint": checkpoint})

    def complete(self, run_id: str, output_refs: list[str]) -> dict[str, Any]:
        return self._transition(run_id, {"started", "checkpointed"}, "completed", changes={"output_refs": output_refs})

    def block(self, run_id: str, reason: str) -> dict[str, Any]:
        return self._transition(run_id, {"started", "checkpointed"}, "blocked", changes={"error": {"reason": reason}})

    def fail(self, run_id: str, code: str, message: str, *, retryable: bool) -> dict[str, Any]:
        return self._transition(
            run_id,
            {"started", "checkpointed"},
            "failed",
            changes={"error": {"code": code, "message": message, "retryable": retryable}},
        )

    def cancel(self, run_id: str, reason: str) -> dict[str, Any]:
        return self._transition(
            run_id,
            {"prepared", "started", "checkpointed", "blocked", "failed"},
            "cancelled",
            changes={"error": {"reason": reason}},
        )

    def resume(self, run_id: str, resume_token: str) -> dict[str, Any]:
        run, _ = self.get(run_id)
        if not hmac.compare_digest(str(run["resume_token_hash"]), _token_hash(resume_token)):
            raise InvalidResumeToken("invalid resume token")
        if run["status"] not in {"checkpointed", "blocked", "failed"}:
            raise RunStateError(f"run is not resumable from {run['status']}")
        if run["status"] == "failed" and not bool((run.get("error") or {}).get("retryable")):
            raise RunStateError("non-retryable failed run cannot resume")
        return self.start(run_id)
