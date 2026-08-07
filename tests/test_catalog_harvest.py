from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.catalog import CatalogHarvester
from app.core import ControlPlaneError


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


if __name__ == "__main__":
    unittest.main()
