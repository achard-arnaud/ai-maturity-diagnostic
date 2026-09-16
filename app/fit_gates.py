"""Epic 07 S02: hard gates/blockers/resolvers policy engine.

Stop condition: "aucun score bypass" (no score bypass) -- this module is
the one gate a score must pass through. per
08_EVIDENCE_DECISION_AND_GATES.md's gate order (completeness/provenance,
freshness, hard gates, blockers, THEN scoring) and this Epic's own
invariant ("un score sans gate critique résolue ne produit jamais
PURSUE"): can_compute_score is false the instant any hard gate fails or
any blocker remains open, with no parameter, flag, or code path in this
module able to override that.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence


@dataclass(frozen=True)
class GateResult:
    gate_id: str
    name: str
    passed: bool
    reason: str | None = None


@dataclass(frozen=True)
class ResolverContract:
    why_blocked: str
    required_state_or_evidence: str
    owner_capability: str
    cta: str
    postcondition: str
    cost_estimate: str
    expiry: str | None


def evaluate_hard_gates(product_snapshot: Mapping, gate_checks: Sequence[Mapping]) -> list[GateResult]:
    """gate_checks is the caller-supplied evaluation of each of the
    product snapshot's hard_gates (each {"gate_id", "passed", "reason"?})
    -- this module doesn't itself decide *how* a gate is checked (that's
    domain-specific, e.g. a compliance questionnaire), only enforces that
    every hard_gate named on the snapshot has a corresponding result."""
    hard_gate_names = list(product_snapshot["content"]["hard_gates"])
    checks_by_name = {c["gate_id"]: c for c in gate_checks}
    results = []
    for name in hard_gate_names:
        check = checks_by_name.get(name)
        if check is None:
            results.append(GateResult(gate_id=name, name=name, passed=False, reason="not yet evaluated"))
        else:
            results.append(
                GateResult(gate_id=name, name=name, passed=bool(check["passed"]), reason=check.get("reason"))
            )
    return results


def can_compute_score(gates: Sequence[GateResult], *, open_blocker_count: int) -> bool:
    """The single choke point: true only if every gate passed and there
    are zero open blockers. No parameter here can force true when either
    condition is false -- this is deliberately the *only* function in
    this module that decides scorability, so there is exactly one place
    to audit for a bypass."""
    if open_blocker_count > 0:
        return False
    return all(g.passed for g in gates)


def failed_gate_reasons(gates: Sequence[GateResult]) -> list[str]:
    return [f"{g.name}: {g.reason or 'failed'}" for g in gates if not g.passed]


def resolve_gate_blocker(gate: GateResult) -> ResolverContract | None:
    if gate.passed:
        return None
    return ResolverContract(
        why_blocked=f"hard gate {gate.name!r} failed: {gate.reason or 'no reason recorded'}",
        required_state_or_evidence=f"evidence that {gate.name!r} is satisfied",
        owner_capability="fit_reviewer",
        cta=f"Provide evidence resolving gate {gate.name!r}, or reject the fit.",
        postcondition=f"gate {gate.name!r} re-evaluated as passed",
        cost_estimate="unknown -- depends on the gate",
        expiry=None,
    )
