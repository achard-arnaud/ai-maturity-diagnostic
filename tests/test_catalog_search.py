from __future__ import annotations

import unittest
from pathlib import Path

import yaml

from app.catalog_search import CatalogSearch


def _write_index(root: Path, offers: list[dict]) -> None:
    catalog = root / "product_catalog"
    catalog.mkdir(parents=True, exist_ok=True)
    (catalog / "index.yaml").write_text(
        yaml.safe_dump({"schema_version": "0.2", "offers": offers}), encoding="utf-8"
    )


def _write_offer(root: Path, file_name: str, offer: dict) -> None:
    (root / "product_catalog" / file_name).write_text(
        yaml.safe_dump({"schema_version": "0.2", "offer": offer}), encoding="utf-8"
    )


class CatalogSearchTests(unittest.TestCase):
    def setUp(self) -> None:
        import tempfile

        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

        _write_index(
            self.root,
            [
                {"offer_id": "OFFER-A", "file": "a.yaml", "name": "Astraforge", "status": "sourced"},
                {"offer_id": "OFFER-B", "file": "b.yaml", "name": "Learning Suite", "status": "draft"},
                {"offer_id": "OFFER-C", "file": "c.yaml", "name": "No Profile Offer", "status": "draft"},
            ],
        )
        _write_offer(
            self.root,
            "a.yaml",
            {
                "offer_id": "OFFER-A",
                "name": "Astraforge",
                "status": "sourced",
                "category": "governed-agent-execution-runtime",
                "positioning": {
                    "one_liner": "Transform agents that can reason into workers that can act durably.",
                    "category_statement": "Governed AI execution runtime for autonomous agents.",
                },
                "icp": {
                    "personas": {
                        "economic_sponsors": ["CTO", "CPO"],
                        "terrain_owners": ["Engineering_Manager"],
                    },
                    "maturity": {"positive_signals": ["Roadmap under delivery pressure"]},
                },
            },
        )
        _write_offer(
            self.root,
            "b.yaml",
            {
                "offer_id": "OFFER-B",
                "name": "Learning Suite",
                "status": "draft",
                "category": "human-capability-and-adoption",
                "positioning": {
                    "one_liner": "Build role-based AI capabilities and safe adoption practices.",
                },
                "icp": {
                    "personas": {"economic_sponsors": ["CHRO", "CLO"]},
                    "positive_signals": ["Uneven adoption across roles"],
                },
            },
        )
        # No offer file at all for OFFER-C: exercises the defensive
        # "profile missing entirely" path (index entry present, file absent).
        self.search = CatalogSearch(self.root)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_empty_query_returns_everything(self) -> None:
        results = self.search.search()
        self.assertEqual(len(results), 3)
        offer_ids = {r["offer_id"] for r in results}
        self.assertEqual(offer_ids, {"OFFER-A", "OFFER-B", "OFFER-C"})

    def test_text_query_matches_one_liner(self) -> None:
        results = self.search.search(query="durably")
        self.assertEqual([r["offer_id"] for r in results], ["OFFER-A"])
        self.assertIn("positioning.one_liner", results[0]["matched_on"])

    def test_text_query_matches_category_statement(self) -> None:
        results = self.search.search(query="autonomous agents")
        self.assertEqual([r["offer_id"] for r in results], ["OFFER-A"])
        self.assertIn("positioning.category_statement", results[0]["matched_on"])

    def test_category_filter(self) -> None:
        results = self.search.search(category="human-capability-and-adoption")
        self.assertEqual([r["offer_id"] for r in results], ["OFFER-B"])

    def test_status_filter(self) -> None:
        results = self.search.search(status="sourced")
        self.assertEqual([r["offer_id"] for r in results], ["OFFER-A"])

    def test_icp_field_present_on_one_offer_absent_on_another_does_not_crash(self) -> None:
        # "Engineering_Manager" only exists on OFFER-A's icp.personas.terrain_owners;
        # OFFER-B and OFFER-C have no such field/shape at all.
        results = self.search.search(query="engineering_manager")
        self.assertEqual([r["offer_id"] for r in results], ["OFFER-A"])
        self.assertIn("icp", results[0]["matched_on"])

    def test_no_results_for_unmatched_query(self) -> None:
        results = self.search.search(query="totally-unmatched-xyz-query")
        self.assertEqual(results, [])

    def test_missing_offer_file_is_defensive(self) -> None:
        # OFFER-C has no backing YAML file; a query that would only match
        # fields from a full profile must not crash and must simply skip it.
        results = self.search.search(query="no profile offer")
        self.assertEqual([r["offer_id"] for r in results], ["OFFER-C"])


if __name__ == "__main__":
    unittest.main()
