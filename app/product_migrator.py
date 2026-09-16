"""Legacy product_catalog/*.yaml -> Product/Snapshot v1 migration (Epic 06
S06). Stop condition: "catalogue compatible" -- an E2E harvest->publish
path (an old promote_candidate-produced offer file becomes a queryable,
stable v1 Product+Snapshot) proves the new catalog can absorb the entire
legacy one without breaking it.

Follows the same dry-run/apply/rollback/manifest shape as
app.demand_migrator (Epic 05 S06) and app.network_v1_migrator (Epic 02
S06). Each legacy offer file maps to exactly one Product and its first
(and, at migration time, only) published Snapshot -- migration never
merges offers and never mutates product_catalog/*.yaml, only reads it.
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
from app.product_policy import compute_content_hash
from app.product_snapshot_store import put_snapshot
from app.product_store import ProductNotFound, get_product, put_product


class ProductMigrationError(RuntimeError):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _product_id_for_offer(offer_id: str) -> str:
    return "product_" + hashlib.sha256(offer_id.encode("utf-8")).hexdigest()[:16]


def _snapshot_id_for_offer(offer_id: str) -> str:
    return "productsnapshot_" + hashlib.sha256(f"{offer_id}::v1".encode("utf-8")).hexdigest()[:16]


def _map_offer_content(offer: dict[str, Any]) -> dict[str, Any]:
    positioning = offer.get("positioning") or {}
    problem = offer.get("problem") or {}
    outcomes = offer.get("outcomes") or {}
    return {
        "name": str(offer.get("name") or offer.get("offer_id") or ""),
        "description": str(positioning.get("one_liner") or ""),
        "exclusions": [str(x) for x in (problem.get("anti_problem") or [])],
        "hard_gates": [str(x) for x in (offer.get("hard_gates") or [])],
        "capabilities": [str(x) for x in (outcomes.get("primary") or [])],
    }


@dataclass(frozen=True)
class ProductMigrator:
    repo_root: Path

    @property
    def _catalog_root(self) -> Path:
        return self.repo_root / "product_catalog"

    def plan(self, *, created_at: str | None = None) -> dict[str, Any]:
        created_at = created_at or _now()
        items: list[dict[str, Any]] = []
        catalog_root = self._catalog_root
        if catalog_root.is_dir():
            for offer_path in sorted(catalog_root.glob("*.yaml")):
                if offer_path.name == "index.yaml":
                    continue
                doc = yaml.safe_load(offer_path.read_text(encoding="utf-8")) or {}
                offer = doc.get("offer")
                if not isinstance(offer, dict) or not offer.get("offer_id"):
                    continue
                offer_id = str(offer["offer_id"])
                workspace_id = offer.get("workspace_id")
                owner_scope = (
                    {"kind": "workspace", "workspace_id": str(workspace_id)}
                    if workspace_id
                    else {"kind": "shared", "workspace_id": None}
                )
                content = _map_offer_content(offer)
                items.append(
                    {
                        "offer_id": offer_id,
                        "product_id": _product_id_for_offer(offer_id),
                        "snapshot_id": _snapshot_id_for_offer(offer_id),
                        "owner_scope": owner_scope,
                        "content": content,
                        "content_hash": compute_content_hash(content),
                        "origin_offer_ref": offer_path.relative_to(self.repo_root).as_posix(),
                    }
                )

        return {
            "schema_version": "1.0",
            "migration_id": f"productmigration_{uuid.uuid4().hex}",
            "created_at": created_at,
            "mode": "dry_run",
            "counts": {"offers": len(items), "total": len(items)},
            "items": items,
        }

    def apply(self, plan: dict[str, Any]) -> Path:
        if plan.get("mode") != "dry_run":
            raise ProductMigrationError("plan is not a fresh dry-run plan")

        applied: list[dict[str, Any]] = []
        skipped: list[dict[str, Any]] = []
        for item in plan["items"]:
            try:
                get_product(self.repo_root, item["product_id"])
                skipped.append({"product_id": item["product_id"], "reason": "already migrated"})
                continue
            except ProductNotFound:
                pass

            put_product(
                self.repo_root,
                {
                    "product_id": item["product_id"],
                    "owner_scope": item["owner_scope"],
                    "name": item["content"]["name"],
                    "status": "active",
                    "created_at": plan["created_at"],
                    "overlay_of_product_id": None,
                },
            )
            put_snapshot(
                self.repo_root,
                {
                    "snapshot_id": item["snapshot_id"],
                    "product_id": item["product_id"],
                    "product_version_id": f"{item['product_id']}-v1",
                    "owner_scope": item["owner_scope"],
                    "content": item["content"],
                    "content_hash": item["content_hash"],
                    "published_at": plan["created_at"],
                    "evidence_ids": [],
                    "supersedes_snapshot_id": None,
                },
            )
            applied.append(
                {
                    "product_id": item["product_id"],
                    "snapshot_id": item["snapshot_id"],
                    "content_hash": item["content_hash"],
                }
            )

        manifest = {
            "schema_version": plan["schema_version"],
            "migration_id": plan["migration_id"],
            "created_at": plan["created_at"],
            "applied_at": _now(),
            "mode": "applied",
            "counts": {**plan["counts"], "applied": len(applied), "skipped": len(skipped)},
            "applied_product_ids": [a["product_id"] for a in applied],
            "applied_snapshot_ids": [a["snapshot_id"] for a in applied],
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
            raise ProductMigrationError("manifest is outside migration root") from exc
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("mode") != "applied":
            raise ProductMigrationError("manifest does not match an applied migration")

        removed_products = set(manifest.get("applied_product_ids", []))
        removed_snapshots = set(manifest.get("applied_snapshot_ids", []))
        store = ArtifactStore(self.repo_root)

        removed_count = 0
        for path, id_field, removed_ids in (
            (Path("data") / "private" / "products" / "products.jsonl", "product_id", removed_products),
            (Path("data") / "private" / "product_snapshots" / "snapshots.jsonl", "snapshot_id", removed_snapshots),
        ):
            existing = store.read_bytes(path)
            if existing is None:
                continue
            data, _version = existing
            records = [json.loads(line) for line in data.decode("utf-8").splitlines() if line.strip()]
            kept = [r for r in records if r[id_field] not in removed_ids]
            removed_count += len(records) - len(kept)
            store.write_text(
                path,
                ("\n".join(json.dumps(r, ensure_ascii=False, sort_keys=True) for r in kept) + "\n") if kept else "",
            )

        result = {"migration_id": manifest["migration_id"], "rolled_back_at": _now(), "removed_count": removed_count}
        rollback_path = manifest_path.with_name(f"{manifest['migration_id']}.rollback.json")
        store.write_text(rollback_path, json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
        return result
