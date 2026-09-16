from __future__ import annotations

import tempfile
import unittest
from datetime import date
from pathlib import Path

from app.network_v1_store import put_entity
from app.person_view import get_person_360


def _person(entity_id: str) -> dict:
    return {
        "entity_id": entity_id,
        "legacy_ids": [f"PERS-{entity_id}"],
        "display_name": "Jane Doe",
        "workspace_id": "ws-a",
        "valid_from": "2026-01-01",
        "valid_to": None,
        "status": "active",
        "merged_into_entity_id": None,
        "provenance": {"source_refs": ["batch-1"], "epistemic_status": "inference", "evidence_grade": "U1"},
        "last_updated": "2026-01-01",
        "stale_after_months": 6,
    }


def _company(entity_id: str) -> dict:
    return {
        "entity_id": entity_id,
        "legacy_ids": [f"COMP-{entity_id}"],
        "canonical_name": "Acme Corp",
        "workspace_id": "ws-a",
        "valid_from": "2026-01-01",
        "valid_to": None,
        "status": "active",
        "merged_into_entity_id": None,
        "provenance": {"source_refs": ["batch-1"], "epistemic_status": "inference", "evidence_grade": "U1"},
        "last_updated": "2026-01-01",
    }


def _relationship(person_entity_id: str, company_entity_id: str, **overrides) -> dict:
    base = {
        "relationship_entity_id": f"rel-{person_entity_id}-{company_entity_id}",
        "legacy_ids": ["REL-1"],
        "person_entity_id": person_entity_id,
        "company_entity_id": company_entity_id,
        "job_title": "VP Engineering",
        "relationship_type": "employment",
        "current_status": "current",
        "valid_from": "2026-01-01",
        "valid_to": None,
        "provenance": {"source_refs": ["evidence-1"], "epistemic_status": "fact", "evidence_grade": "P1"},
    }
    base.update(overrides)
    return base


class PersonView360Tests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_unknown_person_returns_none(self) -> None:
        self.assertIsNone(get_person_360(self.root, "ws-a", "does-not-exist"))

    def test_composes_person_relationships_and_companies_as_distinct_sections(self) -> None:
        put_entity(self.root, "ws-a", "person", _person("p1"))
        put_entity(self.root, "ws-a", "company", _company("c1"))
        put_entity(self.root, "ws-a", "relationship", _relationship("p1", "c1"))

        view = get_person_360(self.root, "ws-a", "p1", as_of=date(2026, 6, 1))

        self.assertEqual("p1", view["person"]["entity_id"])
        self.assertEqual(1, len(view["relationships"]))
        self.assertEqual(1, len(view["companies"]))
        # No truth fusion: the relationship's own provenance/evidence_grade
        # is untouched by the person's provenance, and vice versa.
        self.assertEqual("P1", view["relationships"][0]["provenance"]["evidence_grade"])
        self.assertEqual("U1", view["person"]["provenance"]["evidence_grade"])

    def test_relationship_currentness_is_attached_without_mutating_provenance(self) -> None:
        put_entity(self.root, "ws-a", "person", _person("p1"))
        put_entity(self.root, "ws-a", "company", _company("c1"))
        put_entity(self.root, "ws-a", "relationship", _relationship("p1", "c1", valid_to="2026-03-01"))

        view = get_person_360(self.root, "ws-a", "p1", as_of=date(2026, 6, 1))

        relationship = view["relationships"][0]
        self.assertFalse(relationship["currentness"]["is_current"])
        self.assertEqual("P1", relationship["provenance"]["evidence_grade"])

    def test_contradictory_relationship_surfaces_as_requires_human_review(self) -> None:
        put_entity(self.root, "ws-a", "person", _person("p1"))
        put_entity(self.root, "ws-a", "company", _company("c1"))
        put_entity(
            self.root,
            "ws-a",
            "relationship",
            _relationship("p1", "c1", current_status="former", valid_to=None),
        )

        view = get_person_360(self.root, "ws-a", "p1", as_of=date(2026, 6, 1))

        self.assertTrue(view["relationships"][0]["currentness"]["requires_human_review"])

    def test_relationship_referencing_unbackfilled_company_is_omitted_not_crashed(self) -> None:
        put_entity(self.root, "ws-a", "person", _person("p1"))
        put_entity(self.root, "ws-a", "relationship", _relationship("p1", "c-not-backfilled-yet"))

        view = get_person_360(self.root, "ws-a", "p1", as_of=date(2026, 6, 1))

        self.assertEqual(1, len(view["relationships"]))
        self.assertEqual(0, len(view["companies"]))

    def test_other_persons_relationships_are_excluded(self) -> None:
        put_entity(self.root, "ws-a", "person", _person("p1"))
        put_entity(self.root, "ws-a", "person", _person("p2"))
        put_entity(self.root, "ws-a", "company", _company("c1"))
        put_entity(self.root, "ws-a", "relationship", _relationship("p2", "c1"))

        view = get_person_360(self.root, "ws-a", "p1", as_of=date(2026, 6, 1))

        self.assertEqual(0, len(view["relationships"]))


if __name__ == "__main__":
    unittest.main()
