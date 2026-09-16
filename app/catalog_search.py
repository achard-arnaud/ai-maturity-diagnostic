"""Pure-Python search/filter over ``product_catalog/*.yaml`` offer profiles.

Per ADR-007 §6 / ADR-004: this module must stay free of any
FastAPI/Starlette dependency so it remains usable from plain Python
(scripts, other business modules, tests) without pulling in the web
transport layer.

The full offer profiles served by ``/api/offers`` are richer than what
``RepoControlPlane.list_offers()`` returns (it deliberately stays
lightweight: offer_id/name/status/file/category/profile_version). This
module reuses that method for catalog enumeration (so it does not
duplicate the ``index.yaml`` parsing logic) and then re-reads each
offer's own YAML file for the additional free-text/ICP fields it
searches over. Every access into offer-specific fields is defensive:
the schema has evolved between offers (see
``contracts/product_profile.schema.yaml``), so a field present on one
offer (e.g. Astraforge's enriched ``icp.personas``) may be absent or
differently shaped on another (e.g. a simpler ``icp.positive_signals``
list). Missing or malformed fields are treated as "no match", never as
an error.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.core import RepoControlPlane, _read_yaml


@dataclass(frozen=True)
class CatalogSearchResult:
    offer_id: str | None
    name: str | None
    category: str | None
    status: str | None
    one_liner: str | None
    matched_on: list[str]
    file: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "offer_id": self.offer_id,
            "name": self.name,
            "category": self.category,
            "status": self.status,
            "one_liner": self.one_liner,
            "matched_on": self.matched_on,
            "file": self.file,
        }


def _as_str(value: Any) -> str:
    return value if isinstance(value, str) else ""


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _flatten_text_values(value: Any) -> list[str]:
    """Best-effort collection of every string found under ``value``.

    Used for the defensive ICP match: personas/signals show up as flat
    lists of strings on some offers, as nested dicts of lists on
    others (or are simply absent) — this walks whatever shape is there
    without assuming a fixed structure.
    """

    texts: list[str] = []
    if isinstance(value, str):
        texts.append(value)
    elif isinstance(value, list):
        for item in value:
            texts.extend(_flatten_text_values(item))
    elif isinstance(value, dict):
        for item in value.values():
            texts.extend(_flatten_text_values(item))
    return texts


class CatalogSearch:
    """Search/filter API over the product catalog's offer profiles."""

    def __init__(self, root: Path | None = None):
        self._control = RepoControlPlane(root or RepoControlPlane.default().root)

    def _load_profile(self, file_name: str | None) -> dict[str, Any]:
        if not isinstance(file_name, str) or not file_name:
            return {}
        offer_path = self._control.root / "product_catalog" / file_name
        if not offer_path.is_file():
            return {}
        return _as_dict(_read_yaml(offer_path).get("offer"))

    def search(
        self,
        query: str = "",
        category: str = "",
        status: str = "",
    ) -> list[dict[str, Any]]:
        """Return lightweight search hits across all catalog offers.

        - ``query``: free-text, matched case-insensitively against
          ``name``, ``positioning.one_liner``, ``positioning.category_statement``,
          ``category``, and (defensively) ICP persona/signal text.
        - ``category``: exact, case-insensitive filter on ``category``.
        - ``status``: exact, case-insensitive filter on ``status``.

        Full offer YAML is never returned here — use ``/api/offers``
        (or read the file at the returned ``file`` path) for that.
        """

        needle = query.strip().lower()
        category_filter = category.strip().lower()
        status_filter = status.strip().lower()

        results: list[CatalogSearchResult] = []
        for entry in self._control.list_offers():
            offer_id = entry.get("offer_id")
            entry_status = _as_str(entry.get("status"))
            entry_category = _as_str(entry.get("category"))
            file_name = entry.get("file")

            if status_filter and entry_status.strip().lower() != status_filter:
                continue
            if category_filter and entry_category.strip().lower() != category_filter:
                continue

            profile = self._load_profile(file_name if isinstance(file_name, str) else None)
            name = _as_str(entry.get("name")) or _as_str(profile.get("name"))
            positioning = _as_dict(profile.get("positioning"))
            one_liner = _as_str(positioning.get("one_liner"))
            category_statement = _as_str(positioning.get("category_statement"))
            icp = _as_dict(profile.get("icp"))

            matched_on: list[str] = []
            if needle:
                if needle in name.lower():
                    matched_on.append("name")
                if needle in one_liner.lower():
                    matched_on.append("positioning.one_liner")
                if needle in category_statement.lower():
                    matched_on.append("positioning.category_statement")
                if needle in entry_category.lower():
                    matched_on.append("category")
                if not matched_on:
                    icp_texts = _flatten_text_values(icp)
                    if any(needle in text.lower() for text in icp_texts if isinstance(text, str)):
                        matched_on.append("icp")
                if not matched_on:
                    continue

            results.append(
                CatalogSearchResult(
                    offer_id=offer_id if isinstance(offer_id, str) else None,
                    name=name or None,
                    category=entry_category or None,
                    status=entry_status or None,
                    one_liner=one_liner or None,
                    matched_on=matched_on,
                    file=(
                        f"product_catalog/{file_name}"
                        if isinstance(file_name, str) and file_name
                        else None
                    ),
                )
            )

        return [result.to_dict() for result in results]


def search_catalog(
    root: Path | None = None,
    *,
    query: str = "",
    category: str = "",
    status: str = "",
) -> list[dict[str, Any]]:
    """Module-level convenience wrapper around :class:`CatalogSearch`."""

    return CatalogSearch(root).search(query=query, category=category, status=status)
