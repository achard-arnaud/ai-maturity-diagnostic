#!/usr/bin/env python3
"""Rank private network contacts after a company-product fit decision exists."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

from network_common import ROOT, dump_yaml, load_yaml, normalize, read_jsonl, stable_id, utc_now
from qualification_common import POSITIVE_FIT_DECISIONS, normalized_decision, selected_match


PERSONA_PATTERNS = {
    "CIO": r"\b(cio|chief information officer|information systems director|it director)\b",
    "CTO": r"\b(cto|chief technology officer|technology director)\b",
    "CPO": r"\b(cpo|chief product officer|product director)\b",
    "CDO": r"\b(cdo|chief data officer|chief digital officer|data director|digital director)\b",
    "CISO": r"\b(ciso|chief information security officer|security director)\b",
    "Head_of_Engineering": r"\b(head of engineering|engineering director|vp engineering)\b",
    "Engineering_Manager": r"\b(engineering manager)\b",
    "Platform_Lead": r"\b(platform lead|head of platform|platform manager)\b",
    "Product_Engineering_Lead": r"\b(product engineering|engineering lead)\b",
    "Transformation_Lead": r"\b(transformation.*(lead|director|head)|head of transformation)\b",
    "PMO_Director": r"\b(pmo.*(director|head)|head of pmo)\b",
    "AI_Lead": r"\b(head of ai|ai lead|artificial intelligence officer)\b",
    "Data_or_Security_Governance": r"\b(data governance|security governance|risk|compliance)\b",
    "Architecture": r"\b(architect|architecture)\b",
}


def persona_matches(title: str, personas: list[str]) -> list[str]:
    normalized = normalize(title)
    matches: list[str] = []
    for persona in personas:
        pattern = PERSONA_PATTERNS.get(persona)
        if pattern and re.search(pattern, normalized, flags=re.I):
            matches.append(persona)
    return matches


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("study_dir", type=Path)
    parser.add_argument("--data-root", type=Path, default=ROOT / "data" / "private")
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()
    study = args.study_dir.resolve()
    manifest = load_yaml(study / "00_manifest.yaml")
    fit = load_yaml(study / "06_product_fit_matrix.yaml")
    company_id = manifest.get("company_id")
    if not company_id:
        parser.error("Study manifest has no company_id; rebuild or link the study through the network queue")
    offer_id = fit.get("recommended_offer_id")
    fit_decision = normalized_decision(fit.get("decision"))
    if not offer_id or fit_decision not in POSITIVE_FIT_DECISIONS:
        parser.error("Contact targeting requires a recommended offer with PURSUE or VALIDATE")
    try:
        match = selected_match(fit)
    except ValueError as exc:
        parser.error(f"Invalid selected fit: {exc}")
    snapshot_record = next(
        (item for item in manifest.get("product_snapshots", []) if item.get("offer_id") == offer_id), None
    )
    if not snapshot_record:
        parser.error("Recommended offer snapshot is missing")
    product = load_yaml(study / snapshot_record["path"])["offer"]
    persona_group = product.get("icp", {}).get("personas", {})
    expected = {
        "economic_sponsor": list(persona_group.get("economic_sponsors", [])),
        "terrain_owner": list(persona_group.get("terrain_owners", [])),
        "veto_player": list(persona_group.get("veto_players", [])),
    }
    all_personas = [item for values in expected.values() for item in values]

    network_dir = args.data_root.resolve() / "network"
    relations = [
        item for item in read_jsonl(network_dir / "relationships.jsonl") if item.get("company_id") == company_id
    ]
    targets: list[dict[str, Any]] = []
    for relation in relations:
        role_types = {item.get("role") for item in relation.get("role_hypotheses", [])}
        matches = persona_matches(relation.get("job_title", ""), all_personas)
        score = 0
        if "economic_sponsor" in role_types:
            score += 40
        if "technical_sponsor" in role_types:
            score += 30
        if "terrain_owner" in role_types:
            score += 30
        if "veto_player" in role_types:
            score += 20
        score += min(20, len(matches) * 10)
        score = min(100, score)
        if score == 0:
            continue
        target = {
            "target_id": stable_id("TARGET", manifest["study_id"], relation["person_id"], offer_id),
            "person_id": relation["person_id"],
            "relationship_id": relation["relationship_id"],
            "role_hypotheses": sorted(role for role in role_types if role),
            "persona_matches": matches,
            "target_score": score,
            "confidence": "low" if relation.get("current_status") != "current" or not relation.get("observed_at") else "medium",
            "current_role_status": relation.get("current_status", "unverified"),
            "required_validations": [
                "Confirm that the person still holds the stated role.",
                "Validate influence, mandate, and relevance to the matched problem.",
            ],
        }
        targets.append(target)
    targets.sort(key=lambda item: (-item["target_score"], item["person_id"]))
    output = {
        "schema_version": "0.3",
        "generated_at": utc_now(),
        "study_id": manifest["study_id"],
        "company_id": company_id,
        "offer_id": offer_id,
        "fit_decision": fit_decision,
        "fit_score": match.get("score"),
        "product_profile_version": match.get("product_profile_version"),
        "targets": targets[: args.limit],
        "privacy": "Contains private person identifiers; do not publish.",
    }
    dump_yaml(study / "06b_contact_targets.yaml", output)
    print(f"targets={len(output['targets'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
