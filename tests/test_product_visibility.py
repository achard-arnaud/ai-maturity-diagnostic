from __future__ import annotations

import unittest

from app.product_visibility import (
    OverlayError,
    filter_visible_products,
    filter_visible_snapshots,
    validate_overlay_product,
)


def _shared(product_id: str) -> dict:
    return {"product_id": product_id, "owner_scope": {"kind": "shared", "workspace_id": None}, "overlay_of_product_id": None}


def _workspace(product_id: str, workspace_id: str, overlay_of: str | None = None) -> dict:
    return {
        "product_id": product_id,
        "owner_scope": {"kind": "workspace", "workspace_id": workspace_id},
        "overlay_of_product_id": overlay_of,
    }


class VisibilityFilterTests(unittest.TestCase):
    def test_shared_products_visible_to_every_workspace(self) -> None:
        products = [_shared("p-shared")]
        self.assertEqual(["p-shared"], [p["product_id"] for p in filter_visible_products(products, workspace_id="ws-a")])
        self.assertEqual(["p-shared"], [p["product_id"] for p in filter_visible_products(products, workspace_id="ws-b")])

    def test_workspace_overlay_visible_only_to_its_own_workspace(self) -> None:
        products = [_workspace("p-a", "ws-a")]
        self.assertEqual(["p-a"], [p["product_id"] for p in filter_visible_products(products, workspace_id="ws-a")])
        self.assertEqual([], [p["product_id"] for p in filter_visible_products(products, workspace_id="ws-b")])

    def test_no_cross_workspace_leakage_with_mixed_catalog(self) -> None:
        products = [_shared("p-shared"), _workspace("p-a", "ws-a"), _workspace("p-b", "ws-b")]
        visible_to_a = {p["product_id"] for p in filter_visible_products(products, workspace_id="ws-a")}
        visible_to_b = {p["product_id"] for p in filter_visible_products(products, workspace_id="ws-b")}
        self.assertEqual({"p-shared", "p-a"}, visible_to_a)
        self.assertEqual({"p-shared", "p-b"}, visible_to_b)
        self.assertNotIn("p-b", visible_to_a)
        self.assertNotIn("p-a", visible_to_b)

    def test_snapshot_visibility_follows_same_rule(self) -> None:
        snapshots = [
            {"snapshot_id": "s1", "owner_scope": {"kind": "shared", "workspace_id": None}},
            {"snapshot_id": "s2", "owner_scope": {"kind": "workspace", "workspace_id": "ws-a"}},
        ]
        visible_to_a = {s["snapshot_id"] for s in filter_visible_snapshots(snapshots, workspace_id="ws-a")}
        visible_to_b = {s["snapshot_id"] for s in filter_visible_snapshots(snapshots, workspace_id="ws-b")}
        self.assertEqual({"s1", "s2"}, visible_to_a)
        self.assertEqual({"s1"}, visible_to_b)


class OverlayValidationTests(unittest.TestCase):
    def test_shared_product_cannot_overlay_anything(self) -> None:
        product = _shared("p-shared")
        product["overlay_of_product_id"] = "some-base"
        with self.assertRaises(OverlayError):
            validate_overlay_product(product, shared_product_ids={"some-base"})

    def test_standalone_workspace_product_is_valid(self) -> None:
        product = _workspace("p-a", "ws-a")
        validate_overlay_product(product, shared_product_ids=set())  # should not raise

    def test_overlay_of_existing_shared_product_is_valid(self) -> None:
        product = _workspace("p-a", "ws-a", overlay_of="p-shared")
        validate_overlay_product(product, shared_product_ids={"p-shared"})  # should not raise

    def test_overlay_of_nonexistent_shared_product_is_silent_shadowing_and_rejected(self) -> None:
        product = _workspace("p-a", "ws-a", overlay_of="p-does-not-exist")
        with self.assertRaises(OverlayError):
            validate_overlay_product(product, shared_product_ids={"p-shared"})


if __name__ == "__main__":
    unittest.main()
