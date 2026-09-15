from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

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
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return entry

    def list_actions(self, study_id: str) -> list[dict[str, Any]]:
        path = self._path(study_id)
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
