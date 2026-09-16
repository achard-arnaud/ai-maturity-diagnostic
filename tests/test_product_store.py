from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.product_store import ProductNotFound, get_product, list_all_products, put_product


def _product(product_id: str, *, kind: str = "shared", workspace_id: str | None = None) -> dict:
    return {
        "product_id": product_id,
        "owner_scope": {"kind": kind, "workspace_id": workspace_id},
        "name": "Acme",
        "status": "active",
        "created_at": "2026-01-01T00:00:00+00:00",
        "overlay_of_product_id": None,
    }


class ProductStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_put_then_get_round_trips(self) -> None:
        put_product(self.root, _product("p1"))
        record = get_product(self.root, "p1")
        self.assertEqual("p1", record["product_id"])

    def test_get_missing_product_raises(self) -> None:
        with self.assertRaises(ProductNotFound):
            get_product(self.root, "nope")

    def test_put_upserts_by_id(self) -> None:
        put_product(self.root, _product("p1"))
        updated = _product("p1")
        updated["status"] = "archived"
        put_product(self.root, updated)
        record = get_product(self.root, "p1")
        self.assertEqual("archived", record["status"])
        self.assertEqual(1, len(list_all_products(self.root)))

    def test_list_all_is_sorted(self) -> None:
        put_product(self.root, _product("p3"))
        put_product(self.root, _product("p1"))
        put_product(self.root, _product("p2"))
        ids = [p["product_id"] for p in list_all_products(self.root)]
        self.assertEqual(["p1", "p2", "p3"], ids)


if __name__ == "__main__":
    unittest.main()
