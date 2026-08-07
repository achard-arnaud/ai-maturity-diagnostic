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
_PUBLIC_CATALOG_SOURCES = {"web", "perplexity"}


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
            source_metadata = raw.get("source_metadata") or {}
            if not isinstance(source_metadata, dict):
                raise ControlPlaneError(f"item {position} source_metadata must be an object")
            normalized.append(
                {
                    "candidate_id": f"CAND-{position:03d}",
                    "name": name,
                    "source_url": source_url,
                    "raw_claims": raw_claims,
                    "source_metadata": source_metadata,
                    "epistemic_status": "unreviewed_source_claim",
                    "promotion_status": "candidate",
                }
            )

        acquisition = payload.get("acquisition") or {}
        if not isinstance(acquisition, dict):
            raise ControlPlaneError("acquisition must be an object")

        document = {
            "schema_version": "0.5",
            "harvest_id": str(uuid.uuid4()),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "company": company,
            "shelf_id": shelf_id,
            "source_kind": payload.get("source_kind") or "manual_or_external_harvest",
            "acquisition": acquisition,
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

    def discover_public(self, payload: dict[str, Any], *, persist: bool = True) -> dict[str, Any]:
        company = str(payload.get("company") or "").strip()
        shelf_id = str(payload.get("shelf_id") or "").strip()
        if not company:
            raise ControlPlaneError("company is required")
        if shelf_id not in self._shelf_ids():
            raise ControlPlaneError(f"unknown shelf: {shelf_id}")

        source = str(payload.get("source") or "web").strip().lower()
        if source not in _PUBLIC_CATALOG_SOURCES:
            raise ControlPlaneError(
                "public catalog discovery source must be one of: "
                + ", ".join(sorted(_PUBLIC_CATALOG_SOURCES))
            )
        try:
            days = max(1, min(int(payload.get("days") or 3650), 3650))
            limit = max(1, min(int(payload.get("limit") or 12), 20))
        except (TypeError, ValueError) as exc:
            raise ControlPlaneError("days and limit must be integers") from exc

        domain = str(payload.get("domain") or "").strip()
        if domain and ("/" in domain or " " in domain):
            raise ControlPlaneError("domain must be a hostname, not a URL")
        query = str(payload.get("query") or "").strip()
        if not query:
            query = f'"{company}" products services solutions offers catalog'
        if domain:
            query = f"site:{domain} {query}"

        try:
            from scripts.advanced_research import SEARCHERS, source_limitations

            hits = SEARCHERS[source](query, days, limit, False)
        except Exception as exc:
            raise ControlPlaneError(f"public catalog discovery failed: {exc}") from exc

        if not hits:
            return {
                "status": "empty",
                "candidate_count": 0,
                "path": None,
                "acquisition": {
                    "source": source,
                    "query": query,
                    "days": days,
                    "limit": limit,
                },
            }

        items = []
        for hit in hits:
            claims = [hit.snippet] if hit.snippet else []
            items.append(
                {
                    "name": hit.title or hit.url,
                    "source_url": hit.url,
                    "raw_claims": claims,
                    "source_metadata": {
                        "source": hit.source,
                        "published_at": hit.published_at,
                        "author": hit.author,
                        "relevance": hit.relevance,
                        **(hit.metadata or {}),
                    },
                }
            )

        return self.stage(
            {
                "company": company,
                "shelf_id": shelf_id,
                "source_kind": f"public_catalog_discovery:{source}",
                "items": items,
                "acquisition": {
                    "source": source,
                    "query": query,
                    "days": days,
                    "limit": limit,
                    "limitations": source_limitations(source),
                },
            },
            persist=persist,
        )
