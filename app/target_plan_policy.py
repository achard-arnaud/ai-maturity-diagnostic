"""Epic 08 S01: TargetPlan/StakeholderRole/Influence semantics.

Stop condition: "rôles ≠ titres" (roles are not titles) -- a person's
job `title` is carried on their StakeholderRole record purely as
informational context; no function in this module reads `title` to
infer, default, validate, or constrain `role`. The two are deliberately
independent inputs supplied separately by the caller.
"""

from __future__ import annotations

from typing import Mapping, Sequence

SINGULAR_ROLES = frozenset({"sponsor", "champion"})
ALL_ROLES = frozenset({"sponsor", "champion", "user", "prescripteur", "technique", "procurement", "blocker"})


class TargetPlanPolicyError(Exception):
    pass


class RoleCardinalityError(TargetPlanPolicyError):
    pass


def assign_stakeholder_role(
    *,
    stakeholder_role_id: str,
    target_plan_id: str,
    person_entity_id: str,
    role: str,
    title: str,
    assigned_by: str,
    assigned_at: str,
) -> dict:
    """Build a StakeholderRole record. `role` and `title` are accepted as
    two entirely independent parameters -- this function never derives
    one from the other, and never rejects a combination (e.g. title="CEO"
    with role="user") as inconsistent. That independence *is* the "rôles
    ≠ titres" invariant."""
    if role not in ALL_ROLES:
        raise TargetPlanPolicyError(f"unknown role {role!r}; must be one of {sorted(ALL_ROLES)}")
    return {
        "stakeholder_role_id": stakeholder_role_id,
        "target_plan_id": target_plan_id,
        "person_entity_id": person_entity_id,
        "role": role,
        "title": title,
        "status": "active",
        "assigned_at": assigned_at,
        "assigned_by": assigned_by,
        "supersedes_stakeholder_role_id": None,
    }


def validate_role_cardinality(existing_roles: Sequence[Mapping], new_role: str) -> None:
    """Raises RoleCardinalityError if assigning new_role would exceed
    this role's cardinality among currently *active* stakeholders on the
    same plan. sponsor/champion are singular; every other role is
    unbounded."""
    if new_role not in SINGULAR_ROLES:
        return
    active_same_role = [r for r in existing_roles if r["status"] == "active" and r["role"] == new_role]
    if active_same_role:
        raise RoleCardinalityError(
            f"role {new_role!r} is singular per plan -- an active {new_role} already exists "
            f"({active_same_role[0]['stakeholder_role_id']})"
        )


def supersede_stakeholder_role(old_role: Mapping) -> dict:
    updated = dict(old_role)
    updated["status"] = "superseded"
    return updated
