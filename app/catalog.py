from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from app.core import ControlPlaneError, _read_yaml

_SLUG = re.compile(r"[^a-z0-9]+")


def _slug(value: str) -> str:
    clean = _SLUG.sub("-", value.lower()).strip("-")
    if not clean:
        raise ControlPlaneError("company must contain letters or digits")
    return clean


@dataclass(frozen=True)
class CatalogHarvester:
    root: Path

    def _shelf_ids(self) -> set[str]:
        data = _read_yaml(self.root / "catalog_sources" / "shelves.yaml")
        return {
            str(item["shelf_id"])
            for item in data.get("shelves", []) or []
            if isinstance(item, dict) and item.get("shelf_id")
        }

    def stage(self, payload: dict[str, Any], *, persist: bool = True) -> dict[str, Any]:
        company = str(payload.get("company") or "").strip()
        shelf_id = str(payload.get("shelf_id") or "").strip()
        items = payload.get("items")
        if not company:
            raise ControlPlaneError("company is required")
        if shelf_id not in self._shelf_ids():
            raise ControlPlaneError(f"unknown shelf: {shelf_id}")
        if not isinstance(items, list) or not items:
            raise ControlPlaneError("items must be a non-empty list")

        normalized: list[dict[str, Any]] = []
        for position, raw in enumerate(items, start=1):
            if not isinstance(raw, dict):
                raise ControlPlaneError(f"item {position} must be an object")
            name = str(raw.get("name") or "").strip()
            if not name:
                raise ControlPlaneError(f"item {position} requires name")
            raw_claims = raw.get("raw_claims") or []
            if not isinstance(raw_claims, list):
                raise ControlPlaneError(f"item {position} raw_claims must be a list")
            source_url = raw.get("source_url")
            if source_url is not None and not isinstance(source_url, str):
                raise ControlPlaneError(f"item {position} source_url must be a string or null")
            normalized.append(
                {
                    "candidate_id": f"CAND-{position:03d}",
                    "name": name,
                    "source_url": source_url,
                    "raw_claims": raw_claims,
                    "epistemic_status": "unreviewed_source_claim",
                    "promotion_status": "candidate",
                }
            )

        document = {
            "schema_version": "0.5",
            "harvest_id": str(uuid.uuid4()),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "company": company,
            "shelf_id": shelf_id,
            "source_kind": payload.get("source_kind") or "manual_or_external_harvest",
            "items": normalized,
            "promotion_contract": {
                "automatic_promotion_to_product_catalog": False,
                "required_skill": "product-icp-intelligence",
                "required_human_review": True,
            },
        }

        relative_path = None
        if persist:
            directory = self.root / "data" / "private" / "catalog_harvest" / _slug(company)
            directory.mkdir(parents=True, exist_ok=True)
            target = directory / f"{document['harvest_id']}.yaml"
            target.write_text(yaml.safe_dump(document, sort_keys=False, allow_unicode=True), encoding="utf-8")
            relative_path = target.relative_to(self.root).as_posix()

        return {
            "status": "staged" if persist else "preview",
            "candidate_count": len(normalized),
            "path": relative_path,
            "harvest": document,
        }
