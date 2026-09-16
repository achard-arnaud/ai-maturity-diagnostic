"""Reversible legacy mono-root to workspace file migration framework."""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.artifact_store import ArtifactStore


MIGRATION_ROOTS = ("studies", "data/private", "artifacts")


class MigrationError(RuntimeError):
    pass


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class WorkspaceMigrator:
    repo_root: Path
    workspace_id: str

    def __post_init__(self) -> None:
        root = self.repo_root.resolve()
        target = (root / "workspaces" / self.workspace_id).resolve()
        try:
            target.relative_to((root / "workspaces").resolve())
        except ValueError as exc:
            raise MigrationError("workspace_id escapes workspaces root") from exc
        if self.workspace_id in {"", ".", ".."}:
            raise MigrationError("workspace_id is required")
        object.__setattr__(self, "repo_root", root)

    @property
    def workspace_root(self) -> Path:
        return self.repo_root / "workspaces" / self.workspace_id

    def plan(self) -> dict[str, Any]:
        items: list[dict[str, Any]] = []
        for root_name in MIGRATION_ROOTS:
            source_root = self.repo_root / root_name
            if not source_root.is_dir():
                continue
            for source in sorted(path for path in source_root.rglob("*") if path.is_file()):
                relative = source.relative_to(self.repo_root)
                destination = self.workspace_root / relative
                item = {
                    "source": relative.as_posix(),
                    "destination": destination.relative_to(self.repo_root).as_posix(),
                    "sha256": _sha256(source),
                    "size": source.stat().st_size,
                    "action": "copy",
                }
                if destination.is_file():
                    item["action"] = "skip_same" if _sha256(destination) == item["sha256"] else "conflict"
                items.append(item)
        return {
            "schema_version": "1.0",
            "migration_id": f"migration_{uuid.uuid4().hex}",
            "workspace_id": self.workspace_id,
            "created_at": _now(),
            "mode": "dry_run",
            "roots": list(MIGRATION_ROOTS),
            "explicitly_excluded": ["product_catalog"],
            "counts": {
                "files": len(items),
                "bytes": sum(int(item["size"]) for item in items),
                "copy": sum(item["action"] == "copy" for item in items),
                "skip_same": sum(item["action"] == "skip_same" for item in items),
                "conflict": sum(item["action"] == "conflict" for item in items),
            },
            "items": items,
        }

    def apply(self, plan: dict[str, Any]) -> Path:
        if plan.get("workspace_id") != self.workspace_id or plan.get("mode") != "dry_run":
            raise MigrationError("plan does not match this migration")
        if any(item.get("action") == "conflict" for item in plan.get("items", [])):
            raise MigrationError("migration has destination conflicts")
        # Preflight every source before the first destination mutation.
        for item in plan.get("items", []):
            source = self.repo_root / item["source"]
            if not source.is_file() or _sha256(source) != item["sha256"]:
                raise MigrationError(f"source changed after dry-run: {item['source']}")
        target_store = ArtifactStore(self.workspace_root)
        applied: list[dict[str, Any]] = [{**item, "applied": False} for item in plan.get("items", [])]
        manifest = {
            **plan,
            "mode": "applying",
            "started_at": _now(),
            "items": applied,
            "rollback_status": "available",
        }
        manifest_path = self.repo_root / "runtime" / "migrations" / f"{plan['migration_id']}.json"
        manifest_store = ArtifactStore(self.repo_root)

        def persist_manifest() -> None:
            manifest_store.write_text(
                manifest_path, json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
            )

        persist_manifest()
        for position, item in enumerate(plan.get("items", [])):
            if item["action"] != "copy":
                continue
            source = self.repo_root / item["source"]
            destination = self.repo_root / item["destination"]
            relative_destination = destination.relative_to(self.workspace_root)
            target_store.write_bytes(relative_destination, source.read_bytes())
            applied[position]["applied"] = True
            persist_manifest()
        manifest["mode"] = "applied"
        manifest["applied_at"] = _now()
        persist_manifest()
        return manifest_path

    def rollback(self, manifest_path: Path) -> dict[str, Any]:
        manifest_path = manifest_path.resolve()
        try:
            manifest_path.relative_to((self.repo_root / "runtime" / "migrations").resolve())
        except ValueError as exc:
            raise MigrationError("manifest is outside migration root") from exc
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("workspace_id") != self.workspace_id or manifest.get("mode") not in {"applying", "applied"}:
            raise MigrationError("manifest does not match an applied migration")
        removed: list[str] = []
        for item in reversed(manifest.get("items", [])):
            if not item.get("applied"):
                continue
            destination = (self.repo_root / item["destination"]).resolve()
            try:
                destination.relative_to(self.workspace_root.resolve())
            except ValueError as exc:
                raise MigrationError("rollback destination escapes workspace") from exc
            if not destination.is_file():
                continue
            if _sha256(destination) != item["sha256"]:
                raise MigrationError(f"refusing to remove modified destination: {item['destination']}")
            destination.unlink()
            removed.append(item["destination"])
        result = {"migration_id": manifest["migration_id"], "rolled_back_at": _now(), "removed": removed}
        rollback_path = manifest_path.with_name(f"{manifest['migration_id']}.rollback.json")
        ArtifactStore(self.repo_root).write_text(
            rollback_path, json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        )
        return result
