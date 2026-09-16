from __future__ import annotations

import unittest

from jsonschema import Draft202012Validator

from app.network_identity_v1 import (
    company_v0_3_to_v1,
    load_v1_schema,
    person_v0_3_to_v1,
    relationship_v0_3_to_v1,
)


class V1SchemaValidityTests(unittest.TestCase):
    """Schema tests: each v1 contract must itself be a valid JSON Schema."""

    def test_person_v1_schema_is_valid_json_schema(self) -> None:
        Draft202012Validator.check_schema(load_v1_schema("person"))

    def test_company_v1_schema_is_valid_json_schema(self) -> None:
        Draft202012Validator.check_schema(load_v1_schema("company"))

    def test_relationship_v1_schema_is_valid_json_schema(self) -> None:
        Draft202012Validator.check_schema(load_v1_schema("relationship"))


class PersonV0_3ToV1Tests(unittest.TestCase):
    """N-1 reader tests: a legacy v0.3 record maps losslessly into v1 shape."""

    LEGACY_PERSON = {
        "person_id": "PERS-ABCDEF123456",
        "display_name": "Jane Doe",
        "normalized_name": "jane doe",
        "seed_company_id": "COMP-000000000000",
        "identity_key_basis": "normalized_name_and_company",
        "relationship_ids": ["REL-1"],
        "role_hypotheses": [],
        "identity_confidence": "medium",
        "requires_identity_validation": True,
        "source_batch_ids": ["batch-2026-01"],
        "status": "active",
        "last_updated": "2026-09-01",
        "stale_after_months": 6,
    }

    def test_adapted_record_is_valid_against_v1_schema(self) -> None:
        v1 = person_v0_3_to_v1(
            self.LEGACY_PERSON,
            entity_id="entity_abc123",
            workspace_id="default",
            valid_from="2026-09-01",
        )
        Draft202012Validator(load_v1_schema("person")).validate(v1)

    def test_no_data_lost_from_legacy_record(self) -> None:
        v1 = person_v0_3_to_v1(
            self.LEGACY_PERSON,
            entity_id="entity_abc123",
            workspace_id="default",
            valid_from="2026-09-01",
        )
        self.assertEqual([self.LEGACY_PERSON["person_id"]], v1["legacy_ids"])
        self.assertEqual(self.LEGACY_PERSON["display_name"], v1["display_name"])
        self.assertEqual(self.LEGACY_PERSON["status"], v1["status"])
        self.assertEqual(self.LEGACY_PERSON["source_batch_ids"], v1["provenance"]["source_refs"])
        self.assertEqual(self.LEGACY_PERSON["last_updated"], v1["last_updated"])
        self.assertEqual(self.LEGACY_PERSON["stale_after_months"], v1["stale_after_months"])

    def test_entity_id_is_caller_supplied_not_recomputed(self) -> None:
        v1_first = person_v0_3_to_v1(self.LEGACY_PERSON, entity_id="entity_x", workspace_id="default", valid_from="2026-09-01")
        moved = dict(self.LEGACY_PERSON, seed_company_id="COMP-DIFFERENT000")
        v1_second = person_v0_3_to_v1(moved, entity_id="entity_x", workspace_id="default", valid_from="2026-09-02")
        # Same entity_id even though the identity-key basis (company) changed --
        # this is the exact gap ADR-009 fixes relative to legacy stable_id().
        self.assertEqual(v1_first["entity_id"], v1_second["entity_id"])


class CompanyV0_3ToV1Tests(unittest.TestCase):
    LEGACY_COMPANY = {
        "company_id": "COMP-000000000000",
        "canonical_name": "Acme Corp",
        "normalized_name": "acme corp",
        "aliases": ["Acme"],
        "countries": ["FR"],
        "relationship_ids": ["REL-1"],
        "linked_person_ids": ["PERS-ABCDEF123456"],
        "contact_count": 1,
        "source_batch_ids": ["batch-2026-01"],
        "workspace_id": None,
        "status": "active",
        "last_updated": "2026-09-01",
        "stale_after_months": 6,
    }

    def test_adapted_record_is_valid_against_v1_schema(self) -> None:
        v1 = company_v0_3_to_v1(
            self.LEGACY_COMPANY,
            entity_id="entity_company_1",
            workspace_id="default",
            valid_from="2026-09-01",
        )
        Draft202012Validator(load_v1_schema("company")).validate(v1)

    def test_null_legacy_workspace_id_coalesces_to_default(self) -> None:
        v1 = company_v0_3_to_v1(
            self.LEGACY_COMPANY,
            entity_id="entity_company_1",
            workspace_id="",
            valid_from="2026-09-01",
        )
        self.assertEqual("default", v1["workspace_id"])


class RelationshipV0_3ToV1Tests(unittest.TestCase):
    LEGACY_RELATIONSHIP = {
        "relationship_id": "REL-1",
        "person_id": "PERS-ABCDEF123456",
        "company_id": "COMP-000000000000",
        "job_title": "VP Engineering",
        "country": "FR",
        "relationship_type": "employment",
        "current_status": "current",
        "role_hypotheses": [],
        "source_refs": ["evidence-1"],
        "observed_at": "2026-08-01",
        "epistemic_status": "fact",
        "evidence_grade": "P1",
        "requires_validation": False,
    }

    def test_adapted_record_is_valid_against_v1_schema(self) -> None:
        v1 = relationship_v0_3_to_v1(
            self.LEGACY_RELATIONSHIP,
            person_entity_id="entity_abc123",
            company_entity_id="entity_company_1",
            valid_from="2026-09-01",
        )
        Draft202012Validator(load_v1_schema("relationship")).validate(v1)

    def test_observed_at_becomes_valid_from_when_present(self) -> None:
        v1 = relationship_v0_3_to_v1(
            self.LEGACY_RELATIONSHIP,
            person_entity_id="entity_abc123",
            company_entity_id="entity_company_1",
            valid_from="2026-09-01",
        )
        self.assertEqual("2026-08-01", v1["valid_from"])

    def test_missing_observed_at_falls_back_to_supplied_valid_from(self) -> None:
        record = dict(self.LEGACY_RELATIONSHIP, observed_at=None)
        v1 = relationship_v0_3_to_v1(
            record,
            person_entity_id="entity_abc123",
            company_entity_id="entity_company_1",
            valid_from="2026-09-01",
        )
        self.assertEqual("2026-09-01", v1["valid_from"])


if __name__ == "__main__":
    unittest.main()
