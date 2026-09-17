"""Epic 13 S03: governed learning proposals with audited transitions."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.artifact_store import ArtifactStore
from app.event_journal import EventJournal


class LearningProposalError(ValueError):
    pass


ORIGINS = {"retrospective", "red_team", "dreaming"}
TARGET_KINDS = {"rule", "skill", "prompt", "offer", "workflow"}
TRANSITIONS = {
    "draft": {"in_review"},
    "in_review": {"accepted", "rejected"},
    "accepted": {"testing"},
    "testing": {"measured"},
    "rejected": set(),
    "measured": set(),
}


class LearningProposalStore:
    def __init__(self, root: Path, workspace_id: str) -> None:
        if not workspace_id.strip():
            raise LearningProposalError("workspace_id is required")
        self.root = root
        self.workspace_id = workspace_id
        self.store = ArtifactStore(root)
        self.directory = root / "workspaces" / workspace_id / "learning" / "proposals"
        self.events = EventJournal(root, f"workspaces/{workspace_id}/events/learning.jsonl")

    def _path(self, proposal_id: str) -> Path:
        if not proposal_id.startswith("lp_") or any(char not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" for char in proposal_id):
            raise LearningProposalError("invalid proposal_id")
        return self.directory / f"{proposal_id}.json"

    def create(self, *, origin: str, target_kind: str, target_ref: str, hypothesis: str, evidence_refs: list[str], actor_id: str, proposal_id: str | None = None) -> dict[str, Any]:
        if origin not in ORIGINS:
            raise LearningProposalError("origin must distinguish retrospective, red_team or dreaming")
        if target_kind not in TARGET_KINDS:
            raise LearningProposalError("unsupported target_kind")
        if not target_ref.strip() or not hypothesis.strip() or not actor_id.strip() or not evidence_refs:
            raise LearningProposalError("target_ref, hypothesis, evidence_refs and actor_id are required")
        identifier = proposal_id or f"lp_{uuid.uuid4().hex}"
        now = datetime.now(timezone.utc).isoformat()
        proposal = {
            "schema_version": "1.0",
            "proposal_id": identifier,
            "workspace_id": self.workspace_id,
            "origin": origin,
            "target": {"kind": target_kind, "ref": target_ref},
            "hypothesis": hypothesis,
            "evidence_refs": sorted(set(evidence_refs)),
            "status": "draft",
            "created_at": now,
            "created_by": actor_id,
            "experiment_id": None,
            "result_ref": None,
        }
        path = self._path(identifier)
        if path.exists():
            raise LearningProposalError("proposal already exists")
        self.store.write_bytes(path, json.dumps(proposal, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8"))
        self.events.append("learning.proposal.created", workspace_id=self.workspace_id, actor_id=actor_id, object_ref=identifier, data={"origin": origin, "target_kind": target_kind})
        return proposal

    def get(self, proposal_id: str) -> dict[str, Any]:
        path = self._path(proposal_id)
        if not path.is_file():
            raise LearningProposalError("proposal not found")
        return json.loads(path.read_text(encoding="utf-8"))

    def transition(self, proposal_id: str, *, to_status: str, actor_id: str, rationale: str, experiment_id: str | None = None, result_ref: str | None = None) -> dict[str, Any]:
        if not actor_id.strip() or not rationale.strip():
            raise LearningProposalError("actor_id and rationale are required")
        proposal = self.get(proposal_id)
        if to_status not in TRANSITIONS.get(proposal["status"], set()):
            raise LearningProposalError(f"invalid transition {proposal['status']} -> {to_status}")
        if to_status == "testing" and not experiment_id:
            raise LearningProposalError("testing requires experiment_id")
        if to_status == "measured" and (not result_ref or not proposal.get("experiment_id")):
            raise LearningProposalError("measured requires an experiment and result_ref")
        updated = dict(proposal)
        updated["status"] = to_status
        updated["updated_at"] = datetime.now(timezone.utc).isoformat()
        updated["updated_by"] = actor_id
        updated["decision_rationale"] = rationale
        if experiment_id:
            updated["experiment_id"] = experiment_id
        if result_ref:
            updated["result_ref"] = result_ref
        self.store.write_bytes(self._path(proposal_id), json.dumps(updated, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8"))
        self.events.append(f"learning.proposal.{to_status}", workspace_id=self.workspace_id, actor_id=actor_id, object_ref=proposal_id, data={"rationale": rationale, "experiment_id": updated.get("experiment_id"), "result_ref": updated.get("result_ref")})
        return updated

    def list(self) -> list[dict[str, Any]]:
        if not self.directory.is_dir():
            return []
        return sorted((json.loads(path.read_text(encoding="utf-8")) for path in self.directory.glob("lp_*.json")), key=lambda item: item["proposal_id"])
