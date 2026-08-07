#!/usr/bin/env python3
"""Determine sector-rollup eligibility and scaffold evidence-preserving ICB sector summaries."""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from network_common import ROOT, dump_yaml, load_yaml, parse_iso_date, read_jsonl, utc_now


def claim_records(items: list[Any], company_id: str, study_id: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for item in items:
        if isinstance(item, dict):
            records.append(
                {
                    "company_id": company_id,
                    "study_id": study_id,
                    "claim_id": item.get("claim_id") or item.get("id"),
                    "statement": item.get("statement") or item.get("priority") or item.get("gap"),
                    "epistemic_status": item.get("epistemic_status", "unknown"),
                    "confidence": item.get("confidence", "low"),
                }
            )
    return records


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, default=ROOT / "data" / "private")
    parser.add_argument("--studies-root", type=Path, default=ROOT / "studies")
    parser.add_argument("--threshold", type=int, default=3)
    parser.add_argument("--stale-after-months", type=int, default=6)
    parser.add_argument("--date", default=date.today().isoformat())
    args = parser.parse_args()
    as_of = date.fromisoformat(args.date)
    if args.threshold < 3:
        parser.error("--threshold must be at least 3")
    network_dir = args.data_root.resolve() / "network"
    rollup_dir = args.data_root.resolve() / "sector_rollups"
    mappings = {item["company_id"]: item for item in read_jsonl(network_dir / "company_icb_mappings.jsonl")}
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)

    studies_root = args.studies_root.resolve()
    if studies_root.is_dir():
        for manifest_path in studies_root.glob("*/00_manifest.yaml"):
            study_dir = manifest_path.parent
            try:
                manifest = load_yaml(manifest_path)
                profile = load_yaml(study_dir / "05_enterprise_demand_profile.yaml")
            except Exception:
                continue
            company_id = manifest.get("company_id")
            mapping = mappings.get(company_id)
            if not mapping or mapping.get("mapping_status") not in {"candidate", "validated"}:
                continue
            sector = mapping.get("sector") or {}
            if not sector.get("code"):
                continue
            study_date = parse_iso_date(manifest.get("updated_at"))
            current = (
                study_date is not None
                and study_date <= as_of
                and as_of - study_date <= timedelta(days=args.stale_after_months * 30)
            )
            complete = bool(profile.get("evidence_claims") and profile.get("capability_gaps")) and profile.get("confidence") in {"medium", "high"}
            groups[str(sector["code"])].append(
                {
                    "company_id": company_id,
                    "study_id": manifest.get("study_id"),
                    "study_path": str(study_dir),
                    "updated_at": manifest.get("updated_at"),
                    "current": current,
                    "complete": complete,
                    "sector": sector,
                    "icb_mapping_id": mapping.get("mapping_id"),
                    "icb_mapping_status": mapping.get("mapping_status"),
                    "icb_confidence": mapping.get("confidence"),
                    "profile": profile,
                }
            )

    status_entries: list[dict[str, Any]] = []
    generated = 0
    for sector_code, records in sorted(groups.items()):
        eligible = [item for item in records if item["current"] and item["complete"]]
        sector_name = records[0]["sector"]["name"]
        mapping_statuses = {item["icb_mapping_status"] for item in eligible}
        classification_basis = (
            "validated" if mapping_statuses == {"validated"} else
            "candidate" if mapping_statuses == {"candidate"} else "mixed"
        )
        publication_status = "decision_grade" if classification_basis == "validated" else "exploratory"
        status_entries.append(
            {
                "sector_code": sector_code,
                "sector_name": sector_name,
                "observed_studies": len(records),
                "eligible_current_studies": len(eligible),
                "threshold": args.threshold,
                "status": "eligible" if len(eligible) >= args.threshold else "insufficient",
                "classification_basis": classification_basis,
                "publication_status": publication_status,
            }
        )
        if len(eligible) < args.threshold:
            continue
        priority_pool: list[dict[str, Any]] = []
        gap_pool: list[dict[str, Any]] = []
        for item in eligible:
            priority_pool.extend(claim_records(item["profile"].get("strategic_priorities", []), item["company_id"], item["study_id"]))
            gap_pool.extend(claim_records(item["profile"].get("capability_gaps", []), item["company_id"], item["study_id"]))
        rollup = {
            "schema_version": "0.3",
            "sector_code": sector_code,
            "sector_name": sector_name,
            "taxonomy_version": "5.0",
            "generated_at": utc_now(),
            "threshold": args.threshold,
            "classification_basis": classification_basis,
            "publication_status": publication_status,
            "covered_accounts": [
                {
                    "company_id": item["company_id"],
                    "study_id": item["study_id"],
                    "updated_at": item["updated_at"],
                    "icb_mapping_id": item["icb_mapping_id"],
                    "icb_mapping_status": item["icb_mapping_status"],
                    "icb_confidence": item["icb_confidence"],
                }
                for item in eligible
            ],
            "evidence_pool": {"strategic_priorities": priority_pool, "capability_gaps": gap_pool},
            "synthesis": {
                "recurring_priorities": [],
                "recurring_capability_gaps": [],
                "maturity_patterns": [],
                "training_and_upskilling_themes": [],
                "use_cases_by_line_of_business": [],
                "contradictions": [],
                "unknowns": [],
            },
            "confidence": "low" if publication_status == "exploratory" else "medium",
            "limitations": [
                "Candidate or mixed ICB mappings limit this rollup to exploratory use."
            ] if publication_status == "exploratory" else [],
            "next_skill": "sector-intelligence-consolidation",
        }
        dump_yaml(rollup_dir / f"ICB-{sector_code}.yaml", rollup)
        generated += 1
    dump_yaml(
        rollup_dir / "status.yaml",
        {
            "schema_version": "0.3",
            "generated_at": utc_now(),
            "as_of": as_of.isoformat(),
            "threshold": args.threshold,
            "sectors": status_entries,
            "generated_rollups": generated,
        },
    )
    print(f"eligible_rollups={generated}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
