"""Epic 05 S01: map a legacy 05_enterprise_demand_profile.yaml
(contracts/enterprise_demand_profile.schema.yaml, app.demand.DemandCatalog)
onto a CanonicalDemandV1 record.

Migration parity discipline: every legacy field that has a v1 dimension
is carried over verbatim (never re-worded, never inferred); every
dimension with no legacy source stays an explicit, visible unknown (per
app.demand_policy.unknown) -- never a guessed default. This mirrors
app.demand.create_demand_profile's own "every field the human did not
supply is an honest empty/unknowns entry" discipline, just going the
other direction.
"""

from __future__ import annotations

from typing import Any

from app.demand_policy import known, unknown


def map_from_enterprise_profile(
    profile: dict[str, Any],
    *,
    demand_id: str,
    workspace_id: str,
    company_entity_id: str,
    claim_ids: list[str] | None = None,
    origin_profile_ref: str | None,
    created_at: str,
    updated_at: str,
) -> dict[str, Any]:
    evidence_claims = profile.get("evidence_claims") or []
    problem_statement = evidence_claims[0]["statement"] if evidence_claims and evidence_claims[0].get("statement") else None

    capability_gaps = [g for g in (profile.get("capability_gaps") or []) if g]
    buying_context = profile.get("buying_context") or {}
    sponsors = [s for s in (buying_context.get("sponsors") or []) if s]
    timing_signals = [t for t in (buying_context.get("timing_signals") or []) if t]

    return {
        "demand_id": demand_id,
        "workspace_id": workspace_id,
        "company_entity_id": company_entity_id,
        "status": "observed",
        "problem": known(problem_statement) if problem_statement else unknown(),
        # No legacy field maps to population/urgency/initiative/budget --
        # these stay explicit unknowns rather than being guessed from
        # adjacent legacy data.
        "population": unknown(),
        "impact": known("; ".join(capability_gaps)) if capability_gaps else unknown(),
        "urgency": unknown(),
        "initiative": unknown(),
        "sponsor": known("; ".join(sponsors)) if sponsors else unknown(),
        "budget": unknown(),
        "timing": known("; ".join(timing_signals)) if timing_signals else unknown(),
        "claim_ids": list(claim_ids or []),
        "origin_profile_ref": origin_profile_ref,
        "created_at": created_at,
        "updated_at": updated_at,
    }
