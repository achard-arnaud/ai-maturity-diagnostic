"""Authenticated write path for the private network JSONL layer.

Per ADR-004, the web control plane is orchestration, not business truth --
but a manually-entered contact or company *is* legitimate, human-asserted
network data, distinct from harvested/staged product-catalog candidates
(see app/catalog_promotion.py, which stays strictly manual-review-gated).
This module lets an authenticated user create a person or company record
through the same canonical `data/private/network/people.jsonl` /
`companies.jsonl` files that scripts/import_contacts.py writes offline,
reusing its exact ID/normalization conventions so a manually-created
record and a TSV-imported one are indistinguishable in shape.

Plain Python only -- no FastAPI/Starlette imports here (see app/server.py's
module docstring on the FastAPI-boundary rule).

Design decision (duplicate handling): mirrors scripts/import_contacts.py's
existing behavior exactly -- creating a person/company whose stable_id
already exists *updates the existing record in place* (merging
role_hypotheses, refreshing last_updated) rather than rejecting the
request or creating a second record. This keeps the two write paths
(offline TSV import, authenticated API) consistent: the identity key
(normalized name [+ company]) is the source of truth, not call order.

Known gap (flagged for the frontend sprint, per ADR-007 §7 scope): this
module never rebuilds data/private/network/network_index.sqlite. A
person/company created here will not appear in /api/network/people or
/api/network/companies search results until an admin calls
POST /admin/network/rebuild-index (or scripts/rebuild_network_index.py
runs). That manual-trigger design is intentional (see app/network_index.py's
module docstring) but is a real UX gap for anyone using the new create
routes expecting the record to show up immediately.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.core import ControlPlaneError
from scripts.network_common import normalize, read_jsonl, stable_id, utc_now, write_jsonl

PERSON_REQUIRED = [
    "person_id",
    "display_name",
    "seed_company_id",
    "identity_key_basis",
    "relationship_ids",
    "role_hypotheses",
    "status",
    "last_updated",
    "stale_after_months",
]

COMPANY_REQUIRED = [
    "company_id",
    "canonical_name",
    "aliases",
    "countries",
    "relationship_ids",
    "status",
    "last_updated",
    "stale_after_months",
]


def _network_dir(data_root: Path) -> Path:
    return Path(data_root) / "network"


def _validate_required(record: dict[str, Any], required: list[str], *, kind: str) -> None:
    missing = [field for field in required if record.get(field) in (None, "")]
    # Empty list-typed fields (e.g. relationship_ids=[]) are valid -- only
    # None/"" (missing) counts, since e.g. contact_count=0 or an empty list
    # is legitimate data. Re-check list fields with an explicit "not None".
    missing = [
        field
        for field in required
        if record.get(field) is None or (isinstance(record.get(field), str) and not record.get(field))
    ]
    if missing:
        raise ControlPlaneError(f"{kind} is missing required field(s): {', '.join(missing)}")


def create_company(
    data_root: Path,
    *,
    canonical_name: str,
    sector_code: str | None = None,
    workspace_id: str | None = None,
) -> dict[str, Any]:
    """Create (or update, if the normalized name already resolves to an
    existing company) a canonical company record.

    `sector_code` is accepted for forward compatibility with the ICB
    mapping shape used elsewhere (see app/network_index.py's sector_code
    derivation from icb_mapping.sector.code) but is stored only as a
    minimal icb_mapping stub when provided -- it is optional and does not
    replace a real ICB classification pass.
    """

    canonical_name = str(canonical_name or "").strip()
    if not canonical_name:
        raise ControlPlaneError("canonical_name is required")

    network_dir = _network_dir(data_root)
    companies_path = network_dir / "companies.jsonl"
    companies = {item["company_id"]: item for item in read_jsonl(companies_path)}

    company_id = stable_id("COMP", canonical_name)
    now_date = utc_now()[:10]

    company = companies.get(
        company_id,
        {
            "schema_version": "0.3",
            "company_id": company_id,
            "canonical_name": canonical_name,
            "normalized_name": normalize(canonical_name),
            "aliases": [],
            "countries": [],
            "relationship_ids": [],
            "linked_person_ids": [],
            "contact_count": 0,
            "icb_mapping": None,
            "network_screening": None,
            "study": None,
            "source_batch_ids": [],
            "status": "seeded",
            "last_updated": now_date,
            "stale_after_months": 6,
        },
    )
    if canonical_name not in company.get("aliases", []):
        company["aliases"] = [*company.get("aliases", []), canonical_name]
    if sector_code:
        company["icb_mapping"] = {"sector": {"code": str(sector_code)}}
    if workspace_id:
        company["workspace_id"] = str(workspace_id)
    company["last_updated"] = now_date
    company["source_batch_ids"] = list(dict.fromkeys([*company.get("source_batch_ids", []), "manual_entry"]))

    _validate_required(company, COMPANY_REQUIRED, kind="company")

    companies[company_id] = company
    write_jsonl(companies_path, companies.values(), "company_id")
    return company


# TODO(red-team-spec): create_person/create_company never rebuild
# network_index.sqlite (see module docstring above); revisit once a live
# customer onboarding session has actually hit this "I just added someone
# and can't find them" gap, rather than fixing it speculatively now.
def create_person(
    data_root: Path,
    *,
    display_name: str,
    seed_company_id: str,
    role_hypotheses: list[dict[str, Any]] | None = None,
    source: str = "manual_entry",
) -> dict[str, Any]:
    """Create (or update, if the identity key already resolves to an
    existing person) a canonical person record, seeded against an
    existing company (`seed_company_id`).

    Consistent with scripts/import_contacts.py: the person identity key is
    normalized_name + the company's canonical_name (not the raw company
    id), so this looks up the company record first to recover its
    canonical_name for stable_id() purposes.
    """

    display_name = str(display_name or "").strip()
    if not display_name:
        raise ControlPlaneError("display_name is required")
    seed_company_id = str(seed_company_id or "").strip()
    if not seed_company_id:
        raise ControlPlaneError("seed_company_id is required")

    network_dir = _network_dir(data_root)
    companies_path = network_dir / "companies.jsonl"
    people_path = network_dir / "people.jsonl"

    companies = {item["company_id"]: item for item in read_jsonl(companies_path)}
    company = companies.get(seed_company_id)
    if company is None:
        raise ControlPlaneError(f"unknown seed_company_id: {seed_company_id}")

    people = {item["person_id"]: item for item in read_jsonl(people_path)}
    person_id = stable_id("PERS", display_name, company["canonical_name"])
    now_date = utc_now()[:10]

    person = people.get(
        person_id,
        {
            "schema_version": "0.3",
            "person_id": person_id,
            "display_name": display_name,
            "normalized_name": normalize(display_name),
            "seed_company_id": seed_company_id,
            "identity_key_basis": "normalized_name_and_company",
            "relationship_ids": [],
            "role_hypotheses": [],
            "identity_confidence": "medium",
            "requires_identity_validation": True,
            "source_batch_ids": [],
            "status": "seeded",
            "last_updated": now_date,
            "stale_after_months": 6,
        },
    )

    incoming_roles = role_hypotheses or []
    if not isinstance(incoming_roles, list):
        raise ControlPlaneError("role_hypotheses must be a list")
    known_roles = {item["role"]: item for item in person.get("role_hypotheses", []) if isinstance(item, dict) and item.get("role")}
    for role in incoming_roles:
        if not isinstance(role, dict) or not role.get("role"):
            raise ControlPlaneError("each role_hypotheses entry must be an object with a 'role' key")
        known_roles.setdefault(role["role"], role)
    person["role_hypotheses"] = sorted(known_roles.values(), key=lambda item: item["role"])
    person["last_updated"] = now_date
    person["source_batch_ids"] = list(dict.fromkeys([*person.get("source_batch_ids", []), source]))

    _validate_required(person, PERSON_REQUIRED, kind="person")

    people[person_id] = person
    write_jsonl(people_path, people.values(), "person_id")
    return person


def reassign_company_workspace(data_root: Path, company_id: str, new_workspace_id: str) -> dict[str, Any]:
    """Move a company to a different workspace by updating its
    `workspace_id` field in-place in companies.jsonl.

    `data_root` is the directory containing companies.jsonl (e.g.
    ROOT / "data" / "private" / "network"). Read-modify-write over the
    whole file, matching write_jsonl's existing atomic-write convention.

    Raises ControlPlaneError for an unknown company_id or a blank
    new_workspace_id -- this is a required-precondition failure for a
    targeted mutation, not a read-side search a caller can shrug off.

    Never touches the derived SQLite index (data/private/network/
    network_index.sqlite) -- that stays a separate, explicit rebuild
    step. Callers must remember to trigger a rebuild afterwards, or
    search results served from the stale index will keep showing the
    old workspace_id until that happens.
    """
    company_id = str(company_id or "").strip()
    new_workspace_id = str(new_workspace_id or "").strip()
    if not company_id:
        raise ControlPlaneError("company_id is required")
    if not new_workspace_id:
        raise ControlPlaneError("new_workspace_id is required")

    companies_path = Path(data_root) / "companies.jsonl"
    records = read_jsonl(companies_path)
    updated: dict[str, Any] | None = None
    for record in records:
        if record.get("company_id") == company_id:
            record["workspace_id"] = new_workspace_id
            updated = record
            break
    if updated is None:
        raise ControlPlaneError(f"unknown company_id: {company_id}")

    write_jsonl(companies_path, records, sort_key="company_id")
    return updated
