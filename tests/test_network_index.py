from __future__ import annotations

import json
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from app import network_index


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(item, ensure_ascii=False) + "\n" for item in records), encoding="utf-8")


def person(
    person_id: str,
    display_name: str,
    seed_company_id: str,
    *,
    status: str = "active",
    identity_confidence: str = "medium",
    role_hypotheses: list | None = None,
    last_updated: str = "2026-08-01",
    stale_after_months: int = 6,
) -> dict:
    return {
        "schema_version": "0.3",
        "person_id": person_id,
        "display_name": display_name,
        "normalized_name": display_name.lower(),
        "seed_company_id": seed_company_id,
        "identity_key_basis": "normalized_name_and_company",
        "relationship_ids": [],
        "role_hypotheses": role_hypotheses if role_hypotheses is not None else [],
        "identity_confidence": identity_confidence,
        "requires_identity_validation": False,
        "source_batch_ids": [],
        "status": status,
        "last_updated": last_updated,
        "stale_after_months": stale_after_months,
    }


def company(
    company_id: str,
    canonical_name: str,
    *,
    status: str = "active",
    sector_code: str | None = None,
    workspace_id: str | None = None,
) -> dict:
    return {
        "schema_version": "0.3",
        "company_id": company_id,
        "canonical_name": canonical_name,
        "normalized_name": canonical_name.lower(),
        "aliases": [],
        "countries": ["France"],
        "relationship_ids": [],
        "linked_person_ids": [],
        "contact_count": 0,
        "icb_mapping": {"sector": {"code": sector_code}} if sector_code else None,
        "network_screening": None,
        "study": None,
        "source_batch_ids": [],
        "workspace_id": workspace_id,
        "status": status,
        "last_updated": "2026-08-01",
        "stale_after_months": 6,
    }


class NetworkIndexTests(unittest.TestCase):
    def test_rebuild_from_missing_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_root = Path(tmp) / "network"
            index_path = Path(tmp) / "index.sqlite"
            counts = network_index.rebuild(data_root, index_path)
            self.assertEqual(counts, {"people": 0, "companies": 0, "relationships": 0})
            self.assertEqual(network_index.search_people(index_path), [])
            self.assertEqual(network_index.search_companies(index_path), [])

    def test_rebuild_from_empty_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_root = Path(tmp) / "network"
            data_root.mkdir(parents=True)
            (data_root / "people.jsonl").write_text("", encoding="utf-8")
            (data_root / "companies.jsonl").write_text("", encoding="utf-8")
            (data_root / "relationships.jsonl").write_text("", encoding="utf-8")
            index_path = Path(tmp) / "index.sqlite"
            counts = network_index.rebuild(data_root, index_path)
            self.assertEqual(counts, {"people": 0, "companies": 0, "relationships": 0})

    def _build_fixture(self, data_root: Path) -> None:
        stale_date = (date.today() - timedelta(days=400)).isoformat()
        people = [
            person(
                "PERS-1", "Alice Martin", "COMP-1", status="active",
                identity_confidence="high",
                role_hypotheses=[{"role": "economic_sponsor", "confidence": "medium"}],
            ),
            person(
                "PERS-2", "Bob Durand", "COMP-1", status="seeded",
                role_hypotheses=["veto_player"],
            ),
            person(
                "PERS-3", "Claire Petit", "COMP-2", status="refresh_due",
                last_updated=stale_date, stale_after_months=6,
            ),
        ]
        companies = [
            company("COMP-1", "EDF", sector_code="651010"),
            company("COMP-2", "Orange", sector_code="151020"),
        ]
        relationships = [
            {
                "schema_version": "0.3",
                "relationship_id": "REL-1",
                "person_id": "PERS-1",
                "company_id": "COMP-1",
                "job_title": "CIO",
                "country": "France",
                "relationship_type": "employment",
                "current_status": "current",
                "role_hypotheses": [],
                "source_refs": ["batch-1"],
                "observed_at": "2026-07-23",
                "epistemic_status": "inference",
                "evidence_grade": "U1",
                "requires_validation": False,
            }
        ]
        write_jsonl(data_root / "people.jsonl", people)
        write_jsonl(data_root / "companies.jsonl", companies)
        write_jsonl(data_root / "relationships.jsonl", relationships)

    def test_rebuild_and_search(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_root = Path(tmp) / "network"
            data_root.mkdir(parents=True)
            self._build_fixture(data_root)
            index_path = Path(tmp) / "index.sqlite"
            counts = network_index.rebuild(data_root, index_path)
            self.assertEqual(counts, {"people": 3, "companies": 2, "relationships": 1})

            # text search
            results = network_index.search_people(index_path, text="alice")
            self.assertEqual([r["person_id"] for r in results], ["PERS-1"])

            # status filter
            results = network_index.search_people(index_path, status="seeded")
            self.assertEqual([r["person_id"] for r in results], ["PERS-2"])

            # company_id filter
            results = network_index.search_people(index_path, company_id="COMP-1")
            self.assertEqual({r["person_id"] for r in results}, {"PERS-1", "PERS-2"})

            # role filter, dict-shaped role_hypotheses
            results = network_index.search_people(index_path, role="economic_sponsor")
            self.assertEqual([r["person_id"] for r in results], ["PERS-1"])

            # role filter, string-shaped role_hypotheses
            results = network_index.search_people(index_path, role="veto_player")
            self.assertEqual([r["person_id"] for r in results], ["PERS-2"])

            # stale_only filter
            results = network_index.search_people(index_path, stale_only=True)
            self.assertEqual([r["person_id"] for r in results], ["PERS-3"])

            # company search
            results = network_index.search_companies(index_path, text="edf")
            self.assertEqual([r["company_id"] for r in results], ["COMP-1"])

            results = network_index.search_companies(index_path, sector="151020")
            self.assertEqual([r["company_id"] for r in results], ["COMP-2"])

    def test_rebuild_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_root = Path(tmp) / "network"
            data_root.mkdir(parents=True)
            self._build_fixture(data_root)
            index_path = Path(tmp) / "index.sqlite"
            network_index.rebuild(data_root, index_path)
            first = network_index.search_people(index_path)
            network_index.rebuild(data_root, index_path)
            second = network_index.search_people(index_path)
            self.assertEqual(len(first), 3)
            self.assertEqual(len(second), 3)
            self.assertEqual(
                sorted(r["person_id"] for r in first),
                sorted(r["person_id"] for r in second),
            )


    def test_workspace_id_indexing_and_filtering(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_root = Path(tmp) / "network"
            data_root.mkdir(parents=True)
            people = [
                person("PERS-1", "Alice Martin", "COMP-1"),
                person("PERS-2", "Bob Durand", "COMP-2"),
                person("PERS-3", "Nobody Nowhere", "COMP-MISSING"),
            ]
            companies = [
                company("COMP-1", "EDF", workspace_id="acme-ws"),
                company("COMP-2", "Orange"),  # no workspace_id -> defaults to "default"
            ]
            write_jsonl(data_root / "people.jsonl", people)
            write_jsonl(data_root / "companies.jsonl", companies)
            write_jsonl(data_root / "relationships.jsonl", [])
            index_path = Path(tmp) / "index.sqlite"
            network_index.rebuild(data_root, index_path)

            # explicit workspace_id is indexed and filterable
            results = network_index.search_companies(index_path, workspace_id="acme-ws")
            self.assertEqual([r["company_id"] for r in results], ["COMP-1"])

            # company with no workspace_id defaults to "default" and is found
            results = network_index.search_companies(index_path, workspace_id="default")
            self.assertEqual([r["company_id"] for r in results], ["COMP-2"])

            # search_people resolves workspace through seed_company_id
            results = network_index.search_people(index_path, workspace_id="acme-ws")
            self.assertEqual([r["person_id"] for r in results], ["PERS-1"])

            # a person whose seed_company_id has no indexed company falls back to "default"
            results = network_index.search_people(index_path, workspace_id="default")
            self.assertEqual(
                {r["person_id"] for r in results},
                {"PERS-2", "PERS-3"},
            )


class FindPotentialDuplicatesTests(unittest.TestCase):
    def test_same_name_different_company_is_flagged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_root = Path(tmp)
            people = [
                person("PERS-1", "Jean Dupont", "COMP-1"),
                person("PERS-2", "Jean Dupont", "COMP-2"),
            ]
            write_jsonl(data_root / "people.jsonl", people)
            write_jsonl(data_root / "companies.jsonl", [])
            write_jsonl(data_root / "relationships.jsonl", [])
            index_path = Path(tmp) / "index.sqlite"
            network_index.rebuild(data_root, index_path)

            groups = network_index.find_potential_duplicates(index_path)
            self.assertEqual(len(groups), 1)
            self.assertEqual(groups[0]["normalized_name"], "jean dupont")
            person_ids = {r["person_id"] for r in groups[0]["records"]}
            self.assertEqual(person_ids, {"PERS-1", "PERS-2"})

    def test_different_names_are_not_flagged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_root = Path(tmp)
            people = [
                person("PERS-1", "Jean Dupont", "COMP-1"),
                person("PERS-2", "Marie Curie", "COMP-2"),
            ]
            write_jsonl(data_root / "people.jsonl", people)
            write_jsonl(data_root / "companies.jsonl", [])
            write_jsonl(data_root / "relationships.jsonl", [])
            index_path = Path(tmp) / "index.sqlite"
            network_index.rebuild(data_root, index_path)

            self.assertEqual(network_index.find_potential_duplicates(index_path), [])

    def test_single_person_produces_empty_list(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_root = Path(tmp)
            write_jsonl(data_root / "people.jsonl", [person("PERS-1", "Jean Dupont", "COMP-1")])
            write_jsonl(data_root / "companies.jsonl", [])
            write_jsonl(data_root / "relationships.jsonl", [])
            index_path = Path(tmp) / "index.sqlite"
            network_index.rebuild(data_root, index_path)

            self.assertEqual(network_index.find_potential_duplicates(index_path), [])

    def test_same_name_same_company_is_not_flagged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_root = Path(tmp)
            people = [
                person("PERS-1", "Jean Dupont", "COMP-1"),
                person("PERS-2", "Jean Dupont", "COMP-1"),
            ]
            write_jsonl(data_root / "people.jsonl", people)
            write_jsonl(data_root / "companies.jsonl", [])
            write_jsonl(data_root / "relationships.jsonl", [])
            index_path = Path(tmp) / "index.sqlite"
            network_index.rebuild(data_root, index_path)

            self.assertEqual(network_index.find_potential_duplicates(index_path), [])

    def test_missing_index_returns_empty_list(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(
                network_index.find_potential_duplicates(Path(tmp) / "missing.sqlite"), []
            )

    def test_group_carries_a_stable_group_key(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_root = Path(tmp)
            people = [
                person("PERS-1", "Jean Dupont", "COMP-1"),
                person("PERS-2", "Jean Dupont", "COMP-2"),
            ]
            write_jsonl(data_root / "people.jsonl", people)
            write_jsonl(data_root / "companies.jsonl", [])
            write_jsonl(data_root / "relationships.jsonl", [])
            index_path = Path(tmp) / "index.sqlite"
            network_index.rebuild(data_root, index_path)

            groups = network_index.find_potential_duplicates(index_path)
            self.assertTrue(groups[0]["group_key"])
            # Same group_key regardless of member ordering in the underlying rows.
            again = network_index.find_potential_duplicates(index_path)
            self.assertEqual(groups[0]["group_key"], again[0]["group_key"])

    def test_dismissed_group_is_excluded_by_default_when_root_given(self) -> None:
        from app.duplicate_dismissals import dismiss_duplicate_group

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data_root = root / "data" / "private" / "network"
            people = [
                person("PERS-1", "Jean Dupont", "COMP-1"),
                person("PERS-2", "Jean Dupont", "COMP-2"),
            ]
            write_jsonl(data_root / "people.jsonl", people)
            write_jsonl(data_root / "companies.jsonl", [])
            write_jsonl(data_root / "relationships.jsonl", [])
            index_path = data_root / "network_index.sqlite"
            network_index.rebuild(data_root, index_path)

            groups = network_index.find_potential_duplicates(index_path, root=root)
            self.assertEqual(len(groups), 1)
            dismiss_duplicate_group(root, ["PERS-1", "PERS-2"], actor="rep@acme.com")

            after = network_index.find_potential_duplicates(index_path, root=root)
            self.assertEqual(after, [])

            still_visible = network_index.find_potential_duplicates(index_path, root=root, include_dismissed=True)
            self.assertEqual(len(still_visible), 1)

    def test_without_root_dismissals_are_not_filtered(self) -> None:
        from app.duplicate_dismissals import dismiss_duplicate_group

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data_root = root / "data" / "private" / "network"
            people = [
                person("PERS-1", "Jean Dupont", "COMP-1"),
                person("PERS-2", "Jean Dupont", "COMP-2"),
            ]
            write_jsonl(data_root / "people.jsonl", people)
            write_jsonl(data_root / "companies.jsonl", [])
            write_jsonl(data_root / "relationships.jsonl", [])
            index_path = data_root / "network_index.sqlite"
            network_index.rebuild(data_root, index_path)
            dismiss_duplicate_group(root, ["PERS-1", "PERS-2"], actor="rep@acme.com")

            groups = network_index.find_potential_duplicates(index_path)
            self.assertEqual(len(groups), 1)


if __name__ == "__main__":
    unittest.main()
