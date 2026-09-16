"""Epic 04 S07: contamination, coverage and factuality evals.

Per 10_LEARNING_LOOP_OBSERVABILITY_AND_QA.md's evals discipline and this
Epic's own acceptance bar ("aucune mention d'offre injectée avant
handoff"), a gold-set-style eval suite runs over a set of ResearchCases
and Claims and checks three thresholds before a release can go:
contamination (zero tolerance -- a single product/offer mention in a
claim statement fails the whole eval), coverage (share of cases that meet
S01's completeness gate), and factuality (share of "fact"-typed claims
whose lineage actually validates, per S01's validate_claim_lineage).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from app.research_policy import compute_completeness, validate_claim_lineage

CONTAMINATION_TOKENS = ("product", "catalog", "offer", "pricing", "sku", "discount")


@dataclass(frozen=True)
class EvalThresholds:
    max_contamination: int = 0
    min_coverage: float = 0.8
    min_factuality: float = 0.9


@dataclass(frozen=True)
class EvalReport:
    contaminated_claim_ids: tuple[str, ...]
    coverage: float
    factuality: float
    thresholds: EvalThresholds
    passed: bool
    failures: tuple[str, ...]


def check_contamination(claims: Sequence[Mapping]) -> list[str]:
    """Return claim_ids whose statement contains banned product/offer
    vocabulary -- a case-insensitive scan of the free-text statement, not
    just the record's field names (S05's structural guard already covers
    the shape; this covers the content)."""
    hits = []
    for claim in claims:
        statement = claim.get("statement", "").lower()
        if any(token in statement for token in CONTAMINATION_TOKENS):
            hits.append(claim["claim_id"])
    return hits


def compute_coverage(cases: Sequence[Mapping], claims_by_case: Mapping[str, Sequence[Mapping]]) -> float:
    """Share of cases whose claim set meets gate-1 completeness."""
    if not cases:
        return 0.0
    complete = sum(
        1 for case in cases
        if compute_completeness(claims_by_case.get(case["research_case_id"], [])).is_complete
    )
    return complete / len(cases)


def compute_factuality(
    claims: Sequence[Mapping],
    *,
    evidence_by_id: Mapping[str, Mapping],
    claims_by_id: Mapping[str, Mapping],
) -> float:
    """Share of "fact"-typed claims whose lineage validates cleanly."""
    fact_claims = [c for c in claims if c["claim_type"] == "fact"]
    if not fact_claims:
        return 0.0
    valid = sum(
        1 for c in fact_claims
        if validate_claim_lineage(c, evidence_by_id=evidence_by_id, claims_by_id=claims_by_id) is None
    )
    return valid / len(fact_claims)


def run_evals(
    cases: Sequence[Mapping],
    claims: Sequence[Mapping],
    *,
    evidence_by_id: Mapping[str, Mapping],
    thresholds: EvalThresholds = EvalThresholds(),
) -> EvalReport:
    claims_by_case: dict[str, list[Mapping]] = {}
    claims_by_id: dict[str, Mapping] = {}
    for claim in claims:
        claims_by_case.setdefault(claim["research_case_id"], []).append(claim)
        claims_by_id[claim["claim_id"]] = claim

    contaminated = check_contamination(claims)
    coverage = compute_coverage(cases, claims_by_case)
    factuality = compute_factuality(claims, evidence_by_id=evidence_by_id, claims_by_id=claims_by_id)

    failures = []
    if len(contaminated) > thresholds.max_contamination:
        failures.append(f"contamination: {len(contaminated)} claim(s) exceed max {thresholds.max_contamination}")
    if coverage < thresholds.min_coverage:
        failures.append(f"coverage: {coverage:.2f} below min {thresholds.min_coverage:.2f}")
    if factuality < thresholds.min_factuality:
        failures.append(f"factuality: {factuality:.2f} below min {thresholds.min_factuality:.2f}")

    return EvalReport(
        contaminated_claim_ids=tuple(contaminated),
        coverage=coverage,
        factuality=factuality,
        thresholds=thresholds,
        passed=not failures,
        failures=tuple(failures),
    )
