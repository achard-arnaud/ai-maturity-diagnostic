"""Epic 11 S01: commercial object link integrity.

This module deliberately contains no stage-transition policy.  Its sole
responsibility is to make the upstream chain explicit and reject a raw
prospect (or a cross-workspace reference) before it can enter Pipeline.
"""

from __future__ import annotations

from typing import Mapping


class OpportunityLinkError(ValueError):
    """Raised when a canonical commercial record breaks its lineage."""


class OpportunityLifecycleError(ValueError):
    """Raised when qualification, conversion or a stage gate is not met."""


OPPORTUNITY_STAGES = ("draft", "discovery", "proof", "proposal", "closed_won", "closed_lost")
_NEXT_STAGES = {
    "draft": frozenset({"discovery"}),
    "discovery": frozenset({"proof"}),
    "proof": frozenset({"proposal"}),
    "proposal": frozenset({"closed_won", "closed_lost"}),
    "closed_won": frozenset(),
    "closed_lost": frozenset(),
}
_EXIT_CRITERIA = {
    "discovery": frozenset({"lead_converted"}),
    "proof": frozenset({"discovery_recorded", "stakeholders_confirmed"}),
    "proposal": frozenset({"proof_completed", "success_criteria_met"}),
    "closed_won": frozenset({"commercial_decision_recorded", "customer_acceptance_recorded"}),
    "closed_lost": frozenset({"commercial_decision_recorded", "loss_reason_recorded"}),
}


def qualify_lead(
    lead: Mapping[str, object], *, fit_verdict: str, target_plan_status: str, engagement_kind: str,
) -> dict:
    """Return a qualified Lead only after the three upstream commercial gates.

    A meeting alone never creates a pipeline record: the Fit must have been
    decided PURSUE and the TargetPlan must be active.  The function is kept
    separate from conversion so human qualification cannot silently create an
    Opportunity.
    """
    if fit_verdict != "PURSUE":
        raise OpportunityLifecycleError("lead qualification requires a PURSUE fit verdict")
    if target_plan_status != "active":
        raise OpportunityLifecycleError("lead qualification requires an active target plan")
    if engagement_kind != "meeting_booked":
        raise OpportunityLifecycleError("lead qualification requires a meeting_booked engagement")
    qualified = dict(lead)
    qualified["status"] = "qualified"
    return qualified


def convert_lead(lead: Mapping[str, object]) -> dict:
    """Mark an already qualified Lead converted; no Opportunity is created here."""
    if lead["status"] != "qualified":
        raise OpportunityLifecycleError("only a qualified lead can be converted")
    converted = dict(lead)
    converted["status"] = "converted"
    return converted


def required_exit_criteria(next_stage: str) -> frozenset[str]:
    """Expose the exact, stable set of evidence required to enter a stage."""
    if next_stage not in _EXIT_CRITERIA:
        raise OpportunityLifecycleError(f"{next_stage!r} is not an enterable opportunity stage")
    return _EXIT_CRITERIA[next_stage]


def transition_opportunity(
    opportunity: Mapping[str, object], *, next_stage: str, completed_criteria: set[str] | frozenset[str],
) -> dict:
    """Advance exactly one allowed stage after all named exit criteria pass."""
    current_stage = str(opportunity["status"])
    if next_stage not in _NEXT_STAGES.get(current_stage, frozenset()):
        raise OpportunityLifecycleError(f"cannot skip from {current_stage!r} to {next_stage!r}")
    missing = _EXIT_CRITERIA[next_stage] - set(completed_criteria)
    if missing:
        raise OpportunityLifecycleError(f"missing exit criteria for {next_stage}: {sorted(missing)}")
    transitioned = dict(opportunity)
    transitioned["status"] = next_stage
    return transitioned


def _same_workspace(*records: Mapping[str, object]) -> None:
    workspaces = {record["workspace_id"] for record in records}
    if len(workspaces) != 1:
        raise OpportunityLinkError("commercial records must belong to one workspace")


def validate_opportunity_links(lead: Mapping[str, object], opportunity: Mapping[str, object]) -> None:
    """Validate the Lead -> Opportunity boundary without inferring qualification.

    The caller must supply a Lead already marked ``qualified``.  A prospect
    cannot be substituted because it has neither this status nor the required
    Demand/Fit/TargetPlan lineage.
    """
    _same_workspace(lead, opportunity)
    if lead["status"] != "qualified":
        raise OpportunityLinkError("only a qualified lead can create an opportunity")
    if opportunity["lead_id"] != lead["lead_id"]:
        raise OpportunityLinkError("opportunity must reference its qualifying lead")
    for field in ("demand_id", "fit_assessment_id", "target_plan_id"):
        if opportunity[field] != lead[field]:
            raise OpportunityLinkError(f"opportunity {field} must preserve lead lineage")


def validate_commercial_chain(
    lead: Mapping[str, object],
    opportunity: Mapping[str, object],
    proof: Mapping[str, object],
    deal: Mapping[str, object],
    expansion: Mapping[str, object],
) -> None:
    """Check the immutable Lead -> Opportunity -> Proof -> Deal -> Expansion chain."""
    validate_opportunity_links(lead, opportunity)
    _same_workspace(lead, opportunity, proof, deal, expansion)
    if proof["opportunity_id"] != opportunity["opportunity_id"]:
        raise OpportunityLinkError("proof must reference its opportunity")
    if deal["opportunity_id"] != opportunity["opportunity_id"] or deal["proof_id"] != proof["proof_id"]:
        raise OpportunityLinkError("deal must reference the opportunity and its proof")
    if expansion["deal_id"] != deal["deal_id"]:
        raise OpportunityLinkError("expansion must reference its deal")
