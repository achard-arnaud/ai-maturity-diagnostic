#!/usr/bin/env python3
"""Migrate legacy name-only person IDs to provisional name-and-company IDs."""

from __future__ import annotations

import argparse
import shutil
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

from network_common import ROOT, normalize, read_jsonl, stable_id, utc_now, write_jsonl


def merge_unique(values: list[Any], additions: list[Any]) -> list[Any]:
    result = list(values)
    for value in additions:
        if value not in result:
            result.append(value)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, default=ROOT / "data" / "private")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    data_root = args.data_root.resolve()
    network = data_root / "network"
    people = {item["person_id"]: item for item in read_jsonl(network / "people.jsonl")}
    companies = {item["company_id"]: item for item in read_jsonl(network / "companies.jsonl")}
    relationships = read_jsonl(network / "relationships.jsonl")
    if not people or not companies or not relationships:
        parser.error("Canonical people, companies, and relationships are required")

    migrated_people: dict[str, dict[str, Any]] = {}
    migrated_relationships: list[dict[str, Any]] = []
    relationship_ids_by_company: dict[str, list[str]] = defaultdict(list)
    person_ids_by_company: dict[str, list[str]] = defaultdict(list)
    changed_people: set[str] = set()

    for relationship in relationships:
        old_person_id = relationship["person_id"]
        company_id = relationship["company_id"]
        old_person = people.get(old_person_id)
        company = companies.get(company_id)
        if not old_person or not company:
            parser.error(f"Broken relationship reference: {relationship.get('relationship_id')}")
        display_name = str(old_person["display_name"])
        new_person_id = stable_id("PERS", display_name, str(company["canonical_name"]))
        new_relationship_id = stable_id("REL", new_person_id, company_id, str(relationship["job_title"]))
        if new_person_id != old_person_id:
            changed_people.add(old_person_id)

        person = migrated_people.get(new_person_id)
        if person is None:
            person = dict(old_person)
            person.update(
                {
                    "person_id": new_person_id,
                    "normalized_name": normalize(display_name),
                    "seed_company_id": company_id,
                    "identity_key_basis": "normalized_name_and_company",
                    "relationship_ids": [],
                }
            )
        else:
            person["source_batch_ids"] = merge_unique(
                person.get("source_batch_ids", []), old_person.get("source_batch_ids", [])
            )
            roles = {item.get("role"): item for item in person.get("role_hypotheses", []) if isinstance(item, dict)}
            for role in old_person.get("role_hypotheses", []):
                if isinstance(role, dict) and role.get("role") not in roles:
                    roles[role.get("role")] = role
            person["role_hypotheses"] = sorted(roles.values(), key=lambda item: str(item.get("role")))
        person["relationship_ids"] = merge_unique(person.get("relationship_ids", []), [new_relationship_id])
        migrated_people[new_person_id] = person

        migrated = dict(relationship)
        migrated["person_id"] = new_person_id
        migrated["relationship_id"] = new_relationship_id
        migrated_relationships.append(migrated)
        relationship_ids_by_company[company_id].append(new_relationship_id)
        person_ids_by_company[company_id].append(new_person_id)

    for company_id, company in companies.items():
        company["relationship_ids"] = sorted(set(relationship_ids_by_company.get(company_id, [])))
        company["linked_person_ids"] = sorted(set(person_ids_by_company.get(company_id, [])))
        company["contact_count"] = len(company["linked_person_ids"])

    print(
        f"legacy_people={len(people)} migrated_people={len(migrated_people)} "
        f"relationships={len(migrated_relationships)} changed_legacy_ids={len(changed_people)}"
    )
    if not args.apply:
        print("DRY-RUN: pass --apply to write the migration")
        return 0

    stamp = utc_now().replace(":", "").replace("+00:00", "Z")
    backup = data_root / "migrations" / f"person-identity-v0.3-{stamp}"
    backup.mkdir(parents=True, exist_ok=False)
    for name in ("people.jsonl", "companies.jsonl", "relationships.jsonl"):
        shutil.copy2(network / name, backup / name)
    write_jsonl(network / "people.jsonl", migrated_people.values(), "person_id")
    write_jsonl(network / "companies.jsonl", companies.values(), "company_id")
    write_jsonl(network / "relationships.jsonl", migrated_relationships, "relationship_id")
    print(f"APPLIED: backup={backup}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
