#!/usr/bin/env python3
"""Build evidence-bounded reach hypothesis records from fit and private contact targets."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from network_common import dump_yaml, load_yaml, stable_id, utc_now
from qualification_common import POSITIVE_FIT_DECISIONS, normalized_decision, selected_match


def claim_parts(items: list[Any]) -> tuple[list[str], list[str]]:
    ids: list[str] = []
    statements: list[str] = []
    for item in items:
        if isinstance(item, dict):
            identifier = item.get("claim_id") or item.get("id")
            statement = item.get("statement") or item.get("priority") or item.get("gap")
            if identifier:
                ids.append(str(identifier))
            if statement:
                statements.append(str(statement))
        elif isinstance(item, str):
            statements.append(item)
    return ids, statements


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("study_dir", type=Path)
    args = parser.parse_args()
    study = args.study_dir.resolve()
    manifest = load_yaml(study / "00_manifest.yaml")
    fit = load_yaml(study / "06_product_fit_matrix.yaml")
    profile = load_yaml(study / "05_enterprise_demand_profile.yaml")
    targets = load_yaml(study / "06b_contact_targets.yaml")
    offer_id = fit.get("recommended_offer_id")
    decision = normalized_decision(fit.get("decision"))
    if decision not in POSITIVE_FIT_DECISIONS:
        parser.error("Reach hypotheses require a selected PURSUE or VALIDATE fit")
    try:
        match = selected_match(fit)
    except ValueError as exc:
        parser.error(f"Invalid selected fit: {exc}")
    if targets.get("study_id") != manifest.get("study_id") or targets.get("company_id") != manifest.get("company_id"):
        parser.error("Contact targets do not belong to this study/company")
    if targets.get("offer_id") != offer_id or normalized_decision(targets.get("fit_decision")) != decision:
        parser.error("Contact targets are stale or inconsistent with the selected fit")
    if targets.get("fit_score") != match.get("score"):
        parser.error("Contact targets are stale relative to the selected fit score")
    snapshot = next(
        (item for item in manifest.get("product_snapshots", []) if item.get("offer_id") == offer_id), None
    )
    if not snapshot:
        parser.error("Recommended product snapshot is missing")
    product = load_yaml(study / snapshot["path"])["offer"]
    priority_ids, priority_statements = claim_parts(profile.get("strategic_priorities", []))
    gap_ids, gap_statements = claim_parts(profile.get("capability_gaps", []))
    proof = product.get("proof", {})
    proof_refs = [value for value in [proof.get("source_registry")] if value]
    hypotheses: list[dict[str, Any]] = []
    for target in targets.get("targets", []):
        missing: list[str] = []
        if not priority_ids:
            missing.append("Source-backed strategic priority claim ID")
        if not gap_ids:
            missing.append("Source-backed capability-gap claim ID")
        if not proof_refs:
            missing.append("Product evidence reference")
        if target.get("current_role_status") != "current":
            missing.append("Dated validation of the contact's current role")
        priority = priority_statements[0] if priority_statements else None
        gap = gap_statements[0] if gap_statements else None
        hypothesis = {
            "reach_id": stable_id("REACH", manifest["study_id"], target["person_id"], str(offer_id)),
            "person_id": target["person_id"],
            "target_id": target["target_id"],
            "status": "blocked" if missing else "ready",
            "verified_priority_claim_ids": priority_ids[:3],
            "capability_gap_claim_ids": gap_ids[:3],
            "product_evidence_refs": proof_refs,
            "angle_components": {
                "verified_priority": priority,
                "observed_gap": gap,
                "relevant_offer_proof": proof.get("evidence_status"),
            },
            "validation_question": f"Dans quelle mesure « {gap} » constitue-t-il aujourd’hui un blocage prioritaire ?" if gap else None,
            "missing_inputs": missing,
        }
        hypotheses.append(hypothesis)
    output = {
        "schema_version": "0.3",
        "generated_at": utc_now(),
        "study_id": manifest["study_id"],
        "company_id": manifest.get("company_id"),
        "offer_id": offer_id,
        "fit_decision": fit.get("decision"),
        "fit_score": match.get("score"),
        "hypotheses": hypotheses,
        "privacy": "Resolve person IDs only in the private network registry.",
    }
    dump_yaml(study / "07b_reach_hypotheses.yaml", output)
    print(f"ready={sum(item['status'] == 'ready' for item in hypotheses)} blocked={sum(item['status'] == 'blocked' for item in hypotheses)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
