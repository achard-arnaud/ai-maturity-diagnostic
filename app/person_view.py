"""Person 360 view: compose identity, relationships and companies without
fusing their truths (Epic 02 S05).

Each section keeps its own `provenance` (and, for relationships, its own
computed `currentness`) rather than being flattened into one record. A
relationship's evidence_grade never gets copied onto the person, and a
company's provenance never gets copied onto a relationship -- composing a
360 view is a read-side aggregation over distinct sources, exactly like
app.account_view.get_account_360 already does for company/qualification/
reach/blocker-actions.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

from app.network_temporal import CurrentnessConflict, evaluate_currentness
from app.network_v1_store import EntityNotFound, get_entity, list_entities


def get_person_360(
    root: Path,
    workspace_id: str,
    person_entity_id: str,
    *,
    as_of: date | None = None,
) -> dict[str, Any] | None:
    """Aggregate one person's canonical identity, relationships and the
    companies those relationships point at.

    Returns None if the person entity is not known in this workspace (same
    "not found is an ordinary read-side outcome" convention as
    app.account_view.get_account_360).
    """

    try:
        person = get_entity(root, workspace_id, "person", person_entity_id)
    except EntityNotFound:
        return None

    as_of = as_of or date.today()

    relationships: list[dict[str, Any]] = []
    company_ids: set[str] = set()
    # Relationships are workspace-scoped like everything else here; a full
    # implementation would paginate, but Epic 02 S05's scope is the
    # composition contract, not scale -- S06's migration/backfill is where
    # real volumes land.
    page = list_entities(root, workspace_id, "relationship", limit=100)
    for relationship in page.items:
        if relationship["person_entity_id"] != person_entity_id:
            continue
        try:
            currentness = evaluate_currentness(relationship, as_of=as_of)
            currentness_view = {"is_current": currentness.is_current, "reason": currentness.reason}
        except CurrentnessConflict as exc:
            currentness_view = {"is_current": None, "reason": str(exc), "requires_human_review": True}
        relationships.append({**relationship, "currentness": currentness_view})
        company_ids.add(relationship["company_entity_id"])

    companies: list[dict[str, Any]] = []
    for company_entity_id in sorted(company_ids):
        try:
            companies.append(get_entity(root, workspace_id, "company", company_entity_id))
        except EntityNotFound:
            # A relationship can reference a company not yet backfilled into
            # the v1 store; surface that as an absence, not a crash.
            continue

    return {
        "person": person,
        "relationships": relationships,
        "companies": companies,
    }
