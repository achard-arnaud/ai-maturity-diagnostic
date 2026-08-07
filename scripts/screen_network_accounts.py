#!/usr/bin/env python3
"""Rank network companies for research using contacts only, without inferring product fit."""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

from network_common import ROOT, dump_yaml, read_jsonl, stable_id, title_signals, utc_now, write_jsonl


MODEL_VERSION = "network-screening-2026-07.v0.1"


def access_score(count: int) -> int:
    return {0: 0, 1: 6, 2: 10, 3: 14, 4: 17}.get(count, 20)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, default=ROOT / "data" / "private")
    args = parser.parse_args()
    network_dir = args.data_root.resolve() / "network"
    companies = read_jsonl(network_dir / "companies.jsonl")
    relationships = read_jsonl(network_dir / "relationships.jsonl")
    if not companies or not relationships:
        parser.error("Canonical companies and relationships are required")

    by_company: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for relationship in relationships:
        by_company[relationship["company_id"]].append(relationship)

    screenings: list[dict[str, Any]] = []
    for company in companies:
        relations = by_company.get(company["company_id"], [])
        role_types = {
            role["role"]
            for relation in relations
            for role in relation.get("role_hypotheses", [])
        }
        signals = [title_signals(relation.get("job_title", "")) for relation in relations]
        senior_count = sum(item["senior"] for item in signals)
        ai_data_count = sum(item["ai_data"] for item in signals)
        delivery_count = sum(item["delivery"] for item in signals)
        component_access = access_score(len(relations))
        component_executive = min(25, senior_count * 10)
        component_ai_data = min(20, ai_data_count * 7)
        component_delivery = min(15, delivery_count * 5)
        relevant_roles = role_types.intersection(
            {"economic_sponsor", "technical_sponsor", "terrain_owner", "veto_player", "transformation_owner"}
        )
        component_committee = min(15, len(relevant_roles) * 4)
        mapping = company.get("icb_mapping") or {}
        component_icb = 5 if mapping.get("mapping_status") in {"candidate", "validated"} else 0
        components = {
            "network_access": component_access,
            "executive_access": component_executive,
            "ai_data_proximity": component_ai_data,
            "delivery_transformation_proximity": component_delivery,
            "buying_committee_coverage": component_committee,
            "classification_readiness": component_icb,
        }
        score = sum(components.values())
        if score >= 65:
            tier, priority = "A", "high"
        elif score >= 45:
            tier, priority = "B", "medium"
        elif score >= 25:
            tier, priority = "C", "low"
        else:
            tier, priority = "D", "hold"
        confidence = "medium" if len(relations) >= 3 and len(relevant_roles) >= 3 else "low"
        screening = {
            "schema_version": "0.3",
            "screening_id": stable_id("SCREEN", company["company_id"], MODEL_VERSION),
            "company_id": company["company_id"],
            "model_version": MODEL_VERSION,
            "contact_count": len(relations),
            "observed_role_families": sorted(role_types),
            "components": components,
            "score": score,
            "tier": tier,
            "research_priority": priority,
            "confidence": confidence,
            "evidence_grade": "U1",
            "limitations": [
                "This score measures research access and relevance signals, not demonstrated demand.",
                "Every role is imported from an undated private file and remains unverified.",
                "No product information is used in this screening model.",
            ],
            "generated_at": utc_now(),
        }
        company["network_screening"] = {
            "screening_id": screening["screening_id"],
            "model_version": MODEL_VERSION,
            "score": score,
            "tier": tier,
            "research_priority": priority,
            "confidence": confidence,
        }
        screenings.append(screening)

    screenings.sort(key=lambda item: (-item["score"], item["company_id"]))
    write_jsonl(network_dir / "account_screening.jsonl", screenings, "screening_id")
    write_jsonl(network_dir / "companies.jsonl", companies, "company_id")
    tier_counts: dict[str, int] = defaultdict(int)
    for item in screenings:
        tier_counts[item["tier"]] += 1
    dump_yaml(
        network_dir / "account_screening_summary.yaml",
        {
            "schema_version": "0.3",
            "model_version": MODEL_VERSION,
            "generated_at": utc_now(),
            "total_companies": len(screenings),
            "tier_counts": dict(sorted(tier_counts.items())),
            "top_research_queue": [
                {"company_id": item["company_id"], "score": item["score"], "tier": item["tier"]}
                for item in screenings[:50]
            ],
            "warning": "Ranking is a product-agnostic screening prior, not an ICP or product-fit decision.",
        },
    )
    print(dict(sorted(tier_counts.items())))
    return 0


if __name__ == "__main__":
    sys.exit(main())
