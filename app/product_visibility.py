"""Epic 06 S04: catalog ownership/subscription model per ADR-008.

Stop condition: "pas de fuite cross-workspace" (no cross-workspace
leakage). A workspace's catalog view is a deterministic projection:
every shared-core product/snapshot, plus that workspace's own overlays
-- never another workspace's overlay, and never a silent visibility
change to a shared entry.
"""

from __future__ import annotations

from typing import Mapping, Sequence


class OverlayError(Exception):
    pass


def _is_visible(owner_scope: Mapping, *, workspace_id: str) -> bool:
    if owner_scope["kind"] == "shared":
        return True
    return owner_scope["kind"] == "workspace" and owner_scope.get("workspace_id") == workspace_id


def filter_visible_products(products: Sequence[Mapping], *, workspace_id: str) -> list[Mapping]:
    return [p for p in products if _is_visible(p["owner_scope"], workspace_id=workspace_id)]


def filter_visible_snapshots(snapshots: Sequence[Mapping], *, workspace_id: str) -> list[Mapping]:
    return [s for s in snapshots if _is_visible(s["owner_scope"], workspace_id=workspace_id)]


def validate_overlay_product(product: Mapping, *, shared_product_ids: set[str]) -> None:
    """Enforce ADR-008's "no silent shadowing" rule at the point an
    overlay product is created/published.

    - A shared product must never carry overlay_of_product_id.
    - A workspace product's overlay_of_product_id, if set, must name an
      *existing* shared product -- overlaying a product that doesn't
      exist is exactly the silent-shadowing failure mode ADR-008 forbids.
    """
    owner_scope = product["owner_scope"]
    overlay_of = product.get("overlay_of_product_id")

    if owner_scope["kind"] == "shared":
        if overlay_of is not None:
            raise OverlayError("a shared product can never overlay another product")
        return

    if overlay_of is not None and overlay_of not in shared_product_ids:
        raise OverlayError(
            f"overlay_of_product_id {overlay_of!r} does not name an existing shared product "
            "-- silent shadowing is forbidden (ADR-008)"
        )
