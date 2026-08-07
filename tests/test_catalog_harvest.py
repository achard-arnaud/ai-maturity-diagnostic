from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.catalog import CatalogHarvester
from app.core import ControlPlaneError
from scripts.advanced_research import EvidenceHit, SEARCHERS


class CatalogHarvesterTests(unittest.TestCase):
    def make_root(self, tmp: str) -> Path:
        root = Path(tmp)
        (root / "catalog_sources").mkdir()
        (root / "catalog_sources" / "shelves.yaml").write_text(
            'schema_version: "0.5"\nshelves:\n  - shelf_id: learning-adoption\n    name: Learning\n',
            encoding="utf-8",
        )
        (root / "product_catalog").mkdir()
        return root

    def test_stage_writes_only_private_candidate_area(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_root(tmp)
            result = CatalogHarvester(root).stage(
                {
                    "company": "Example Co",
                    "shelf_id": "learning-adoption",
                    "items": [{"name": "AI Academy", "raw_claims": ["Claim"]}],
                }
            )
            self.assertEqual("staged", result["status"])
            self.assertTrue(result["path"].startswith("data/private/catalog_harvest/example-co/"))
            self.assertEqual([], list((root / "product_catalog").iterdir()))
            self.assertFalse(
                result["harvest"]["promotion_contract"]["automatic_promotion_to_product_catalog"]
            )
            self.assertEqual(
                "product-icp-intelligence",
                result["harvest"]["promotion_contract"]["required_skill"],
            )

    def test_unknown_shelf_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_root(tmp)
            with self.assertRaises(ControlPlaneError):
                CatalogHarvester(root).stage(
                    {
                        "company": "Example Co",
                        "shelf_id": "unknown",
                        "items": [{"name": "AI Academy"}],
                    },
                    persist=False,
                )

    def test_raw_claims_must_be_structured_as_list(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_root(tmp)
            with self.assertRaises(ControlPlaneError):
                CatalogHarvester(root).stage(
                    {
                        "company": "Example Co",
                        "shelf_id": "learning-adoption",
                        "items": [{"name": "AI Academy", "raw_claims": "unstructured claim"}],
                    },
                    persist=False,
                )

    def test_public_discovery_stages_evidence_as_candidates_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_root(tmp)
            hit = EvidenceHit(
                source="web",
                title="Example Co AI Academy",
                url="https://example.com/academy",
                snippet="Public source claim.",
                relevance=0.8,
            )
            with patch.dict(SEARCHERS, {"web": lambda query, days, limit, enrich: [hit]}):
                result = CatalogHarvester(root).discover_public(
                    {
                        "company": "Example Co",
                        "shelf_id": "learning-adoption",
                        "source": "web",
                    },
                    persist=False,
                )
            self.assertEqual("preview", result["status"])
            candidate = result["harvest"]["items"][0]
            self.assertEqual("unreviewed_source_claim", candidate["epistemic_status"])
            self.assertEqual("candidate", candidate["promotion_status"])
            self.assertFalse(
                result["harvest"]["promotion_contract"]["automatic_promotion_to_product_catalog"]
            )


if __name__ == "__main__":
    unittest.main()
