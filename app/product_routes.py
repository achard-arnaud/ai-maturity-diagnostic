"""/api/v1/workspaces/{workspace_id}/products read model (Epic 06 S05).

Deep links are stable: GET .../products/{product_id} and
GET .../products/{product_id}/snapshots/{snapshot_id} always return the
identical record for the same id (immutability from S01/S03 makes this
trivially true for snapshots; products are only ever upserted by their
own owner). Visibility is enforced via app.product_visibility -- a
product/snapshot invisible to this workspace 404s exactly like an
unknown one, never leaking its existence.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status

from app.authruntime.deps import RequestContext, require_workspace_access
from app.product_diff import diff_snapshot_content
from app.product_snapshot_store import ProductSnapshotNotFound, get_snapshot
from app.product_store import ProductNotFound, get_product, list_all_products
from app.product_visibility import filter_visible_products


def create_v1_product_router(root: Path) -> APIRouter:
    router = APIRouter(prefix="/api/v1/workspaces/{workspace_id}")

    @router.get("/products")
    def list_products_route(
        workspace_id: str,
        _ctx: RequestContext = Depends(require_workspace_access()),
    ):
        visible = filter_visible_products(list_all_products(root), workspace_id=workspace_id)
        return {"items": visible}

    @router.get("/products/{product_id}")
    def get_product_route(
        workspace_id: str,
        product_id: str,
        _ctx: RequestContext = Depends(require_workspace_access()),
    ):
        try:
            product = get_product(root, product_id)
        except ProductNotFound as exc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "not found") from exc
        if not filter_visible_products([product], workspace_id=workspace_id):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "not found")
        return product

    @router.get("/products/{product_id}/snapshots/{snapshot_id}")
    def get_snapshot_route(
        workspace_id: str,
        product_id: str,
        snapshot_id: str,
        _ctx: RequestContext = Depends(require_workspace_access()),
    ):
        try:
            snapshot = get_snapshot(root, snapshot_id)
        except ProductSnapshotNotFound as exc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "not found") from exc
        if snapshot["product_id"] != product_id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "not found")
        if snapshot["owner_scope"]["kind"] == "workspace" and snapshot["owner_scope"]["workspace_id"] != workspace_id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "not found")
        return snapshot

    @router.get("/products/{product_id}/diff")
    def diff_snapshots_route(
        workspace_id: str,
        product_id: str,
        from_snapshot_id: str,
        to_snapshot_id: str,
        _ctx: RequestContext = Depends(require_workspace_access()),
    ):
        try:
            old_snapshot = get_snapshot(root, from_snapshot_id)
            new_snapshot = get_snapshot(root, to_snapshot_id)
        except ProductSnapshotNotFound as exc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "not found") from exc
        if old_snapshot["product_id"] != product_id or new_snapshot["product_id"] != product_id:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "snapshots do not belong to this product")
        return {
            "from_snapshot_id": from_snapshot_id,
            "to_snapshot_id": to_snapshot_id,
            "diff": diff_snapshot_content(old_snapshot["content"], new_snapshot["content"]),
        }

    return router
