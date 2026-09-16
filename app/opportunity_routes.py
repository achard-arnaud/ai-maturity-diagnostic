"""Epic 11 S05: IDOR-safe Pipeline read endpoints."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status

from app.authruntime.deps import RequestContext, require_workspace_access
from app.opportunity_store import OpportunityNotFound, build_pipeline_board, get_opportunity, list_opportunities


def create_v1_opportunity_router(root: Path) -> APIRouter:
    router = APIRouter(prefix="/api/v1/workspaces/{workspace_id}")

    @router.get("/opportunities")
    def list_opportunities_route(workspace_id: str, stage: str | None = None, limit: int = 20, cursor: str | None = None, _ctx: RequestContext = Depends(require_workspace_access())):
        try:
            page = list_opportunities(root, workspace_id, stage=stage, limit=limit, cursor=cursor)
        except ValueError as exc:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
        return {"items": page.items, "next_cursor": page.next_cursor}

    @router.get("/opportunities/pipeline-board")
    def pipeline_board_route(workspace_id: str, _ctx: RequestContext = Depends(require_workspace_access())):
        return {"stages": build_pipeline_board(root, workspace_id)}

    @router.get("/opportunities/{opportunity_id}")
    def get_opportunity_route(workspace_id: str, opportunity_id: str, _ctx: RequestContext = Depends(require_workspace_access())):
        try:
            return get_opportunity(root, workspace_id, opportunity_id)
        except OpportunityNotFound as exc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "not found") from exc

    return router
