"""Epic 05 S05: qualification-blocker resolver.

Per 08_EVIDENCE_DECISION_AND_GATES.md's resolver contract (`why_blocked`,
`required_state_or_evidence`, `owner_capability`, `cta`, `postcondition`,
`cost_estimate`, `expiry`): when a Demand fails S02's qualification
checklist, this turns the bare missing-dimension list into a full,
actionable resolver a UI can render directly -- never just a raw
validation error.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from app.demand_lifecycle import run_qualification_checklist


@dataclass(frozen=True)
class ResolverContract:
    why_blocked: str
    required_state_or_evidence: tuple[str, ...]
    owner_capability: str
    cta: str
    postcondition: str
    cost_estimate: str
    expiry: str | None


def resolve_qualification_blocker(demand: Mapping) -> ResolverContract | None:
    """Returns None when the demand is not blocked (checklist passes);
    otherwise a full resolver contract naming exactly what unblocks it."""
    checklist = run_qualification_checklist(demand)
    if checklist.passed:
        return None
    return ResolverContract(
        why_blocked="; ".join(checklist.missing),
        required_state_or_evidence=checklist.missing,
        owner_capability="demand_owner",
        cta="Complete intake: capture the missing dimension(s) with a sourced claim.",
        postcondition="qualification checklist passes (problem known, >=1 buying signal known)",
        cost_estimate="low (single intake update)",
        expiry=None,
    )
