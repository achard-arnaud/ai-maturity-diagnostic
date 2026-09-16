"""Epic 07 S06: the one gate Epic 08 (Buying Committee and Target Plans)
must call before creating a TargetPlan. Stop condition: "target creation
gated" -- a TargetPlan can never be created from a FitAssessment that
hasn't reached an authorized PURSUE verdict, including when that PURSUE
was itself a now-expired override (which must be re-reviewed, not
treated as a standing authorization).
"""

from __future__ import annotations

from typing import Any

from app.fit_lifecycle import is_override_expired


def can_create_target_plan(fit_assessment: dict[str, Any], *, now: str) -> tuple[bool, str | None]:
    """Returns (allowed, reason). reason is None iff allowed is True."""
    if fit_assessment["status"] != "decided":
        return False, f"fit assessment is not decided (status={fit_assessment['status']!r})"

    verdict = fit_assessment.get("verdict")
    if not verdict or verdict.get("verdict") != "PURSUE":
        return False, f"fit verdict is not PURSUE (verdict={(verdict or {}).get('verdict')!r})"

    if is_override_expired(verdict, now=now):
        return False, "the PURSUE override has expired and must be re-reviewed"

    return True, None
