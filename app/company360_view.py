"""Company 360 read model (Epic 04 S05).

Aggregates ResearchCases, Claims (grouped by truth type) and Evidence for
one company. Per the Epic's own invariant ("recherche product-blind") and
02_DOMAIN_AND_TRUTH_MODEL.md's Account Intelligence context ("claims,
dossier, maturité, initiatives" -- never "offre recommandée"), this view
never carries a product/catalog/offer/fit field. See
tests/test_company360_view.py's structural "product data absente" guard,
mirroring app.signal_screening's "never a fit score" guard from Epic 03.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.claim_store import list_claims
from app.evidence_store import list_evidence
from app.research_case_store import list_cases
from app.research_redteam import find_contradictions

_CLAIM_TYPES = ("fact", "inference", "hypothesis")

_FORBIDDEN_FIELD_TOKENS = ("product", "catalog", "offer", "fit", "recommend")


def get_company_360(root: Path, workspace_id: str, company_entity_id: str) -> dict[str, Any]:
    research_cases = [
        case
        for case in list_cases(root, workspace_id, limit=100).items
        if case["company_entity_id"] == company_entity_id
    ]
    claims = list_claims(root, workspace_id, company_entity_id=company_entity_id)
    evidence = list_evidence(root, workspace_id, entity_ref=company_entity_id)

    claims_by_type: dict[str, list[dict[str, Any]]] = {t: [] for t in _CLAIM_TYPES}
    for claim in claims:
        if claim["status"] == "active":
            claims_by_type[claim["claim_type"]].append(claim)

    unknowns = [
        claim
        for claim in claims_by_type["hypothesis"]
        if claim.get("hypothesis_due_at") is not None
    ]

    contradictions = find_contradictions(claims)

    return {
        "company_entity_id": company_entity_id,
        "research_cases": research_cases,
        "claims": claims_by_type,
        "unknowns": unknowns,
        "contradictions": contradictions,
        "evidence_count": len(evidence),
    }
