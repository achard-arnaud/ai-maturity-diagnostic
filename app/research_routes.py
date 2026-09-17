"""/api/v1/workspaces/{workspace_id}/companies/{company_entity_id}/360
Company 360 read model (Epic 04 S05), plus the ResearchCase queue
read model (Epic 04 S02 -- app.research_case_store) that the GTM
"Research" space (Epic 12 S03, app/frontend/gtm-spaces.js) depends on.

Same auth/pagination/IDOR shape as app.signal_routes -- reuses
require_workspace_access so cross-workspace access 404s exactly like
every other workspace-scoped route in this app.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status

from app.authruntime.deps import RequestContext, require_workspace_access
from app.company360_view import get_company_360
from app.research_case_store import ResearchCaseNotFound, get_case, list_cases


def create_v1_research_router(root: Path) -> APIRouter:
    router = APIRouter(prefix="/api/v1/workspaces/{workspace_id}")

    @router.get("/companies/{company_entity_id}/360")
    def get_company_360_route(
        workspace_id: str,
        company_entity_id: str,
        _ctx: RequestContext = Depends(require_workspace_access()),
    ):
        return get_company_360(root, workspace_id, company_entity_id)

    @router.get("/research-cases")
    def list_cases_route(
        workspace_id: str,
        status_filter: str | None = None,
        owner: str | None = None,
        limit: int = 20,
        cursor: str | None = None,
        _ctx: RequestContext = Depends(require_workspace_access()),
    ):
        if not 1 <= limit <= 100:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "limit must be between 1 and 100")
        page = list_cases(root, workspace_id, status=status_filter, owner=owner, limit=limit, cursor=cursor)
        return {"items": page.items, "next_cursor": page.next_cursor}

    @router.get("/research-cases/{research_case_id}")
    def get_case_route(
        workspace_id: str,
        research_case_id: str,
        _ctx: RequestContext = Depends(require_workspace_access()),
    ):
        try:
            return get_case(root, workspace_id, research_case_id)
        except ResearchCaseNotFound as exc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "not found") from exc

    return router
