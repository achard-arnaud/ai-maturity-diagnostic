"""/api/v1/workspaces/{workspace_id}/target-plans read/write model
(Epic 08 S05). Stop condition: "accès borné" (bounded access) --
IDOR-safe cross-workspace 404s (same convention as every other v1
route), and pagination is always bounded (1-100), never unbounded.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status

from app.authruntime.deps import RequestContext, require_workspace_access
from app.buying_committee_view import build_committee_graph
from app.target_plan_store import (
    TargetPlanNotFound,
    get_plan,
    list_plans,
    list_stakeholders_for_plan,
)


def create_v1_target_plan_router(root: Path) -> APIRouter:
    router = APIRouter(prefix="/api/v1/workspaces/{workspace_id}")

    @router.get("/target-plans")
    def list_plans_route(
        workspace_id: str,
        status_filter: str | None = None,
        limit: int = 20,
        cursor: str | None = None,
        _ctx: RequestContext = Depends(require_workspace_access()),
    ):
        if not 1 <= limit <= 100:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "limit must be between 1 and 100")
        page = list_plans(root, workspace_id, status=status_filter, limit=limit, cursor=cursor)
        return {"items": page.items, "next_cursor": page.next_cursor}

    @router.get("/target-plans/{target_plan_id}")
    def get_plan_route(
        workspace_id: str,
        target_plan_id: str,
        _ctx: RequestContext = Depends(require_workspace_access()),
    ):
        try:
            plan = get_plan(root, workspace_id, target_plan_id)
        except TargetPlanNotFound as exc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "not found") from exc
        return plan

    @router.get("/target-plans/{target_plan_id}/stakeholders")
    def list_stakeholders_route(
        workspace_id: str,
        target_plan_id: str,
        _ctx: RequestContext = Depends(require_workspace_access()),
    ):
        try:
            get_plan(root, workspace_id, target_plan_id)
        except TargetPlanNotFound as exc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "not found") from exc
        stakeholders = list_stakeholders_for_plan(root, workspace_id, target_plan_id)
        return {"items": stakeholders}

    @router.get("/target-plans/{target_plan_id}/committee-graph")
    def get_committee_graph_route(
        workspace_id: str,
        target_plan_id: str,
        _ctx: RequestContext = Depends(require_workspace_access()),
    ):
        try:
            get_plan(root, workspace_id, target_plan_id)
        except TargetPlanNotFound as exc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "not found") from exc
        stakeholders = list_stakeholders_for_plan(root, workspace_id, target_plan_id)
        active = [s for s in stakeholders if s["status"] == "active"]
        return build_committee_graph(active, {})

    return router
