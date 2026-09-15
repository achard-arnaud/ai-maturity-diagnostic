"""Prospecting-campaign launch and cross-sell prep, on top of the existing
network search index and nudging module.

Plain Python only -- no FastAPI/Starlette imports here (see app/server.py's module
docstring on the FastAPI-boundary rule).

This module does not duplicate search logic: `launch_prospecting_campaign` runs
`app.network_index.search_people`/`search_companies` against the already-built
derived SQLite index and only persists the resulting campaign record. It does not
duplicate nudging logic either: `prepare_cross_sell` calls
`UseCaseNudger.generate(study_id, mode="cross_sell_package")` and only records that
the prep happened.

Persistence for campaign records follows the same atomic-write convention as the
rest of the private network JSONL layer (scripts/network_common.py: read the whole
file, add/replace a record, write the whole file back through a temp-file rename),
rather than BlockerActionLog's append-only pattern -- BlockerActionLog is scoped to
QualificationCockpit's six named pipeline steps and its {cancel, step_back, force}
action vocabulary, neither of which a prospecting campaign or a cross-sell prep
event is (this is not a qualification-step blocker resolution at all). A campaign
can also change over time (e.g. going from "draft" to another status when list
views need to reflect the current state), which fits network_common's
read-modify-atomic-rewrite convention better than an append-only log.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.core import ControlPlaneError
from app.network_index import search_companies, search_people
from app.nudging import UseCaseNudger
from scripts.network_common import read_jsonl, stable_id, utc_now, write_jsonl

_CRITERIA_FIELDS = {"text", "status", "company_id", "role", "stale", "workspace_id", "sector"}
_PEOPLE_ONLY_FIELDS = {"company_id", "role", "stale"}
_COMPANY_ONLY_FIELDS = {"sector"}


def _campaigns_path(root: Path) -> Path:
    return Path(root) / "data" / "private" / "network" / "campaigns.jsonl"


def _index_path(root: Path) -> Path:
    return Path(root) / "data" / "private" / "network" / "network_index.sqlite"


def _entity_kind(criteria: dict[str, Any]) -> str:
    """Infer whether this criteria dict targets people or companies.

    An explicit "entity" key ("people" | "companies") wins. Otherwise, a
    people-only filter (company_id/role/stale) or a company-only filter
    (sector) decides it; a criteria dict with neither, or with both a
    people-only and a company-only field, must say which entity it means.
    """
    entity = criteria.get("entity")
    if entity in {"people", "companies"}:
        return entity
    wants_people = bool(_PEOPLE_ONLY_FIELDS & criteria.keys())
    wants_companies = bool(_COMPANY_ONLY_FIELDS & criteria.keys())
    if wants_people and not wants_companies:
        return "people"
    if wants_companies and not wants_people:
        return "companies"
    raise ControlPlaneError(
        "prospecting criteria must set entity to 'people' or 'companies' "
        "(or use a field that unambiguously implies one, e.g. company_id/role/stale for people, sector for companies)"
    )


def _run_search(root: Path, criteria: dict[str, Any]) -> tuple[str, list[dict[str, Any]]]:
    unknown = sorted(set(criteria.keys()) - _CRITERIA_FIELDS - {"entity"})
    if unknown:
        raise ControlPlaneError("unknown prospecting criteria field(s): " + ", ".join(unknown))
    entity = _entity_kind(criteria)
    index_path = _index_path(root)
    if entity == "people":
        results = search_people(
            index_path,
            text=criteria.get("text") or None,
            status=criteria.get("status") or None,
            company_id=criteria.get("company_id") or None,
            role=criteria.get("role") or None,
            stale_only=bool(criteria.get("stale")),
            workspace_id=criteria.get("workspace_id") or None,
        )
    else:
        results = search_companies(
            index_path,
            text=criteria.get("text") or None,
            sector=criteria.get("sector") or None,
            workspace_id=criteria.get("workspace_id") or None,
        )
    return entity, results


def _load_campaigns(root: Path) -> list[dict[str, Any]]:
    return read_jsonl(_campaigns_path(root))


def _save_campaign(root: Path, record: dict[str, Any]) -> None:
    records = [item for item in _load_campaigns(root) if item.get("campaign_id") != record["campaign_id"]]
    records.append(record)
    write_jsonl(_campaigns_path(root), records, sort_key="campaign_id")


def list_campaigns(root: Path) -> list[dict[str, Any]]:
    return sorted(_load_campaigns(root), key=lambda item: str(item.get("created_at") or ""))


def launch_prospecting_campaign(root: Path, *, name: str, criteria: dict[str, Any], actor: str) -> dict[str, Any]:
    name = str(name or "").strip()
    actor = str(actor or "").strip()
    if not name:
        raise ControlPlaneError("campaign name is required")
    if not actor:
        raise ControlPlaneError("actor is required for a tracked prospecting campaign")
    if not isinstance(criteria, dict):
        raise ControlPlaneError("criteria must be an object")
    entity, results = _run_search(root, criteria)
    created_at = utc_now()
    record: dict[str, Any] = {
        "campaign_id": stable_id("CAMP", name, entity, created_at),
        "kind": "prospecting",
        "name": name,
        "entity": entity,
        "criteria": criteria,
        "target_count": len(results),
        "created_at": created_at,
        "actor": actor,
        "status": "draft",
    }
    _save_campaign(root, record)
    return record


def prepare_cross_sell(root: Path, *, study_id: str, actor: str) -> dict[str, Any]:
    study_id = str(study_id or "").strip()
    actor = str(actor or "").strip()
    if not study_id:
        raise ControlPlaneError("study_id is required")
    if not actor:
        raise ControlPlaneError("actor is required for a tracked cross-sell prep")
    generated = UseCaseNudger(root).generate(study_id, mode="cross_sell_package")
    created_at = utc_now()
    event: dict[str, Any] = {
        "campaign_id": stable_id("XSELL", study_id, actor, created_at),
        "kind": "cross_sell_prep",
        "study_id": study_id,
        "company": generated.get("company"),
        "nudge_count": len(generated.get("nudges", []) or []),
        "created_at": created_at,
        "actor": actor,
        "status": "recorded",
    }
    _save_campaign(root, event)
    return {"nudging": generated, "event": event}
