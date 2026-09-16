"""Epic 08 S03: plan builder and validation workflow.

Stop condition: "blockers actionnables" (actionable blockers) -- a
TargetPlan that isn't ready to activate always comes with a concrete,
actionable resolver per problem stakeholder, never a bare "not ready"
verdict.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from app.fit_targeting_gate import can_create_target_plan
from app.target_currentness import AUTHORITY_ROLES, ReadinessResult


class TargetPlanWorkflowError(Exception):
    pass


def create_target_plan(
    fit_assessment: Mapping[str, Any],
    *,
    target_plan_id: str,
    workspace_id: str,
    company_entity_id: str,
    created_at: str,
) -> dict[str, Any]:
    """The only constructor for a TargetPlan -- per 'fit avant ciblage',
    refuses unless the fit assessment already authorizes targeting."""
    allowed, reason = can_create_target_plan(fit_assessment, now=created_at)
    if not allowed:
        raise TargetPlanWorkflowError(f"cannot create target plan: {reason}")
    return {
        "target_plan_id": target_plan_id,
        "workspace_id": workspace_id,
        "company_entity_id": company_entity_id,
        "fit_assessment_id": fit_assessment["fit_assessment_id"],
        "status": "draft",
        "created_at": created_at,
        "updated_at": None,
    }


@dataclass(frozen=True)
class StakeholderBlocker:
    stakeholder_role_id: str
    why_blocked: str
    cta: str


def build_stakeholder_blockers(
    active_stakeholders: Sequence[Mapping[str, Any]],
    readiness_by_stakeholder_id: Mapping[str, ReadinessResult],
) -> list[StakeholderBlocker]:
    """One actionable blocker per not-ready active stakeholder -- never
    a bare failure with no next step."""
    blockers = []
    for stakeholder in active_stakeholders:
        result = readiness_by_stakeholder_id.get(stakeholder["stakeholder_role_id"])
        if result is None or result.ready:
            continue
        blockers.append(
            StakeholderBlocker(
                stakeholder_role_id=stakeholder["stakeholder_role_id"],
                why_blocked="; ".join(result.reasons),
                cta=f"Resolve: {'; '.join(result.reasons)} for {stakeholder['role']} {stakeholder['person_entity_id']}.",
            )
        )
    return blockers


def can_activate_plan(
    active_stakeholders: Sequence[Mapping[str, Any]],
    readiness_by_stakeholder_id: Mapping[str, ReadinessResult],
) -> tuple[bool, list[StakeholderBlocker]]:
    """A plan can activate only once at least one active, ready
    authority-role (sponsor/champion) stakeholder exists. Every not-ready
    active stakeholder (whatever their role) surfaces its own actionable
    blocker regardless of whether it's what's stopping activation."""
    blockers = build_stakeholder_blockers(active_stakeholders, readiness_by_stakeholder_id)

    has_ready_authority = any(
        s["role"] in AUTHORITY_ROLES and readiness_by_stakeholder_id.get(s["stakeholder_role_id"], ReadinessResult(False, ())).ready
        for s in active_stakeholders
    )
    if not has_ready_authority:
        blockers = [
            StakeholderBlocker(
                stakeholder_role_id="",
                why_blocked="no ready sponsor or champion on this plan",
                cta="Assign and validate a ready sponsor or champion before activating.",
            )
        ] + blockers

    return has_ready_authority, blockers


def activate_plan(plan: Mapping[str, Any], *, activated_at: str, allowed: bool) -> dict[str, Any]:
    if plan["status"] != "draft":
        raise TargetPlanWorkflowError(f"cannot activate plan {plan['target_plan_id']} from status {plan['status']!r}")
    if not allowed:
        raise TargetPlanWorkflowError(f"plan {plan['target_plan_id']} has unresolved activation blockers")
    updated = dict(plan)
    updated["status"] = "active"
    updated["updated_at"] = activated_at
    return updated


def mark_plan_stale(plan: Mapping[str, Any], *, reason: str, marked_at: str) -> dict[str, Any]:
    if not reason.strip():
        raise TargetPlanWorkflowError("marking a plan stale requires a reason")
    updated = dict(plan)
    updated["status"] = "stale"
    updated["updated_at"] = marked_at
    return updated
