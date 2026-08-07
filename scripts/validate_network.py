#!/usr/bin/env python3
"""Validate the private network data layer and cross-object references."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from network_common import ROOT, file_sha256, load_yaml, normalize, parse_iso_date, read_jsonl, stable_id


SCHEMA_VERSION = "0.3"
PERSON_STATUSES = {"seeded", "active", "refresh_due"}
CONFIDENCE_LEVELS = {"low", "medium", "high"}
RELATIONSHIP_STATUSES = {"unverified", "current", "former", "invalidated"}
EPISTEMIC_STATUSES = {"fact", "inference", "hypothesis", "unknown"}
EVIDENCE_GRADES = {"P1", "P2", "U1", "W1", "N0"}
MAPPING_STATUSES = {"candidate", "validated", "pending", "conflict", "out_of_scope"}
SCOPE_STATUSES = {"in_scope", "out_of_scope", "unknown"}
SCREENING_COMPONENT_MAXIMA = {
    "network_access": 20,
    "executive_access": 25,
    "ai_data_proximity": 20,
    "delivery_transformation_proximity": 15,
    "buying_committee_coverage": 15,
    "classification_readiness": 5,
}


def is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def require_fields(label: str, item: dict, fields: set[str], errors: list[str]) -> None:
    missing = fields - set(item)
    if missing:
        errors.append(f"{label} missing fields: {sorted(missing)}")


def valid_iso_date(value: object, *, nullable: bool = False) -> bool:
    if value in (None, ""):
        return nullable
    return parse_iso_date(value) is not None and len(str(value)) == 10


def duplicates(values: list[str]) -> set[str]:
    seen: set[str] = set()
    repeated: set[str] = set()
    for value in values:
        if value in seen:
            repeated.add(value)
        seen.add(value)
    return repeated


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, default=ROOT / "data" / "private")
    args = parser.parse_args()
    data_root = args.data_root.resolve()
    network = data_root / "network"
    errors: list[str] = []
    warnings: list[str] = []
    try:
        people = read_jsonl(network / "people.jsonl")
        companies = read_jsonl(network / "companies.jsonl")
        relationships = read_jsonl(network / "relationships.jsonl")
        mappings = read_jsonl(network / "company_icb_mappings.jsonl")
        screenings = read_jsonl(network / "account_screening.jsonl")
    except Exception as exc:
        print("ERROR:", exc)
        return 1
    if not people or not companies or not relationships:
        errors.append("People, companies, and relationships must not be empty")
    for label, records, key in (
        ("people", people, "person_id"),
        ("companies", companies, "company_id"),
        ("relationships", relationships, "relationship_id"),
        ("mappings", mappings, "mapping_id"),
        ("screenings", screenings, "screening_id"),
    ):
        repeated = duplicates([str(item.get(key, "")) for item in records])
        if repeated:
            errors.append(f"Duplicate {label} IDs: {sorted(repeated)[:5]}")
    person_ids = {item["person_id"] for item in people}
    company_ids = {item["company_id"] for item in companies}
    relationship_ids = {item["relationship_id"] for item in relationships}
    company_by_id = {item["company_id"]: item for item in companies}
    person_by_id = {item["person_id"]: item for item in people}

    for person in people:
        label = f"Person {person.get('person_id', '<missing>')}"
        require_fields(
            label,
            person,
            {
                "schema_version", "person_id", "display_name", "normalized_name", "seed_company_id",
                "identity_key_basis", "relationship_ids", "role_hypotheses", "identity_confidence",
                "requires_identity_validation", "source_batch_ids", "status", "last_updated", "stale_after_months",
            },
            errors,
        )
        if person.get("schema_version") != SCHEMA_VERSION:
            errors.append(f"{label} has invalid schema_version")
        if not all(isinstance(person.get(field), str) and person.get(field) for field in ("person_id", "display_name", "normalized_name", "seed_company_id")):
            errors.append(f"{label} has invalid identity strings")
        elif person.get("normalized_name") != normalize(person["display_name"]):
            errors.append(f"{label} normalized_name mismatch")
        if person.get("identity_key_basis") != "normalized_name_and_company":
            errors.append(f"{label} has unsupported identity_key_basis")
        if person.get("identity_confidence") not in CONFIDENCE_LEVELS:
            errors.append(f"{label} has invalid identity_confidence")
        if person.get("status") not in PERSON_STATUSES:
            errors.append(f"{label} has invalid status")
        if not isinstance(person.get("requires_identity_validation"), bool):
            errors.append(f"{label} requires_identity_validation must be boolean")
        for field in ("relationship_ids", "role_hypotheses", "source_batch_ids"):
            if not isinstance(person.get(field), list):
                errors.append(f"{label} {field} must be a list")
        if not valid_iso_date(person.get("last_updated")):
            errors.append(f"{label} has invalid last_updated date")
        if not isinstance(person.get("stale_after_months"), int) or isinstance(person.get("stale_after_months"), bool) or person.get("stale_after_months", 0) < 1:
            errors.append(f"{label} stale_after_months must be a positive integer")

    for company in companies:
        label = f"Company {company.get('company_id', '<missing>')}"
        require_fields(
            label,
            company,
            {
                "schema_version", "company_id", "canonical_name", "normalized_name", "aliases", "countries",
                "relationship_ids", "linked_person_ids", "contact_count", "icb_mapping", "network_screening",
                "study", "source_batch_ids", "status", "last_updated", "stale_after_months",
            },
            errors,
        )
        if company.get("schema_version") != SCHEMA_VERSION:
            errors.append(f"{label} has invalid schema_version")
        if not isinstance(company.get("canonical_name"), str) or not company.get("canonical_name"):
            errors.append(f"{label} canonical_name must be a non-empty string")
        elif company.get("normalized_name") != normalize(company["canonical_name"]):
            errors.append(f"{label} normalized_name mismatch")
        for field in ("aliases", "countries", "relationship_ids", "linked_person_ids", "source_batch_ids"):
            if not isinstance(company.get(field), list):
                errors.append(f"{label} {field} must be a list")
        if not isinstance(company.get("contact_count"), int) or isinstance(company.get("contact_count"), bool) or company.get("contact_count", -1) < 0:
            errors.append(f"{label} contact_count must be a non-negative integer")
        if company.get("status") not in PERSON_STATUSES:
            errors.append(f"{label} has invalid status")
        if not valid_iso_date(company.get("last_updated")):
            errors.append(f"{label} has invalid last_updated date")
        if not isinstance(company.get("stale_after_months"), int) or isinstance(company.get("stale_after_months"), bool) or company.get("stale_after_months", 0) < 1:
            errors.append(f"{label} stale_after_months must be a positive integer")

    for relation in relationships:
        label = f"Relationship {relation.get('relationship_id', '<missing>')}"
        require_fields(
            label,
            relation,
            {
                "schema_version", "relationship_id", "person_id", "company_id", "job_title", "country",
                "relationship_type", "current_status", "role_hypotheses", "source_refs", "observed_at",
                "epistemic_status", "evidence_grade", "requires_validation",
            },
            errors,
        )
        if relation.get("schema_version") != SCHEMA_VERSION:
            errors.append(f"{label} has invalid schema_version")
        if relation.get("person_id") not in person_ids:
            errors.append(f"Relationship has unknown person: {relation.get('relationship_id')}")
        if relation.get("company_id") not in company_ids:
            errors.append(f"Relationship has unknown company: {relation.get('relationship_id')}")
        if relation.get("relationship_type") != "employment":
            errors.append(f"{label} has invalid relationship_type")
        if relation.get("current_status") not in RELATIONSHIP_STATUSES:
            errors.append(f"{label} has invalid current_status")
        if relation.get("epistemic_status") not in EPISTEMIC_STATUSES:
            errors.append(f"{label} has invalid epistemic_status")
        if relation.get("evidence_grade") not in EVIDENCE_GRADES:
            errors.append(f"{label} has invalid evidence_grade")
        if not isinstance(relation.get("requires_validation"), bool):
            errors.append(f"{label} requires_validation must be boolean")
        if not isinstance(relation.get("source_refs"), list) or not relation.get("source_refs"):
            errors.append(f"{label} requires at least one source_ref")
        if not isinstance(relation.get("role_hypotheses"), list):
            errors.append(f"{label} role_hypotheses must be a list")
        if not valid_iso_date(relation.get("observed_at"), nullable=True):
            errors.append(f"{label} has invalid observed_at date")
        if relation.get("current_status") == "unverified" and not relation.get("requires_validation"):
            errors.append(f"Unverified relationship lacks validation flag: {relation.get('relationship_id')}")
        if relation.get("current_status") in {"current", "former", "invalidated"} and not valid_iso_date(relation.get("observed_at")):
            errors.append(f"{label} has a validated status without a dated observation")
        person = person_by_id.get(relation.get("person_id"))
        company = company_by_id.get(relation.get("company_id"))
        if person and company:
            expected_person_id = stable_id("PERS", person.get("display_name", ""), company.get("canonical_name", ""))
            if relation.get("person_id") != expected_person_id:
                errors.append(f"{label} person ID does not match normalized name-and-company seed")
            if person.get("seed_company_id") != relation.get("company_id"):
                errors.append(f"{label} conflicts with person's seed_company_id")
            expected_relationship_id = stable_id(
                "REL", str(relation.get("person_id", "")), str(relation.get("company_id", "")), str(relation.get("job_title", ""))
            )
            if relation.get("relationship_id") != expected_relationship_id:
                errors.append(f"{label} is not the deterministic relationship ID")
    for company in companies:
        unknown = set(company.get("relationship_ids", [])) - relationship_ids
        if unknown:
            errors.append(f"Company {company['company_id']} has unknown relationships")
        if company.get("contact_count") != len(set(company.get("linked_person_ids", []))):
            errors.append(f"Company contact count mismatch: {company['company_id']}")
        if set(company.get("linked_person_ids", [])) - person_ids:
            errors.append(f"Company {company['company_id']} has unknown linked people")
    for person in people:
        unknown = set(person.get("relationship_ids", [])) - relationship_ids
        if unknown:
            errors.append(f"Person {person['person_id']} has unknown relationships")
    if len(mappings) != len(companies):
        errors.append("Every company must have one ICB mapping record, including pending or out-of-scope")
    if len(screenings) != len(companies):
        errors.append("Every company must have one network screening record")

    taxonomy = load_yaml(ROOT / "data" / "taxonomies" / "icb_v5_2026.yaml")
    sectors_by_code = {
        str(sector["code"]): {
            "industry": {"code": str(industry["code"]), "name": industry["name"]},
            "supersector": {"code": str(supersector["code"]), "name": supersector["name"]},
            "sector": {"code": str(sector["code"]), "name": sector["name"]},
        }
        for industry in taxonomy.get("industries", [])
        for supersector in industry.get("supersectors", [])
        for sector in supersector.get("sectors", [])
    }
    mapping_by_company: dict[str, dict] = {}
    for mapping in mappings:
        label = f"ICB mapping {mapping.get('mapping_id', '<missing>')}"
        require_fields(
            label,
            mapping,
            {
                "schema_version", "mapping_id", "company_id", "taxonomy_version", "scope_status", "mapping_status",
                "assigned_level", "industry", "supersector", "sector", "candidate_sector_codes", "confidence",
                "method", "rationale", "source_ids", "evidence_grade", "requires_validation",
            },
            errors,
        )
        if mapping.get("schema_version") != SCHEMA_VERSION:
            errors.append(f"{label} has invalid schema_version")
        if mapping.get("company_id") not in company_ids:
            errors.append(f"{label} references an unknown company")
        if mapping.get("company_id") in mapping_by_company:
            errors.append(f"Company has more than one ICB mapping: {mapping.get('company_id')}")
        mapping_by_company[mapping.get("company_id")] = mapping
        if mapping.get("scope_status") not in SCOPE_STATUSES:
            errors.append(f"{label} has invalid scope_status")
        if mapping.get("mapping_status") not in MAPPING_STATUSES:
            errors.append(f"{label} has invalid mapping_status")
        if mapping.get("assigned_level") not in {None, "industry", "supersector", "sector", "subsector"}:
            errors.append(f"{label} has invalid assigned_level")
        if mapping.get("confidence") not in CONFIDENCE_LEVELS:
            errors.append(f"{label} has invalid confidence")
        if mapping.get("evidence_grade") not in EVIDENCE_GRADES:
            errors.append(f"{label} has invalid evidence_grade")
        if not isinstance(mapping.get("requires_validation"), bool):
            errors.append(f"{label} requires_validation must be boolean")
        if not isinstance(mapping.get("candidate_sector_codes"), list) or not isinstance(mapping.get("source_ids"), list):
            errors.append(f"{label} candidate_sector_codes and source_ids must be lists")
        sector = mapping.get("sector") or {}
        if sector.get("code") and str(sector["code"]) not in sectors_by_code:
            errors.append(f"Unknown ICB sector code: {sector['code']}")
        elif sector.get("code"):
            expected = sectors_by_code[str(sector["code"])]
            for level in ("industry", "supersector", "sector"):
                if mapping.get(level) != expected[level]:
                    errors.append(f"{label} has inconsistent {level} hierarchy")
        if mapping.get("mapping_status") == "candidate" and not mapping.get("requires_validation"):
            errors.append(f"Candidate mapping lacks validation flag: {mapping.get('mapping_id')}")
        if mapping.get("mapping_status") == "validated" and mapping.get("requires_validation"):
            errors.append(f"Validated mapping still requires validation: {mapping.get('mapping_id')}")

    screening_by_company: dict[str, dict] = {}
    for screening in screenings:
        label = f"Screening {screening.get('screening_id', '<missing>')}"
        require_fields(
            label,
            screening,
            {
                "schema_version", "screening_id", "company_id", "model_version", "contact_count",
                "observed_role_families", "components", "score", "tier", "research_priority", "confidence",
                "evidence_grade", "limitations", "generated_at",
            },
            errors,
        )
        if screening.get("schema_version") != SCHEMA_VERSION:
            errors.append(f"{label} has invalid schema_version")
        company_id = screening.get("company_id")
        if company_id not in company_ids:
            errors.append(f"{label} references an unknown company")
        if company_id in screening_by_company:
            errors.append(f"Company has more than one screening: {company_id}")
        screening_by_company[company_id] = screening
        components = screening.get("components")
        if not isinstance(components, dict) or set(components) != set(SCREENING_COMPONENT_MAXIMA):
            errors.append(f"{label} has invalid component keys")
            components = {}
        for field, maximum in SCREENING_COMPONENT_MAXIMA.items():
            value = components.get(field)
            if not is_number(value) or not 0 <= value <= maximum:
                errors.append(f"{label} component {field} must be between 0 and {maximum}")
        score = screening.get("score")
        if not is_number(score) or not 0 <= score <= 100:
            errors.append(f"{label} score must be numeric from 0 to 100")
        elif components and score != sum(components.values()):
            errors.append(f"{label} score does not equal the component sum")
        expected_tier, expected_priority = (
            ("A", "high") if is_number(score) and score >= 65 else
            ("B", "medium") if is_number(score) and score >= 45 else
            ("C", "low") if is_number(score) and score >= 25 else ("D", "hold")
        )
        if screening.get("tier") != expected_tier or screening.get("research_priority") != expected_priority:
            errors.append(f"{label} tier/research_priority does not match score")
        if screening.get("confidence") not in CONFIDENCE_LEVELS:
            errors.append(f"{label} has invalid confidence")
        if screening.get("evidence_grade") != "U1":
            errors.append(f"{label} evidence_grade must be U1")
        if not isinstance(screening.get("limitations"), list) or not screening.get("limitations"):
            errors.append(f"{label} requires limitations")

    for company in companies:
        mapping = mapping_by_company.get(company["company_id"])
        embedded_mapping = company.get("icb_mapping")
        if mapping:
            expected = {key: mapping.get(key) for key in ("mapping_id", "mapping_status", "assigned_level", "industry", "supersector", "sector", "confidence", "requires_validation")}
            if embedded_mapping != expected:
                errors.append(f"Company {company['company_id']} embedded ICB mapping is stale")
        screening = screening_by_company.get(company["company_id"])
        embedded_screening = company.get("network_screening")
        if screening:
            expected = {key: screening.get(key) for key in ("screening_id", "model_version", "score", "tier", "research_priority", "confidence")}
            if embedded_screening != expected:
                errors.append(f"Company {company['company_id']} embedded screening is stale")

    for manifest_path in data_root.glob("intake_batches/*/manifest.yaml"):
        try:
            manifest = load_yaml(manifest_path)
            raw = data_root / manifest["source"]["raw_snapshot_path"]
            if not raw.is_file() or file_sha256(raw) != manifest["source"]["sha256"]:
                errors.append(f"Raw intake checksum mismatch: {manifest.get('batch_id')}")
            if manifest.get("privacy", {}).get("publishable") is not False:
                errors.append(f"Private batch is not marked non-publishable: {manifest.get('batch_id')}")
        except Exception as exc:
            errors.append(f"Invalid batch manifest {manifest_path}: {exc}")
    if not list(data_root.glob("intake_batches/*/manifest.yaml")):
        warnings.append("No intake batch manifest found")

    for message in warnings:
        print("WARN:", message)
    for message in errors:
        print("ERROR:", message)
    print(f"RESULT: {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
