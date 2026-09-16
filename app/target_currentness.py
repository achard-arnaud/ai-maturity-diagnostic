"""Epic 08 S02: currentness/authority/warm-path evidence policies.

Stop condition: "ready strict" -- a stakeholder is only ever "ready" for
Reach (Epic 09) under a strict, explicit set of conditions: their
relationship currentness must be resolved current (not stale, not a
conflict needing human review), and for authority-bearing roles
(sponsor/champion) their assigned authority must be evidenced by
something beyond a job title -- this Epic's own invariant ("un titre de
poste ne prouve ni autorité ni rôle").
"""

from __future__ import annotations

from dataclasses import dataclass

AUTHORITY_ROLES = frozenset({"sponsor", "champion"})
_WEAK_CONFIDENCE = frozenset({"low", "unknown"})


@dataclass(frozen=True)
class ReadinessResult:
    ready: bool
    reasons: tuple[str, ...]


def evaluate_readiness(
    *,
    role: str,
    currentness_is_current: bool | None,
    currentness_requires_review: bool,
    influence_confidence: str,
) -> ReadinessResult:
    reasons: list[str] = []

    if currentness_requires_review:
        reasons.append("currentness conflict requires human review")
    elif currentness_is_current is not True:
        reasons.append("currentness insufficient -- relationship is not current")

    if role in AUTHORITY_ROLES and influence_confidence in _WEAK_CONFIDENCE:
        reasons.append(
            "authority not evidenced beyond title -- a job title alone never proves authority"
        )

    return ReadinessResult(ready=not reasons, reasons=tuple(reasons))
