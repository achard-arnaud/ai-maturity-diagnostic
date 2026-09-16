"""/api/v1/workspaces/{workspace_id}/companies/{company_entity_id}/360
Company 360 read model (Epic 04 S05).

Same auth shape as app.signal_routes/app.network_v1_routes -- reuses
require_workspace_access so cross-workspace access 404s exactly like
every other workspace-scoped route in this app.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends

from app.authruntime.deps import RequestContext, require_workspace_access
from app.company360_view import get_company_360


def create_v1_research_router(root: Path) -> APIRouter:
    router = APIRouter(prefix="/api/v1/workspaces/{workspace_id}")

    @router.get("/companies/{company_entity_id}/360")
    def get_company_360_route(
        workspace_id: str,
        company_entity_id: str,
        _ctx: RequestContext = Depends(require_workspace_access()),
    ):
        return get_company_360(root, workspace_id, company_entity_id)

    return router
