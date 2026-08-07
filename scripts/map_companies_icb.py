#!/usr/bin/env python3
"""Create conservative ICB candidate mappings for canonical company records."""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from network_common import ROOT, dump_yaml, load_yaml, read_jsonl, stable_id, utc_now, write_jsonl


def taxonomy_index(taxonomy: dict[str, Any]) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for industry in taxonomy.get("industries", []):
        for supersector in industry.get("supersectors", []):
            for sector in supersector.get("sectors", []):
                index[str(sector["code"])] = {
                    "industry": {"code": str(industry["code"]), "name": industry["name"]},
                    "supersector": {"code": str(supersector["code"]), "name": supersector["name"]},
                    "sector": {"code": str(sector["code"]), "name": sector["name"]},
                }
    return index


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, default=ROOT / "data" / "private")
    parser.add_argument("--taxonomy", type=Path, default=ROOT / "data" / "taxonomies" / "icb_v5_2026.yaml")
    parser.add_argument("--rules", type=Path, default=ROOT / "data" / "taxonomies" / "company_icb_candidate_rules.yaml")
    args = parser.parse_args()

    data_root = args.data_root.resolve()
    network_dir = data_root / "network"
    companies = read_jsonl(network_dir / "companies.jsonl")
    if not companies:
        parser.error("No companies found; run import_contacts.py first")
    taxonomy = load_yaml(args.taxonomy)
    rules = load_yaml(args.rules)
    sectors = taxonomy_index(taxonomy)
    mappings: list[dict[str, Any]] = []
    counts: Counter[str] = Counter()
    sector_company_counts: Counter[str] = Counter()
    sector_contact_counts: Counter[str] = Counter()

    out_patterns = [re.compile(pattern, flags=re.I) for pattern in rules.get("out_of_scope_patterns", [])]
    sector_rules: list[tuple[dict[str, Any], list[re.Pattern[str]]]] = []
    for rule in rules.get("sector_rules", []):
        code = str(rule.get("sector_code"))
        if code not in sectors:
            raise ValueError(f"Unknown sector code in mapping rules: {code}")
        sector_rules.append((rule, [re.compile(pattern, flags=re.I) for pattern in rule.get("patterns", [])]))

    for company in companies:
        company_id = company["company_id"]
        name = company.get("normalized_name", "")
        mapping: dict[str, Any] = {
            "schema_version": "0.3",
            "mapping_id": stable_id("ICBMAP", company_id),
            "company_id": company_id,
            "taxonomy_version": str(taxonomy["taxonomy"]["version"]),
            "scope_status": "unknown",
            "mapping_status": "pending",
            "assigned_level": None,
            "industry": None,
            "supersector": None,
            "sector": None,
            "candidate_sector_codes": [],
            "confidence": "low",
            "method": "name_pattern_v0.1",
            "rationale": "No defensible candidate from the available company label.",
            "source_ids": ["ICB-P1-2026", rules["rules_version"]],
            "evidence_grade": "N0",
            "requires_validation": True,
        }
        if any(pattern.search(name) for pattern in out_patterns):
            mapping.update(
                {
                    "scope_status": "out_of_scope",
                    "mapping_status": "out_of_scope",
                    "rationale": "The label appears to be a public, academic, judicial, or nonprofit body outside the equity ICB company scope.",
                }
            )
        else:
            matches: list[dict[str, Any]] = []
            for rule, patterns in sector_rules:
                if any(pattern.search(name) for pattern in patterns):
                    matches.append(rule)
            if matches:
                primary = matches[0]
                code = str(primary["sector_code"])
                mapping.update(
                    {
                        "scope_status": "in_scope",
                        "mapping_status": "candidate",
                        "assigned_level": "sector",
                        **sectors[code],
                        "candidate_sector_codes": list(dict.fromkeys(str(item["sector_code"]) for item in matches)),
                        "rationale": primary["rationale"],
                    }
                )
        counts[mapping["mapping_status"]] += 1
        if mapping["mapping_status"] == "candidate" and mapping.get("sector"):
            sector_code = str(mapping["sector"]["code"])
            sector_company_counts[sector_code] += 1
            sector_contact_counts[sector_code] += int(company.get("contact_count", 0))
        company["icb_mapping"] = {
            "mapping_id": mapping["mapping_id"],
            "mapping_status": mapping["mapping_status"],
            "assigned_level": mapping["assigned_level"],
            "industry": mapping["industry"],
            "supersector": mapping["supersector"],
            "sector": mapping["sector"],
            "confidence": mapping["confidence"],
            "requires_validation": mapping["requires_validation"],
        }
        mappings.append(mapping)

    write_jsonl(network_dir / "company_icb_mappings.jsonl", mappings, "mapping_id")
    write_jsonl(network_dir / "companies.jsonl", companies, "company_id")
    dump_yaml(
        network_dir / "icb_mapping_summary.yaml",
        {
            "schema_version": "0.3",
            "generated_at": utc_now(),
            "taxonomy_version": taxonomy["taxonomy"]["version"],
            "rules_version": rules["rules_version"],
            "total_companies": len(companies),
            "status_counts": dict(sorted(counts.items())),
            "candidate_sectors": [
                {
                    "sector_code": code,
                    "sector_name": sectors[code]["sector"]["name"],
                    "company_count": sector_company_counts[code],
                    "contact_count": sector_contact_counts[code],
                }
                for code in sorted(
                    sector_company_counts,
                    key=lambda item: (-sector_company_counts[item], sectors[item]["sector"]["name"]),
                )
            ],
            "policy": rules["policy"],
        },
    )
    print(dict(sorted(counts.items())))
    return 0


if __name__ == "__main__":
    sys.exit(main())
