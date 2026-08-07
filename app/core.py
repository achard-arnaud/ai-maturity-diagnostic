from __future__ import annotations

import hashlib
import json
import os
import re
import shlex
import subprocess
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

_SKILL_ID = re.compile(r"^[a-z0-9][a-z0-9-]*$")


class ControlPlaneError(ValueError):
    pass


def _read_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _frontmatter(skill_md: Path) -> dict[str, Any]:
    text = skill_md.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}
    _, raw, _rest = text.split("---", 2)
    data = yaml.safe_load(raw)
    return data if isinstance(data, dict) else {}


def _safe_relative(root: Path, raw: str) -> str:
    candidate = (root / raw).resolve()
    try:
        relative = candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise ControlPlaneError(f"context path escapes repository: {raw}") from exc
    return relative.as_posix()


@dataclass(frozen=True)
class RepoControlPlane:
    root: Path

    @classmethod
    def default(cls) -> "RepoControlPlane":
        return cls(Path(__file__).resolve().parents[1])

    def list_skills(self) -> list[dict[str, Any]]:
        skills_root = self.root / "skills"
        items: list[dict[str, Any]] = []
        if not skills_root.is_dir():
            return items
        for skill_dir in sorted(path for path in skills_root.iterdir() if path.is_dir()):
            skill_md = skill_dir / "SKILL.md"
            if not skill_md.is_file():
                continue
            meta = _frontmatter(skill_md)
            skill_id = str(meta.get("name") or skill_dir.name)
            items.append(
                {
                    "id": skill_id,
                    "description": str(meta.get("description") or "").strip(),
                    "path": skill_md.relative_to(self.root).as_posix(),
                    "sha256": _sha256(skill_md),
                }
            )
        return items

    def list_offers(self) -> list[dict[str, Any]]:
        index_path = self.root / "product_catalog" / "index.yaml"
        index = _read_yaml(index_path)
        result: list[dict[str, Any]] = []
        for entry in index.get("offers", []) or []:
            if not isinstance(entry, dict):
                continue
            file_name = entry.get("file")
            profile: dict[str, Any] = {}
            if isinstance(file_name, str):
                offer_path = index_path.parent / file_name
                if offer_path.is_file():
                    profile = _read_yaml(offer_path).get("offer", {}) or {}
            result.append(
                {
                    "offer_id": entry.get("offer_id"),
                    "name": entry.get("name"),
                    "status": entry.get("status"),
                    "file": file_name,
                    "category": profile.get("category"),
                    "profile_version": profile.get("profile_version"),
                }
            )
        return result

    def list_shelves(self) -> list[dict[str, Any]]:
        path = self.root / "catalog_sources" / "shelves.yaml"
        data = _read_yaml(path)
        shelves = data.get("shelves", [])
        return [item for item in shelves if isinstance(item, dict)]

    def backlog(self) -> list[dict[str, Any]]:
        sources = [
            self.root / "artifacts" / "TODO_release_v0_3.yaml",
            self.root / "artifacts" / "TODO_productization_v0_5.yaml",
        ]
        result: list[dict[str, Any]] = []
        for path in sources:
            if not path.is_file():
                continue
            doc = _read_yaml(path)
            for item in doc.get("items", []) or []:
                if not isinstance(item, dict):
                    continue
                row = dict(item)
                row["source"] = path.relative_to(self.root).as_posix()
                result.append(row)
        return result

    def build_invocation(self, skill_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        if not _SKILL_ID.fullmatch(skill_id):
            raise ControlPlaneError("invalid skill id")
        skill_path = self.root / "skills" / skill_id / "SKILL.md"
        if not skill_path.is_file():
            raise ControlPlaneError(f"unknown skill: {skill_id}")
        context_paths = payload.get("context_paths") or []
        if not isinstance(context_paths, list):
            raise ControlPlaneError("context_paths must be a list")
        safe_context = [_safe_relative(self.root, str(path)) for path in context_paths]
        return {
            "schema_version": "0.5",
            "request_id": str(uuid.uuid4()),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "mode": "unit",
            "skill": {
                "id": skill_id,
                "path": skill_path.relative_to(self.root).as_posix(),
                "sha256": _sha256(skill_path),
            },
            "input": payload.get("input"),
            "context_paths": safe_context,
            "execution_contract": {
                "no_implicit_cross_skill_memory": True,
                "artifacts_are_handoffs": True,
                "respect_AGENTS_md": True,
            },
        }

    def invoke(self, skill_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        envelope = self.build_invocation(skill_id, payload)
        command = os.getenv("AI_DIAGNOSTIC_SKILL_EXECUTOR", "").strip()
        if not command:
            return {
                "status": "prepared",
                "executor_configured": False,
                "message": (
                    "Unit invocation prepared. Configure AI_DIAGNOSTIC_SKILL_EXECUTOR "
                    "to execute it; no execution is claimed without a runtime."
                ),
                "invocation": envelope,
            }
        timeout = int(os.getenv("AI_DIAGNOSTIC_SKILL_TIMEOUT_SECONDS", "120"))
        completed = subprocess.run(
            shlex.split(command),
            input=json.dumps(envelope, ensure_ascii=False),
            text=True,
            capture_output=True,
            timeout=timeout,
            cwd=self.root,
            check=False,
        )
        return {
            "status": "completed" if completed.returncode == 0 else "failed",
            "executor_configured": True,
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "invocation": envelope,
        }
