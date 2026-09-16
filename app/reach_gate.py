"""Epic 08 S06: the gate Epic 09 (Reach Execution Queue) must call
before initiating outreach to a stakeholder. Stop condition: "reach
gated" -- reach is never initiated for an inactive plan, an inactive
stakeholder, or a stakeholder whose readiness has since lapsed (a
refresh-back check: readiness is evaluated fresh each time, never cached
from plan-activation time).
"""

from __future__ import annotations

from typing import Any

from app.target_currentness import ReadinessResult


def can_initiate_reach(
    plan: dict[str, Any], stakeholder: dict[str, Any], readiness: ReadinessResult
) -> tuple[bool, str | None]:
    if plan["status"] != "active":
        return False, f"target plan is not active (status={plan['status']!r})"
    if stakeholder["status"] != "active":
        return False, f"stakeholder is not active (status={stakeholder['status']!r})"
    if not readiness.ready:
        return False, f"stakeholder not ready: {'; '.join(readiness.reasons)}"
    return True, None
