"""Epic 11 S01: commercial object link integrity.

This module deliberately contains no stage-transition policy.  Its sole
responsibility is to make the upstream chain explicit and reject a raw
prospect (or a cross-workspace reference) before it can enter Pipeline.
"""

from __future__ import annotations

from typing import Mapping


class OpportunityLinkError(ValueError):
    """Raised when a canonical commercial record breaks its lineage."""


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
