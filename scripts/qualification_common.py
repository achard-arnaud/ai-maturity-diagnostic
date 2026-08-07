"""Shared invariants for product-fit validation and downstream handoffs."""

from __future__ import annotations

from typing import Any


FIT_DIMENSION_WEIGHTS: dict[str, int] = {
    "problem_fit": 20,
    "strategic_relevance": 15,
    "gap_fit": 15,
    "urgency": 10,
    "technical_fit": 10,
    "organizational_fit": 10,
    "access_fit": 10,
    "proofability": 5,
    "evidence_confidence": 5,
}
FIT_DECISIONS = {"pursue", "validate", "nurture", "disqualify"}
POSITIVE_FIT_DECISIONS = {"pursue", "validate"}
GATE_STATUSES = {"PASS", "OPEN", "FAIL"}
GATE_SEVERITIES = {"blocker", "critical"}


def normalized_decision(value: Any) -> str | None:
    if value is None:
        return None
    return str(value).strip().lower()


def weighted_fit_score(match: dict[str, Any]) -> float | None:
    """Return the canonical weighted score, or None when dimensions are invalid."""
    total = 0.0
    for field, weight in FIT_DIMENSION_WEIGHTS.items():
        value = match.get(field)
        if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 5:
            return None
        total += value / 5 * weight
    return round(total, 2)


def gate_errors(match: dict[str, Any]) -> list[str]:
    """Validate hard-gate records and their consequences for the match decision."""
    errors: list[str] = []
    decision = normalized_decision(match.get("decision"))
    gates = match.get("hard_gates")
    if not isinstance(gates, list):
        return ["hard_gates must be a list"]

    blocking_open = False
    blocking_fail = False
    seen_ids: set[str] = set()
    for gate in gates:
        if not isinstance(gate, dict):
            errors.append("hard_gates contains a non-object record")
            continue
        gate_id = gate.get("id")
        status = str(gate.get("status", "")).upper()
        severity = str(gate.get("severity", "")).lower()
        if not isinstance(gate_id, str) or not gate_id.strip():
            errors.append("hard gate is missing a non-empty id")
        elif gate_id in seen_ids:
            errors.append(f"duplicate hard gate id {gate_id}")
        else:
            seen_ids.add(gate_id)
        if status not in GATE_STATUSES:
            errors.append(f"gate {gate_id or '<missing>'} has invalid status")
        if severity not in GATE_SEVERITIES:
            errors.append(f"gate {gate_id or '<missing>'} has invalid severity")
        if severity in GATE_SEVERITIES and status == "OPEN":
            blocking_open = True
        if severity in GATE_SEVERITIES and status == "FAIL":
            blocking_fail = True

    if decision == "pursue" and (blocking_open or blocking_fail):
        errors.append("PURSUE is forbidden with an OPEN or FAIL blocker/critical gate")
    if decision == "validate" and blocking_fail:
        errors.append("VALIDATE is forbidden with a FAIL blocker/critical gate")
    return errors


def selected_match(fit: dict[str, Any]) -> dict[str, Any]:
    """Return the uniquely selected match after checking decision coordination."""
    offer_id = fit.get("recommended_offer_id")
    decision = normalized_decision(fit.get("decision"))
    if not isinstance(offer_id, str) or not offer_id:
        raise ValueError("A recommended_offer_id is required for this downstream handoff")
    if decision not in FIT_DECISIONS:
        raise ValueError("The top-level fit decision is missing or invalid")
    matches = fit.get("matches")
    if not isinstance(matches, list):
        raise ValueError("Fit matches must be a list")
    selected = [item for item in matches if isinstance(item, dict) and item.get("offer_id") == offer_id]
    if len(selected) != 1:
        raise ValueError("The recommended offer must resolve to exactly one match record")
    match = selected[0]
    match_decision = normalized_decision(match.get("decision"))
    if decision != match_decision:
        raise ValueError("Top-level decision must equal the recommended match decision")
    gate_problems = gate_errors(match)
    if gate_problems:
        raise ValueError("; ".join(gate_problems))
    expected = weighted_fit_score(match)
    score = match.get("score")
    if expected is None:
        raise ValueError("The selected match has invalid fit dimensions")
    if not isinstance(score, (int, float)) or isinstance(score, bool):
        raise ValueError("The selected match requires a numeric weighted score")
    if abs(float(score) - expected) > 0.01:
        raise ValueError(f"Selected match score {score} does not equal weighted score {expected:g}")
    return match
