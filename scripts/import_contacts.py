#!/usr/bin/env python3
"""Import a private TSV contact batch into canonical people, companies, and relationships."""

from __future__ import annotations

import argparse
import csv
import shutil
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any

from network_common import (
    ROOT,
    dump_yaml,
    file_sha256,
    infer_roles,
    normalize,
    read_jsonl,
    stable_id,
    utc_now,
    write_jsonl,
)


REQUIRED_COLUMNS = ["Name", "Job title", "Company", "Country"]


def merge_unique(values: list[Any], additions: list[Any]) -> list[Any]:
    result = list(values)
    for value in additions:
        if value not in result:
            result.append(value)
    return result


def parse_rows(path: Path) -> tuple[list[dict[str, str]], list[dict[str, Any]]]:
    valid: list[dict[str, str]] = []
    rejected: list[dict[str, Any]] = []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames != REQUIRED_COLUMNS:
            raise ValueError(f"Expected columns {REQUIRED_COLUMNS}, found {reader.fieldnames}")
        for source_row, row in enumerate(reader, start=2):
            cleaned = {key: (row.get(key) or "").strip() for key in REQUIRED_COLUMNS}
            missing = [key for key, value in cleaned.items() if not value]
            if missing:
                rejected.append({"source_row": source_row, "missing": missing})
                continue
            cleaned["source_row"] = str(source_row)
            valid.append(cleaned)
    return valid, rejected


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file", type=Path)
    parser.add_argument("--data-root", type=Path, default=ROOT / "data" / "private")
    parser.add_argument("--batch-date", default=date.today().isoformat())
    parser.add_argument("--batch-id")
    parser.add_argument("--source-effective-date", default=None)
    args = parser.parse_args()

    source = args.input_file.resolve()
    if not source.is_file():
        parser.error(f"Input file does not exist: {source}")
    try:
        batch_date = date.fromisoformat(args.batch_date).isoformat()
    except ValueError:
        parser.error("--batch-date must use YYYY-MM-DD")
    if args.source_effective_date:
        try:
            effective_date = date.fromisoformat(args.source_effective_date).isoformat()
        except ValueError:
            parser.error("--source-effective-date must use YYYY-MM-DD")
    else:
        effective_date = None

    digest = file_sha256(source)
    batch_id = args.batch_id or f"CONTACTS-{batch_date.replace('-', '')}-{digest[:8].upper()}"
    data_root = args.data_root.resolve()
    network_dir = data_root / "network"
    batch_dir = data_root / "intake_batches" / batch_id
    manifest_path = batch_dir / "manifest.yaml"
    if manifest_path.is_file():
        existing = manifest_path.read_text(encoding="utf-8")
        if digest in existing:
            print(f"IDEMPOTENT: {batch_id}")
            return 0
        parser.error(f"Batch ID already exists with different content: {batch_id}")

    rows, rejected = parse_rows(source)
    batch_dir.mkdir(parents=True, exist_ok=False)
    raw_snapshot = batch_dir / "raw_contacts.tsv"
    shutil.copy2(source, raw_snapshot)

    people = {item["person_id"]: item for item in read_jsonl(network_dir / "people.jsonl")}
    companies = {item["company_id"]: item for item in read_jsonl(network_dir / "companies.jsonl")}
    relationships = {
        item["relationship_id"]: item for item in read_jsonl(network_dir / "relationships.jsonl")
    }

    for row in rows:
        company_id = stable_id("COMP", row["Company"])
        # The short-term functional identity key is deliberately employer-scoped.
        # A future verified external profile may link several provisional records,
        # but provider URLs never become canonical internal IDs directly.
        person_id = stable_id("PERS", row["Name"], row["Company"])
        relationship_id = stable_id("REL", person_id, company_id, row["Job title"])
        source_ref = f"{batch_id}:row:{row['source_row']}"
        roles = infer_roles(row["Job title"])

        person = people.get(
            person_id,
            {
                "schema_version": "0.3",
                "person_id": person_id,
                "display_name": row["Name"],
                "normalized_name": normalize(row["Name"]),
                "seed_company_id": company_id,
                "identity_key_basis": "normalized_name_and_company",
                "relationship_ids": [],
                "role_hypotheses": [],
                "identity_confidence": "medium",
                "requires_identity_validation": True,
                "source_batch_ids": [],
                "status": "seeded",
                "last_updated": batch_date,
                "stale_after_months": 6,
            },
        )
        person["relationship_ids"] = merge_unique(person.get("relationship_ids", []), [relationship_id])
        person["source_batch_ids"] = merge_unique(person.get("source_batch_ids", []), [batch_id])
        known_roles = {item["role"]: item for item in person.get("role_hypotheses", [])}
        for role in roles:
            known_roles.setdefault(role["role"], role)
        person["role_hypotheses"] = sorted(known_roles.values(), key=lambda item: item["role"])
        person["last_updated"] = batch_date
        people[person_id] = person

        company = companies.get(
            company_id,
            {
                "schema_version": "0.3",
                "company_id": company_id,
                "canonical_name": row["Company"],
                "normalized_name": normalize(row["Company"]),
                "aliases": [],
                "countries": [],
                "relationship_ids": [],
                "linked_person_ids": [],
                "contact_count": 0,
                "icb_mapping": None,
                "network_screening": None,
                "study": None,
                "source_batch_ids": [],
                "status": "seeded",
                "last_updated": batch_date,
                "stale_after_months": 6,
            },
        )
        company["aliases"] = merge_unique(company.get("aliases", []), [row["Company"]])
        company["countries"] = merge_unique(company.get("countries", []), [row["Country"]])
        company["relationship_ids"] = merge_unique(company.get("relationship_ids", []), [relationship_id])
        company["linked_person_ids"] = merge_unique(company.get("linked_person_ids", []), [person_id])
        company["source_batch_ids"] = merge_unique(company.get("source_batch_ids", []), [batch_id])
        company["last_updated"] = batch_date
        companies[company_id] = company

        relationship = relationships.get(
            relationship_id,
            {
                "schema_version": "0.3",
                "relationship_id": relationship_id,
                "person_id": person_id,
                "company_id": company_id,
                "job_title": row["Job title"],
                "country": row["Country"],
                "relationship_type": "employment",
                "current_status": "unverified",
                "role_hypotheses": roles,
                "source_refs": [],
                "observed_at": effective_date,
                "epistemic_status": "fact",
                "evidence_grade": "U1",
                "requires_validation": True,
            },
        )
        relationship["source_refs"] = merge_unique(relationship.get("source_refs", []), [source_ref])
        relationships[relationship_id] = relationship

    for company in companies.values():
        company["relationship_ids"] = sorted(set(company.get("relationship_ids", [])))
        company["linked_person_ids"] = sorted(set(company.get("linked_person_ids", [])))
        company["contact_count"] = len(company["linked_person_ids"])

    write_jsonl(network_dir / "people.jsonl", people.values(), "person_id")
    write_jsonl(network_dir / "companies.jsonl", companies.values(), "company_id")
    write_jsonl(network_dir / "relationships.jsonl", relationships.values(), "relationship_id")

    manifest = {
        "schema_version": "0.3",
        "batch_id": batch_id,
        "source": {
            "original_path": str(source),
            "raw_snapshot_path": str(raw_snapshot.relative_to(data_root)),
            "sha256": digest,
            "effective_date": effective_date,
        },
        "imported_at": utc_now(),
        "privacy": {
            "classification": "confidential_contact_data",
            "publishable": False,
            "handling": "Keep private; do not copy names into public deliverables.",
        },
        "input_schema": REQUIRED_COLUMNS,
        "counts": {
            "rows": len(rows) + len(rejected),
            "people": len({stable_id("PERS", row["Name"], row["Company"]) for row in rows}),
            "companies": len({stable_id("COMP", row["Company"]) for row in rows}),
            "relationships": len(
                {
                    stable_id(
                        "REL",
                        stable_id("PERS", row["Name"]),
                        stable_id("COMP", row["Company"]),
                        row["Job title"],
                    )
                    for row in rows
                }
            ),
            "rejected_rows": len(rejected),
        },
        "outputs": {
            "people": "network/people.jsonl",
            "companies": "network/companies.jsonl",
            "relationships": "network/relationships.jsonl",
        },
        "limitations": [
            "The file contains no observation date for job titles.",
            "Country is preserved as supplied and is not assumed to be company headquarters.",
            "Person IDs are provisional and scoped to normalized name plus supplied company.",
            "A verified external identity may later link employer-scoped records without replacing internal IDs.",
        ],
        "rejected_rows": rejected,
    }
    dump_yaml(manifest_path, manifest)
    dump_yaml(
        network_dir / "contact_intake_summary.yaml",
        {
            "schema_version": "0.3",
            "latest_batch_id": batch_id,
            "generated_at": utc_now(),
            "total_people": len(people),
            "total_companies": len(companies),
            "total_relationships": len(relationships),
            "latest_batch_counts": manifest["counts"],
            "privacy": "confidential_contact_data",
        },
    )
    print(batch_id)
    print(f"people={len(people)} companies={len(companies)} relationships={len(relationships)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
