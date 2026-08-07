#!/usr/bin/env python3
"""Build a company research queue and optionally initialize or refresh studies."""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from network_common import ROOT, dump_yaml, load_yaml, normalize, parse_iso_date, read_jsonl, utc_now, write_jsonl


def discover_studies(studies_root: Path) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    by_id: dict[str, dict[str, Any]] = {}
    by_name: dict[str, dict[str, Any]] = {}
    if not studies_root.is_dir():
        return by_id, by_name
    for manifest_path in studies_root.glob("*/00_manifest.yaml"):
        try:
            manifest = load_yaml(manifest_path)
        except Exception:
            continue
        record = {"manifest": manifest, "path": str(manifest_path.parent)}
        company_id = manifest.get("company_id")
        key_name = normalize(str(manifest.get("company", "")))
        for index, key in ((by_id, company_id), (by_name, key_name)):
            if not key:
                continue
            existing = index.get(str(key))
            current_date = str(manifest.get("updated_at") or "")
            existing_date = str(existing["manifest"].get("updated_at") or "") if existing else ""
            if existing is None or current_date > existing_date:
                index[str(key)] = record
    return by_id, by_name


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, default=ROOT / "data" / "private")
    parser.add_argument("--studies-root", type=Path, default=ROOT / "studies")
    parser.add_argument("--date", default=date.today().isoformat())
    parser.add_argument("--stale-after-months", type=int, default=6)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--offers", default="all")
    args = parser.parse_args()
    try:
        as_of = date.fromisoformat(args.date)
    except ValueError:
        parser.error("--date must use YYYY-MM-DD")
    if args.limit < 1:
        parser.error("--limit must be positive")

    network_dir = args.data_root.resolve() / "network"
    companies = read_jsonl(network_dir / "companies.jsonl")
    if not companies:
        parser.error("No network companies found")
    studies_root = args.studies_root.resolve()
    by_id, by_name = discover_studies(studies_root)
    entries: list[dict[str, Any]] = []
    stale_delta = timedelta(days=args.stale_after_months * 30)

    for company in companies:
        screening = company.get("network_screening") or {}
        tier = screening.get("tier", "D")
        current = by_id.get(company["company_id"]) or by_name.get(company.get("normalized_name", ""))
        action = "hold"
        reason = "Network screening tier is below the automatic research threshold."
        last_updated = None
        current_path = None
        if current:
            manifest = current["manifest"]
            current_path = current["path"]
            last_updated = manifest.get("updated_at")
            study_date = parse_iso_date(last_updated)
            company_update = parse_iso_date(company.get("last_updated"))
            if company_update and (study_date is None or company_update > study_date):
                action, reason = "refresh", "A newer contact batch affects this company."
            elif study_date is None or as_of - study_date > stale_delta:
                action, reason = "refresh", "The current study is older than the refresh horizon."
            else:
                action, reason = "ready", "A current study exists."
        elif tier in {"A", "B"}:
            action, reason = "create", "Research priority is high or medium and no study exists."
        entries.append(
            {
                "company_id": company["company_id"],
                "company_name": company["canonical_name"],
                "screening_tier": tier,
                "screening_score": screening.get("score", 0),
                "action": action,
                "reason": reason,
                "current_study_path": current_path,
                "last_updated": last_updated,
            }
        )

    action_order = {"refresh": 0, "create": 1, "ready": 2, "hold": 3}
    entries.sort(key=lambda item: (action_order[item["action"]], -item["screening_score"], item["company_name"]))
    queue_path = network_dir / "study_queue.yaml"
    queue = {
        "schema_version": "0.3",
        "generated_at": utc_now(),
        "as_of": as_of.isoformat(),
        "stale_after_months": args.stale_after_months,
        "entries": entries,
    }
    dump_yaml(queue_path, queue)

    applied = 0
    if args.apply:
        for entry in entries:
            if entry["action"] not in {"create", "refresh"} or applied >= args.limit:
                continue
            command = [
                sys.executable,
                str(ROOT / "scripts" / "init_study.py"),
                entry["company_name"],
                "--company-id",
                entry["company_id"],
                "--date",
                as_of.isoformat(),
                "--root",
                str(studies_root),
                "--offers",
                args.offers,
            ]
            target_name = normalize(entry["company_name"]).replace(" ", "-") + "-" + as_of.strftime("%Y%m%d")
            if (studies_root / target_name).exists():
                command.append("--force")
            result = subprocess.run(command, text=True, capture_output=True, check=False)
            if result.returncode != 0:
                print(result.stdout + result.stderr, file=sys.stderr)
                return result.returncode
            entry["applied_study_path"] = result.stdout.splitlines()[0]
            applied += 1
        dump_yaml(queue_path, queue)

    company_index = {item["company_id"]: item for item in companies}
    if applied:
        for entry in entries:
            path = entry.get("applied_study_path")
            if not path:
                continue
            company_index[entry["company_id"]]["study"] = {
                "path": path,
                "status": "seeded",
                "last_updated": as_of.isoformat(),
            }
        write_jsonl(network_dir / "companies.jsonl", company_index.values(), "company_id")

    counts: dict[str, int] = {}
    for entry in entries:
        counts[entry["action"]] = counts.get(entry["action"], 0) + 1
    print({"queue": counts, "applied": applied})
    return 0


if __name__ == "__main__":
    sys.exit(main())
