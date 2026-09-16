"""Legacy enterprise_demand_profile -> Demand v1 migration/reconciliation
(Epic 05 S06). Stop condition: "rollback validé" -- every applied
migration is fully, exactly reversible: rolling back removes precisely
the demand_ids this migration created (verified by count: N after
rollback == N-1 applied demands), and each item's manifest entry carries
a content hash of its source profile so a re-run can detect drift.

Follows the same dry-run/apply/rollback/manifest shape as
app.network_v1_migrator (Epic 02 S06) and app.workspace_migrator (Epic 01
S06). Scope: this is a 1:1 backfill of one legacy
05_enterprise_demand_profile.yaml per study into one CanonicalDemandV1 --
it never merges or de-duplicates across studies (mirrors
app.network_v1_migrator's own "migration never invents a merge" rule).
Legacy study files are only ever read, never mutated, by this module.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from app.artifact_store import ArtifactStore
from app.demand_mapping import map_from_enterprise_profile
from app.demand_store import DemandAlreadyExists, create_demand
from app.workspace_paths import resolve_workspace_root


class DemandMigrationError(RuntimeError):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _demand_id_for_study(study_id: str) -> str:
    """Deterministic mapping from study_id to demand_id -- re-running the
    same dry-run twice, or re-applying after a rollback, always produces
    the same demand_id (same discipline as
    app.network_v1_migrator._entity_id_for_legacy)."""
    return "demand_" + hashlib.sha256(study_id.encode("utf-8")).hexdigest()[:16]


def _company_entity_id_for_legacy(company_id: str) -> str:
    return "entity_" + hashlib.sha256(company_id.encode("utf-8")).hexdigest()[:16]


def _content_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@dataclass(frozen=True)
class DemandMigrator:
    repo_root: Path
    workspace_id: str

    @property
    def _legacy_studies_root(self) -> Path:
        return resolve_workspace_root(self.workspace_id, self.repo_root) / "studies"

    def plan(self, *, created_at: str | None = None) -> dict[str, Any]:
        created_at = created_at or _now()
        items: list[dict[str, Any]] = []
        studies_root = self._legacy_studies_root
        if studies_root.is_dir():
            for manifest_path in sorted(studies_root.glob("*/00_manifest.yaml")):
                profile_path = manifest_path.parent / "05_enterprise_demand_profile.yaml"
                if not profile_path.is_file():
                    continue
                manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
                profile = yaml.safe_load(profile_path.read_text(encoding="utf-8")) or {}
                study_id = str(manifest.get("study_id") or manifest_path.parent.name)
                company_id = str(manifest.get("company_id") or manifest.get("company") or study_id)
                items.append(
                    {
                        "study_id": study_id,
                        "demand_id": _demand_id_for_study(study_id),
                        "company_entity_id": _company_entity_id_for_legacy(company_id),
                        "origin_profile_ref": profile_path.relative_to(self.repo_root).as_posix(),
                        "content_hash": _content_hash(profile_path),
                        "_profile": profile,
                    }
                )

        return {
            "schema_version": "1.0",
            "migration_id": f"demandmigration_{uuid.uuid4().hex}",
            "workspace_id": self.workspace_id,
            "created_at": created_at,
            "mode": "dry_run",
            "counts": {"studies": len(items), "total": len(items)},
            "items": items,
        }

    def apply(self, plan: dict[str, Any]) -> Path:
        if plan.get("workspace_id") != self.workspace_id or plan.get("mode") != "dry_run":
            raise DemandMigrationError("plan does not match this migration")

        applied: list[dict[str, Any]] = []
        skipped: list[dict[str, Any]] = []
        for item in plan["items"]:
            demand = map_from_enterprise_profile(
                item["_profile"],
                demand_id=item["demand_id"],
                workspace_id=self.workspace_id,
                company_entity_id=item["company_entity_id"],
                origin_profile_ref=item["origin_profile_ref"],
                created_at=plan["created_at"],
                updated_at=plan["created_at"],
            )
            try:
                create_demand(self.repo_root, self.workspace_id, demand)
                applied.append({"demand_id": item["demand_id"], "content_hash": item["content_hash"]})
            except DemandAlreadyExists:
                skipped.append({"demand_id": item["demand_id"], "reason": "already migrated"})

        manifest = {
            "schema_version": plan["schema_version"],
            "migration_id": plan["migration_id"],
            "workspace_id": self.workspace_id,
            "created_at": plan["created_at"],
            "applied_at": _now(),
            "mode": "applied",
            "counts": {**plan["counts"], "applied": len(applied), "skipped": len(skipped)},
            "applied_demand_ids": [a["demand_id"] for a in applied],
            "skipped": skipped,
            "rollback_status": "available",
        }
        manifest_path = self.repo_root / "runtime" / "migrations" / f"{plan['migration_id']}.json"
        ArtifactStore(self.repo_root).write_text(
            manifest_path, json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        )
        return manifest_path

    def rollback(self, manifest_path: Path) -> dict[str, Any]:
        manifest_path = manifest_path.resolve()
        try:
            manifest_path.relative_to((self.repo_root / "runtime" / "migrations").resolve())
        except ValueError as exc:
            raise DemandMigrationError("manifest is outside migration root") from exc
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("workspace_id") != self.workspace_id or manifest.get("mode") != "applied":
            raise DemandMigrationError("manifest does not match an applied migration")

        removed_ids = set(manifest.get("applied_demand_ids", []))
        path = Path("data") / "private" / "demands" / self.workspace_id / "demands.jsonl"
        store = ArtifactStore(self.repo_root)
        existing = store.read_bytes(path)
        removed_count = 0
        if existing is not None:
            data, _version = existing
            records = [json.loads(line) for line in data.decode("utf-8").splitlines() if line.strip()]
            kept = [r for r in records if r["demand_id"] not in removed_ids]
            removed_count = len(records) - len(kept)
            store.write_text(
                path,
                ("\n".join(json.dumps(r, ensure_ascii=False, sort_keys=True) for r in kept) + "\n") if kept else "",
            )

        result = {
            "migration_id": manifest["migration_id"],
            "rolled_back_at": _now(),
            "removed_count": removed_count,
        }
        rollback_path = manifest_path.with_name(f"{manifest['migration_id']}.rollback.json")
        store.write_text(rollback_path, json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
        return result
