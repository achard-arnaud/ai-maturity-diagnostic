"""Canonical v1 identity contracts and N-1 adapters (Epic 02 S01).

Per ADR-009: the v1 contracts (contracts/{person,company,relationship}_v1
.schema.yaml) are additive projections, not replacements. Legacy writers
(app/network_writer.py, scripts/import_contacts.py) keep producing v0.3
records unchanged. This module only:

1. Loads and exposes the v1 JSON schemas for validation.
2. Adapts a legacy v0.3 record into a v1-shaped dict (the "N-1 reader":
   nothing from the legacy record is lost, but no legacy writer is touched).

No entity_id is assigned by any automatic process yet -- that is Epic 02
S03 (identity resolution) and S06 (migration/backfill). Callers of the
adapters here must supply entity_id explicitly.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

CONTRACTS_ROOT = Path(__file__).resolve().parents[1] / "contracts"


def load_v1_schema(name: str) -> dict[str, Any]:
    """Load one of the v1 JSON schemas by base name, e.g. "person"."""

    path = CONTRACTS_ROOT / f"{name}_v1.schema.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def person_v0_3_to_v1(
    record: dict[str, Any],
    *,
    entity_id: str,
    workspace_id: str,
    valid_from: str,
) -> dict[str, Any]:
    """Adapt a legacy contracts/person.schema.yaml (v0.3) record to v1 shape."""

    return {
        "entity_id": entity_id,
        "legacy_ids": [record["person_id"]],
        "display_name": record["display_name"],
        "normalized_name": record.get("normalized_name", ""),
        "workspace_id": workspace_id,
        "valid_from": valid_from,
        "valid_to": None,
        "status": record["status"],
        "merged_into_entity_id": None,
        "provenance": {
            "source_refs": list(record.get("source_batch_ids", [])),
            "epistemic_status": "unknown" if record.get("requires_identity_validation") else "inference",
            "evidence_grade": "U1",
        },
        "last_updated": record["last_updated"],
        "stale_after_months": record["stale_after_months"],
    }


def company_v0_3_to_v1(
    record: dict[str, Any],
    *,
    entity_id: str,
    workspace_id: str,
    valid_from: str,
) -> dict[str, Any]:
    """Adapt a legacy contracts/company.schema.yaml (v0.3) record to v1 shape."""

    return {
        "entity_id": entity_id,
        "legacy_ids": [record["company_id"]],
        "canonical_name": record["canonical_name"],
        "normalized_name": record.get("normalized_name", ""),
        "aliases": list(record.get("aliases", [])),
        "countries": list(record.get("countries", [])),
        "workspace_id": workspace_id or record.get("workspace_id") or "default",
        "valid_from": valid_from,
        "valid_to": None,
        "status": record["status"],
        "merged_into_entity_id": None,
        "provenance": {
            "source_refs": list(record.get("source_batch_ids", [])),
            "epistemic_status": "inference",
            "evidence_grade": "U1",
        },
        "last_updated": record["last_updated"],
        "stale_after_months": record["stale_after_months"],
    }


def relationship_v0_3_to_v1(
    record: dict[str, Any],
    *,
    person_entity_id: str,
    company_entity_id: str,
    valid_from: str,
) -> dict[str, Any]:
    """Adapt a legacy contracts/relationship.schema.yaml (v0.3) record to v1 shape."""

    return {
        "relationship_entity_id": record["relationship_id"],
        "legacy_ids": [record["relationship_id"]],
        "person_entity_id": person_entity_id,
        "company_entity_id": company_entity_id,
        "job_title": record["job_title"],
        "country": record["country"],
        "relationship_type": "employment",
        "current_status": record["current_status"],
        "valid_from": record.get("observed_at") or valid_from,
        "valid_to": None,
        "role_hypotheses": list(record.get("role_hypotheses", [])),
        "provenance": {
            "source_refs": list(record.get("source_refs", [])),
            "epistemic_status": record["epistemic_status"],
            "evidence_grade": record["evidence_grade"],
        },
        "requires_validation": bool(record.get("requires_validation", False)),
    }
