"""Epic 07 S03: explainable scoring/coverage/gaps/alternatives.

Stop condition: "justification lisible" (readable justification) --
every number this module produces comes with a human-readable factor
breakdown (mirrors Epic 03's signal_screening explicability pattern), and
coverage/gaps/alternatives/counter_evidence are all structured so a
reviewer can see exactly what was and wasn't checked, never a bare
opaque verdict.

This module never decides *how* a dimension is covered (that's
domain-specific human/skill judgment, supplied by the caller as
dimension_checks) -- it only aggregates, weighs, and explains.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

DEFAULT_WEIGHTS: dict[str, float] = {
    "problem": 0.3,
    "population": 0.1,
    "impact": 0.2,
    "urgency": 0.1,
    "initiative": 0.1,
    "sponsor": 0.1,
    "budget": 0.05,
    "timing": 0.05,
}


class FitScoringError(Exception):
    pass


@dataclass(frozen=True)
class CoverageResult:
    covered: tuple[str, ...]
    gaps: tuple[str, ...]
    coverage_ratio: float


def compute_coverage(dimension_checks: Sequence[Mapping]) -> CoverageResult:
    if not dimension_checks:
        return CoverageResult(covered=(), gaps=(), coverage_ratio=0.0)
    covered = tuple(c["dimension"] for c in dimension_checks if c["covered"])
    gaps = tuple(c["dimension"] for c in dimension_checks if not c["covered"])
    ratio = len(covered) / len(dimension_checks)
    return CoverageResult(covered=covered, gaps=gaps, coverage_ratio=ratio)


@dataclass(frozen=True)
class ScoreFactor:
    name: str
    weight: float
    contribution: float


@dataclass(frozen=True)
class ScoreResult:
    value: float
    factors: tuple[ScoreFactor, ...]
    explanation: str


def compute_explainable_score(
    dimension_checks: Sequence[Mapping], *, weights: Mapping[str, float] = DEFAULT_WEIGHTS
) -> ScoreResult:
    """Weighted sum over covered dimensions, each factor's own
    weight/contribution reported -- never a bare float with no
    breakdown."""
    factors = []
    total = 0.0
    for check in dimension_checks:
        dimension = check["dimension"]
        weight = weights.get(dimension, 0.0)
        contribution = weight if check["covered"] else 0.0
        total += contribution
        factors.append(ScoreFactor(name=dimension, weight=weight, contribution=contribution))

    explanation = "; ".join(
        f"{f.name} ({'covered' if f.contribution > 0 else 'gap'}, weight={f.weight:.2f})" for f in factors
    )
    return ScoreResult(value=round(total, 4), factors=tuple(factors), explanation=explanation or "no dimensions evaluated")


def validate_alternatives(alternatives: Sequence[Mapping]) -> None:
    """Every alternative must carry a non-empty description and
    rationale -- a vague or empty placeholder alternative is rejected,
    never silently accepted as a real one."""
    for alt in alternatives:
        if not str(alt.get("description") or "").strip():
            raise FitScoringError("an alternative requires a non-empty description")
        if not str(alt.get("rationale") or "").strip():
            raise FitScoringError("an alternative requires a non-empty rationale")


def validate_counter_evidence(counter_evidence: Sequence[Mapping]) -> None:
    """Every counter-evidence entry must carry non-empty text -- mirrors
    the red-team discipline from Epic 04's research_redteam module."""
    for entry in counter_evidence:
        if not str(entry.get("statement") or "").strip():
            raise FitScoringError("counter-evidence requires a non-empty statement")
