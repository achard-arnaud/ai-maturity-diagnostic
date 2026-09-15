"""Promote staged catalog candidates into canonical product_catalog offers,
and let a product_owner edit specific fields of their own existing offer.

Per ADR-004, promotion is never automatic -- this module is the backend
half of an explicit, human-invoked promotion action (the route in
app/server.py requires an authenticated call; Part 3/RBAC gates who may
call it). It never runs implicitly from app/catalog.py's stage()/
discover_public() harvesting path.

Plain Python only -- no FastAPI/Starlette imports here (see app/server.py's
module docstring on the FastAPI-boundary rule).

Design decision (evidence status on promotion): a promoted offer is built
from an *unreviewed* staged candidate (app/catalog.py's
CatalogHarvester.stage() marks every item "epistemic_status:
unreviewed_source_claim"). We never upgrade that to a stronger claim on
promotion. If the candidate carries at least one source_url or raw_claims
entry, the resulting profile.proof.evidence_status/epistemic_status is
"vendor_claim" (something was actually sourced, just not human-verified);
if the candidate has neither, it is "hypothesis" (nothing but a bare
name). Every profile field that the candidate did not actually supply
data for is populated as an honest "unknown", never fabricated -- see
contract_notes in contracts/product_profile.schema.yaml ("Unknown
pricing, proof, deployment, or architecture must remain explicit
unknowns").

Known gap (flagged for the frontend sprint): update_offer_sheet accepts a
`workspace_id` parameter but does not cross-check it against the offer's
own ownership, because contracts/product_profile.schema.yaml carries no
workspace_id field today (most existing product_catalog/*.yaml files have
none). Real workspace-ownership enforcement belongs at the RBAC/route
layer once that schema question is settled -- this is a known,
intentionally deferred gap, not an oversight.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from app.core import ControlPlaneError, RepoControlPlane, _read_yaml

_CANDIDATE_HARVEST_DIR = ("data", "private", "catalog_harvest")
_PROTECTED_FIELDS = {"hard_gates", "proof", "offer_id"}
_EDITABLE_FIELDS = {"positioning", "problem", "outcomes", "icp", "name", "category"}


def _harvest_files(root: Path) -> list[Path]:
    directory = Path(root)
    for part in _CANDIDATE_HARVEST_DIR:
        directory = directory / part
    if not directory.is_dir():
        return []
    return sorted(directory.glob("*/*.yaml"))


def list_staged_candidates(root: Path) -> list[dict[str, Any]]:
    """Read every staged, unreviewed candidate item across all harvest
    documents under data/private/catalog_harvest/<company-slug>/*.yaml
    (the exact location app/catalog.py's CatalogHarvester.stage() writes
    to). Never reads or writes product_catalog/*.yaml.

    Returns a flat list, one entry per candidate item, each carrying a
    composite `id` (f"{harvest_id}:{candidate_id}") since an item's bare
    candidate_id ("CAND-001") is only unique within its own harvest
    document, not globally.
    """

    candidates: list[dict[str, Any]] = []
    for path in _harvest_files(root):
        try:
            document = _read_yaml(path)
        except ControlPlaneError:
            continue
        harvest_id = document.get("harvest_id")
        for item in document.get("items", []) or []:
            if not isinstance(item, dict):
                continue
            candidates.append(
                {
                    "id": f"{harvest_id}:{item.get('candidate_id')}",
                    "harvest_id": harvest_id,
                    "candidate_id": item.get("candidate_id"),
                    "company": document.get("company"),
                    "shelf_id": document.get("shelf_id"),
                    "name": item.get("name"),
                    "source_url": item.get("source_url"),
                    "raw_claims": item.get("raw_claims") or [],
                    "source_metadata": item.get("source_metadata") or {},
                    "promotion_status": item.get("promotion_status"),
                    "path": path.relative_to(Path(root)).as_posix(),
                }
            )
    return candidates


def _find_candidate(root: Path, candidate_id: str) -> dict[str, Any]:
    for candidate in list_staged_candidates(root):
        if candidate["id"] == candidate_id:
            return candidate
    raise ControlPlaneError(f"unknown staged candidate: {candidate_id}")


def promote_candidate(
    root: Path,
    candidate_id: str,
    *,
    offer_id: str,
    workspace_id: str | None = None,
) -> dict[str, Any]:
    """Write a new canonical product_catalog/<offer_id>.yaml from a staged,
    unreviewed candidate, and register it in product_catalog/index.yaml.

    Raises ControlPlaneError if candidate_id is not found, or if offer_id
    already exists in the catalog (promotion never silently overwrites an
    existing canonical offer -- use update_offer_sheet for that).
    """

    root = Path(root)
    offer_id = str(offer_id or "").strip()
    if not offer_id:
        raise ControlPlaneError("offer_id is required")

    candidate = _find_candidate(root, candidate_id)

    control = RepoControlPlane(root)
    existing_ids = {entry.get("offer_id") for entry in control.list_offers()}
    if offer_id in existing_ids:
        raise ControlPlaneError(f"offer_id already exists in the catalog: {offer_id}")

    has_source = bool(candidate.get("source_url")) or bool(candidate.get("raw_claims"))
    epistemic_status = "vendor_claim" if has_source else "hypothesis"
    name = str(candidate.get("name") or offer_id)
    file_name = f"{offer_id}.yaml"

    unknowns = [
        "Positioning, problem, and outcomes are unreviewed and derived only from a staged harvest candidate; none have been human-verified.",
        "ICP, hard gate feasibility, and pilot design are entirely unknown at promotion time.",
        "Commercial model and pricing are unknown.",
    ]
    if not candidate.get("source_url"):
        unknowns.append("No source_url was captured for this candidate.")
    if not candidate.get("raw_claims"):
        unknowns.append("No raw_claims text was captured for this candidate.")

    profile: dict[str, Any] = {
        "schema_version": "0.2",
        "offer": {
            "offer_id": offer_id,
            "name": name,
            "profile_version": "promoted-from-candidate.v0.1",
            "owner": None,
            "status": "draft",
            "category": None,
            "positioning": {
                "category_statement": None,
                "one_liner": " ".join(str(claim) for claim in candidate.get("raw_claims") or []) or None,
            },
            "problem": {
                "canonical": None,
                "anti_problem": [],
            },
            "outcomes": {
                "primary": [],
                "secondary": [],
            },
            "icp": {
                "maturity": {"must_have": [], "positive_signals": []},
                "personas": {},
                "anti_icp": [],
            },
            "hard_gates": [],
            "proof": {
                "source_registry": candidate.get("source_url"),
                "evidence_status": (
                    "Promoted directly from an unreviewed staged catalog candidate "
                    f"(harvest {candidate.get('harvest_id')}, candidate {candidate.get('candidate_id')}); "
                    "no human review, verification, or independent sourcing has occurred yet."
                ),
                "epistemic_status": epistemic_status,
            },
            "unknowns": unknowns,
            "promoted_from": {
                "candidate_id": candidate["id"],
                "harvest_id": candidate.get("harvest_id"),
                "company": candidate.get("company"),
                "source_url": candidate.get("source_url"),
            },
        },
    }
    if workspace_id:
        profile["offer"]["workspace_id"] = str(workspace_id)

    offer_path = root / "product_catalog" / file_name
    offer_path.parent.mkdir(parents=True, exist_ok=True)
    offer_path.write_text(yaml.safe_dump(profile, sort_keys=False, allow_unicode=True), encoding="utf-8")

    index_path = root / "product_catalog" / "index.yaml"
    index = _read_yaml(index_path) if index_path.is_file() else {"schema_version": "0.2", "offers": []}
    offers = index.get("offers") or []
    offers.append({"offer_id": offer_id, "file": file_name, "name": name, "status": "draft"})
    index["offers"] = offers
    index_path.write_text(yaml.safe_dump(index, sort_keys=False, allow_unicode=True), encoding="utf-8")

    return profile["offer"]


def update_offer_sheet(
    root: Path,
    offer_id: str,
    updates: dict[str, Any],
    *,
    workspace_id: str | None = None,
) -> dict[str, Any]:
    """Update specific fields (positioning/problem/outcomes/icp/name/category)
    of an existing product_catalog/<offer_id>.yaml. Never allows edits to
    hard_gates or proof -- those remain governed elsewhere (raises
    ControlPlaneError).

    `workspace_id` is accepted but not cross-checked against the offer's
    ownership -- see this module's docstring for why (known, deferred gap;
    the schema carries no workspace_id field on most existing offers).
    """

    root = Path(root)
    offer_id = str(offer_id or "").strip()
    if not offer_id:
        raise ControlPlaneError("offer_id is required")
    if not isinstance(updates, dict) or not updates:
        raise ControlPlaneError("updates must be a non-empty object")

    disallowed = set(updates) & _PROTECTED_FIELDS
    if disallowed:
        raise ControlPlaneError(
            f"cannot edit protected field(s) via update_offer_sheet: {', '.join(sorted(disallowed))}"
        )
    unknown_fields = set(updates) - _EDITABLE_FIELDS
    if unknown_fields:
        raise ControlPlaneError(
            f"cannot edit unsupported field(s): {', '.join(sorted(unknown_fields))}"
        )

    control = RepoControlPlane(root)
    file_name = next(
        (entry.get("file") for entry in control.list_offers() if entry.get("offer_id") == offer_id),
        None,
    )
    if not isinstance(file_name, str) or not file_name:
        raise ControlPlaneError(f"unknown offer_id: {offer_id}")

    offer_path = root / "product_catalog" / file_name
    document = _read_yaml(offer_path)
    offer = document.get("offer")
    if not isinstance(offer, dict):
        raise ControlPlaneError(f"malformed offer document: {file_name}")

    for field, value in updates.items():
        offer[field] = value
    document["offer"] = offer

    offer_path.write_text(yaml.safe_dump(document, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return offer
