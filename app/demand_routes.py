"""/api/v1/workspaces/{workspace_id}/demands read/write model (Epic 05 S04).

Same auth/pagination/IDOR shape as app.signal_routes/app.research_routes
-- reuses require_workspace_access. PATCH is optimistic-concurrency:
the caller must send the version it last read; a stale version gets 409,
never a silent overwrite of a concurrent edit ("mutation sûre").
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, status

from app.authruntime.deps import RequestContext, require_workspace_access
from app.demand_store import (
    DemandAlreadyExists,
    DemandConflict,
    DemandNotFound,
    create_demand,
    get_demand,
    list_demands,
    update_demand,
)


def create_v1_demand_router(root: Path) -> APIRouter:
    router = APIRouter(prefix="/api/v1/workspaces/{workspace_id}")

    @router.get("/demands")
    def list_demands_route(
        workspace_id: str,
        status_filter: str | None = None,
        company_entity_id: str | None = None,
        limit: int = 20,
        cursor: str | None = None,
        _ctx: RequestContext = Depends(require_workspace_access()),
    ):
        if not 1 <= limit <= 100:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "limit must be between 1 and 100")
        page = list_demands(
            root, workspace_id, status=status_filter, company_entity_id=company_entity_id,
            limit=limit, cursor=cursor,
        )
        return {"items": page.items, "next_cursor": page.next_cursor}

    @router.get("/demands/{demand_id}")
    def get_demand_route(
        workspace_id: str,
        demand_id: str,
        _ctx: RequestContext = Depends(require_workspace_access()),
    ):
        try:
            demand, version = get_demand(root, workspace_id, demand_id)
        except DemandNotFound as exc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "not found") from exc
        return {**demand, "version": version}

    @router.post("/demands")
    def create_demand_route(
        workspace_id: str,
        demand: dict[str, Any] = Body(...),
        _ctx: RequestContext = Depends(require_workspace_access()),
    ):
        try:
            version = create_demand(root, workspace_id, demand)
        except DemandAlreadyExists as exc:
            raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
        return {**demand, "version": version}

    @router.patch("/demands/{demand_id}")
    def patch_demand_route(
        workspace_id: str,
        demand_id: str,
        payload: dict[str, Any] = Body(...),
        _ctx: RequestContext = Depends(require_workspace_access()),
    ):
        if "expected_version" not in payload:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "expected_version is required")
        expected_version = payload["expected_version"]
        changes = {k: v for k, v in payload.items() if k != "expected_version"}

        def _mutator(current: dict[str, Any]) -> dict[str, Any]:
            return {**current, **changes}

        try:
            updated, new_version = update_demand(
                root, workspace_id, demand_id, _mutator, expected_version=expected_version,
            )
        except DemandNotFound as exc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "not found") from exc
        except DemandConflict as exc:
            raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
        return {**updated, "version": new_version}

    return router
