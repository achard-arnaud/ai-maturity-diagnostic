from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.artifact_store import ArtifactStore

from app.core import ControlPlaneError

# Mirrors QualificationCockpit's step ids, in pipeline order. Kept here rather than
# imported from app.qualification to avoid coupling the audit log's validation to the
# cockpit's derived-state computation (ADR-004: this module never recomputes stage
# truth, it only records human-triggered dashboard actions against known step ids).
# TODO(red-team-spec): this audit log only understands the six qualification
# steps below; reach role-coverage blockers, nudging rationale, and other
# stage's blockers have no equivalent tracked-action log. Revisit once a
# second workspace or a second real GTM engagement needs a tracked human
# action outside this fixed six-step pipeline.
STEP_ORDER: list[str] = ["demand", "snapshots", "matching", "contacts", "reach", "pilot"]

ACTIONS = {"cancel", "step_back", "force"}


@dataclass(frozen=True)
class BlockerActionLog:
    """Append-only audit log for dashboard-level blocker-resolver actions.

    This is a lightweight, decoupled tracked-action log (per Sprint S6 D2 scope):
    it does NOT implement RBAC, auth, or a workspace-level override system (that is
    S8's job at the backend/RBAC layer, landing in parallel). It only records who did
    what, when, and why, so the dashboard can display it and a later authz layer can
    build on top of it without this module needing to change.
    """

    root: Path

    def _path(self, study_id: str) -> Path:
        safe = "".join(ch for ch in study_id if ch.isalnum() or ch in "-_.") or "unknown"
        return self.root / "studies" / safe / "06d_blocker_actions.jsonl"

    def record(
        self,
        *,
        study_id: str,
        step_id: str,
        action: str,
        actor: str,
        reason: str | None = None,
        target_step_id: str | None = None,
    ) -> dict[str, Any]:
        study_id = str(study_id or "").strip()
        step_id = str(step_id or "").strip()
        action = str(action or "").strip()
        actor = str(actor or "").strip()
        reason = (reason or "").strip() or None
        if not study_id:
            raise ControlPlaneError("study_id is required")
        if not actor:
            raise ControlPlaneError("actor is required for a tracked blocker action")
        if action not in ACTIONS:
            raise ControlPlaneError(f"unknown blocker action: {action}")
        if step_id not in STEP_ORDER:
            raise ControlPlaneError(f"unknown qualification step: {step_id}")
        if action == "force" and not reason:
            raise ControlPlaneError("a force action requires a mandatory reason")
        entry: dict[str, Any] = {
            "study_id": study_id,
            "step_id": step_id,
            "action": action,
            "actor": actor,
            "reason": reason,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        if action == "step_back":
            target_step_id = str(target_step_id or "").strip()
            if target_step_id not in STEP_ORDER:
                raise ControlPlaneError(f"unknown target_step_id: {target_step_id}")
            if STEP_ORDER.index(target_step_id) >= STEP_ORDER.index(step_id):
                raise ControlPlaneError("step_back target_step_id must be earlier in the qualification pipeline")
            entry["target_step_id"] = target_step_id
        path = self._path(study_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        ArtifactStore(self.root).append_jsonl(path, entry)
        return entry

    def _read_path(self, path: Path) -> list[dict[str, Any]]:
        if not path.is_file():
            return []
        rows: list[dict[str, Any]] = []
        for raw in path.read_text(encoding="utf-8").splitlines():
            if not raw.strip():
                continue
            try:
                item = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if isinstance(item, dict):
                rows.append(item)
        return rows

    def list_actions(
        self,
        study_id: str = "",
        *,
        action: str | None = None,
        step_id: str | None = None,
        since: str | None = None,
        until: str | None = None,
    ) -> list[dict[str, Any]]:
        """List recorded blocker actions, optionally filtered.

        With no arguments beyond `study_id`, behaves exactly as before
        (backward compatible with the existing `/api/qualification/actions`
        caller and Account 360's `recent_actions`). Passing an empty
        `study_id` lists across every study directory found under
        `root/studies/*/06d_blocker_actions.jsonl` (a cheap glob over the
        same JSONL files `record()` already writes -- no new index needed).

        `action`/`step_id` are exact-match filters against the recorded
        fields. `since`/`until` are ISO-8601 timestamp strings compared
        lexicographically against the entry's `timestamp` (safe because
        `record()` always writes `datetime.now(timezone.utc).isoformat()`,
        which sorts lexicographically in timestamp order).
        """
        study_id = str(study_id or "").strip()
        if study_id:
            rows = self._read_path(self._path(study_id))
        else:
            rows = []
            studies_root = self.root / "studies"
            if studies_root.is_dir():
                for log_path in sorted(studies_root.glob("*/06d_blocker_actions.jsonl")):
                    rows.extend(self._read_path(log_path))

        if action:
            rows = [row for row in rows if row.get("action") == action]
        if step_id:
            rows = [row for row in rows if row.get("step_id") == step_id]
        if since:
            rows = [row for row in rows if str(row.get("timestamp") or "") >= since]
        if until:
            rows = [row for row in rows if str(row.get("timestamp") or "") <= until]
        return rows
