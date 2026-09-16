"""Legacy network -> v1 store migration/reconciliation (Epic 02 S06).

Follows the same dry-run/apply/rollback/manifest shape as
app.workspace_migrator (Epic 01 S06), specialized to this domain: it reads
the legacy v0.3 JSONL records (data/private/network/{people,companies,
relationships}.jsonl) for one workspace and backfills the v1 store
(app.network_v1_store) via the adapters from app.network_identity_v1.

Scope, per ADR-009: this is a 1:1 backfill (each current legacy record
gets exactly one new entity_id) -- it does NOT run identity resolution.
Discovering that two legacy person_ids are the same real person is Epic 02
S03's job (app.identity_resolution), run as a separate step against the
now-populated v1 store. Migration never invents a merge.

Legacy files (data/private/network/*.jsonl) and the legacy
/api/network/... routes are never read-write touched by this module
beyond a read pass -- "legacy routes compatibles" (S06's stop condition)
holds because nothing here mutates them.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from app.artifact_store import ArtifactStore
from app.network_identity_v1 import company_v0_3_to_v1, person_v0_3_to_v1, relationship_v0_3_to_v1
from app.network_v1_store import put_entity


class NetworkMigrationError(RuntimeError):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _entity_id_for_legacy(legacy_id: str) -> str:
    """Deterministic mapping from a legacy id to a v1 entity_id.

    Derived from the immutable legacy_id string itself (not from mutable
    identity-key fields like name/company), so re-running the same
    dry-run twice, or re-applying after a rollback, produces the same
    entity_id -- required for migration rehearsal to be meaningful.
    """

    return "entity_" + hashlib.sha256(legacy_id.encode("utf-8")).hexdigest()[:16]


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


@dataclass(frozen=True)
class NetworkV1Migrator:
    repo_root: Path
    workspace_id: str

    @property
    def legacy_root(self) -> Path:
        return self.repo_root / "data" / "private" / "network"

    def plan(self, *, as_of: date | None = None) -> dict[str, Any]:
        as_of = as_of or date.today()
        people = [
            p for p in _read_jsonl(self.legacy_root / "people.jsonl")
        ]
        companies = [
            c
            for c in _read_jsonl(self.legacy_root / "companies.jsonl")
            if (c.get("workspace_id") or "default") == self.workspace_id
        ]
        company_ids_in_scope = {c["company_id"] for c in companies}
        people = [p for p in people if p.get("seed_company_id") in company_ids_in_scope]
        person_ids_in_scope = {p["person_id"] for p in people}
        relationships = [
            r
            for r in _read_jsonl(self.legacy_root / "relationships.jsonl")
            if r.get("person_id") in person_ids_in_scope and r.get("company_id") in company_ids_in_scope
        ]

        items: list[dict[str, Any]] = []
        for person in people:
            items.append(
                {
                    "kind": "person",
                    "legacy_id": person["person_id"],
                    "entity_id": _entity_id_for_legacy(person["person_id"]),
                }
            )
        for company in companies:
            items.append(
                {
                    "kind": "company",
                    "legacy_id": company["company_id"],
                    "entity_id": _entity_id_for_legacy(company["company_id"]),
                }
            )
        for relationship in relationships:
            items.append(
                {
                    "kind": "relationship",
                    "legacy_id": relationship["relationship_id"],
                    "entity_id": relationship["relationship_id"],
                }
            )

        return {
            "schema_version": "1.0",
            "migration_id": f"netmigration_{uuid.uuid4().hex}",
            "workspace_id": self.workspace_id,
            "created_at": _now(),
            "as_of": as_of.isoformat(),
            "mode": "dry_run",
            "counts": {
                "people": len(people),
                "companies": len(companies),
                "relationships": len(relationships),
                "total": len(items),
            },
            "items": items,
            "_people": people,
            "_companies": companies,
            "_relationships": relationships,
        }

    def apply(self, plan: dict[str, Any]) -> Path:
        if plan.get("workspace_id") != self.workspace_id or plan.get("mode") != "dry_run":
            raise NetworkMigrationError("plan does not match this migration")

        as_of = plan["as_of"]
        person_entity_by_legacy = {p["person_id"]: _entity_id_for_legacy(p["person_id"]) for p in plan["_people"]}
        company_entity_by_legacy = {c["company_id"]: _entity_id_for_legacy(c["company_id"]) for c in plan["_companies"]}

        applied_entity_ids: list[dict[str, str]] = []
        for person in plan["_people"]:
            entity_id = person_entity_by_legacy[person["person_id"]]
            v1 = person_v0_3_to_v1(person, entity_id=entity_id, workspace_id=self.workspace_id, valid_from=as_of)
            put_entity(self.repo_root, self.workspace_id, "person", v1)
            applied_entity_ids.append({"kind": "person", "entity_id": entity_id})

        for company in plan["_companies"]:
            entity_id = company_entity_by_legacy[company["company_id"]]
            v1 = company_v0_3_to_v1(company, entity_id=entity_id, workspace_id=self.workspace_id, valid_from=as_of)
            put_entity(self.repo_root, self.workspace_id, "company", v1)
            applied_entity_ids.append({"kind": "company", "entity_id": entity_id})

        for relationship in plan["_relationships"]:
            person_entity_id = person_entity_by_legacy.get(relationship["person_id"])
            company_entity_id = company_entity_by_legacy.get(relationship["company_id"])
            if not person_entity_id or not company_entity_id:
                continue
            v1 = relationship_v0_3_to_v1(
                relationship,
                person_entity_id=person_entity_id,
                company_entity_id=company_entity_id,
                valid_from=as_of,
            )
            put_entity(self.repo_root, self.workspace_id, "relationship", v1)
            applied_entity_ids.append({"kind": "relationship", "entity_id": v1["relationship_entity_id"]})

        manifest = {
            "schema_version": plan["schema_version"],
            "migration_id": plan["migration_id"],
            "workspace_id": self.workspace_id,
            "created_at": plan["created_at"],
            "applied_at": _now(),
            "mode": "applied",
            "counts": plan["counts"],
            "applied_entities": applied_entity_ids,
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
            raise NetworkMigrationError("manifest is outside migration root") from exc
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("workspace_id") != self.workspace_id or manifest.get("mode") != "applied":
            raise NetworkMigrationError("manifest does not match an applied migration")

        kind_to_path = {
            "person": self.repo_root / "data" / "private" / "network_v1" / self.workspace_id / "people.jsonl",
            "company": self.repo_root / "data" / "private" / "network_v1" / self.workspace_id / "companies.jsonl",
            "relationship": self.repo_root / "data" / "private" / "network_v1" / self.workspace_id / "relationships.jsonl",
        }
        id_field = {"person": "entity_id", "company": "entity_id", "relationship": "relationship_entity_id"}
        removed_by_kind: dict[str, set[str]] = {"person": set(), "company": set(), "relationship": set()}
        for entry in manifest.get("applied_entities", []):
            removed_by_kind[entry["kind"]].add(entry["entity_id"])

        store = ArtifactStore(self.repo_root)
        for kind, path in kind_to_path.items():
            relative = path.relative_to(self.repo_root)
            existing = store.read_bytes(relative)
            if existing is None:
                continue
            data, _version = existing
            records = [json.loads(line) for line in data.decode("utf-8").splitlines() if line.strip()]
            kept = [r for r in records if r[id_field[kind]] not in removed_by_kind[kind]]
            store.write_text(
                relative,
                ("\n".join(json.dumps(r, ensure_ascii=False, sort_keys=True) for r in kept) + "\n") if kept else "",
            )

        result = {"migration_id": manifest["migration_id"], "rolled_back_at": _now(), "removed_count": sum(len(v) for v in removed_by_kind.values())}
        rollback_path = manifest_path.with_name(f"{manifest['migration_id']}.rollback.json")
        store.write_text(rollback_path, json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
        return result
