"""Screening score: explicable, bounded to research priority (Epic 03 S04).

Stop condition is "score borne a recherche": this module computes a
*research priority* score, never a product-fit score. It has no
knowledge of any product, offer, or catalog -- see Epic 00 Principle #2
("Recherche entreprise product-blind jusqu'au matching") -- and its
output type structurally cannot carry a fit-shaped field (see
test_signal_screening.py's test that walks every key of a computed score
and rejects anything resembling recommended_offer/fit/score_for_offer).

Hard exclusions run first and are absolute: an excluded signal always
scores 0 with a stated reason, regardless of how fresh or well-evidenced
it looks. A score never overrides a hard exclusion -- same rule Epic 00's
qualification gates already establish for hard gates vs. scoring.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.signal_policy import is_expired

_EVIDENCE_GRADE_WEIGHT = {"P1": 1.0, "P2": 0.75, "U1": 0.5, "W1": 0.25, "N0": 0.0}
_SOURCE_KIND_WEIGHT = {"public": 0.6, "manual": 1.0, "import": 0.4}
_TERMINAL_STATUSES = frozenset({"dismissed", "expired"})


@dataclass(frozen=True)
class ScoreFactor:
    name: str
    weight: float
    contribution: float


@dataclass(frozen=True)
class ResearchPriorityScore:
    score: float
    excluded: bool
    exclusion_reason: str | None
    factors: tuple[ScoreFactor, ...]

    def explanation(self) -> list[dict[str, Any]]:
        return [{"name": f.name, "weight": f.weight, "contribution": f.contribution} for f in self.factors]


def _excluded(signal: dict[str, Any]) -> str | None:
    if signal["status"] in _TERMINAL_STATUSES:
        return f"signal status is {signal['status']!r}"
    if is_expired(signal):
        return "signal has passed its freshness window"
    return None


def compute_research_priority_score(signal: dict[str, Any]) -> ResearchPriorityScore:
    """Compute an explicable research-priority score for one signal.

    Never a fit/offer score: it only ever answers "how much should this
    signal raise a company's research priority", not "does this company
    need our product".
    """

    reason = _excluded(signal)
    if reason is not None:
        return ResearchPriorityScore(score=0.0, excluded=True, exclusion_reason=reason, factors=())

    evidence_weight = _EVIDENCE_GRADE_WEIGHT[signal["provenance"]["evidence_grade"]]
    source_weight = _SOURCE_KIND_WEIGHT[signal["source"]["kind"]]

    factors = (
        ScoreFactor(name="evidence_grade", weight=0.6, contribution=0.6 * evidence_weight),
        ScoreFactor(name="source_kind", weight=0.4, contribution=0.4 * source_weight),
    )
    total = sum(f.contribution for f in factors)
    return ResearchPriorityScore(score=round(total, 4), excluded=False, exclusion_reason=None, factors=factors)
