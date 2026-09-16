"""/api/v1/workspaces/{workspace_id}/signals read model (Epic 03 S05).

Same auth/pagination/IDOR shape as app.network_v1_routes (Epic 02 S04) --
reuses require_workspace_access so cross-workspace access 404s exactly
like every other workspace-scoped route in this app.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status

from app.authruntime.deps import RequestContext, require_workspace_access
from app.signal_handoff import SignalHandoffError, queue_research
from app.signal_store import SignalNotFound, get_signal, list_signals


def create_v1_signal_router(root: Path) -> APIRouter:
    router = APIRouter(prefix="/api/v1/workspaces/{workspace_id}")

    @router.get("/signals")
    def list_signals_route(
        workspace_id: str,
        status_filter: str | None = None,
        source_kind: str | None = None,
        limit: int = 20,
        cursor: str | None = None,
        _ctx: RequestContext = Depends(require_workspace_access()),
    ):
        if not 1 <= limit <= 100:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "limit must be between 1 and 100")
        page = list_signals(root, workspace_id, status=status_filter, source_kind=source_kind, limit=limit, cursor=cursor)
        return {"items": page.items, "next_cursor": page.next_cursor}

    @router.get("/signals/{signal_id}")
    def get_signal_route(
        workspace_id: str,
        signal_id: str,
        _ctx: RequestContext = Depends(require_workspace_access()),
    ):
        try:
            return get_signal(root, workspace_id, signal_id)
        except SignalNotFound as exc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "not found") from exc

    @router.post("/signals/{signal_id}/queue-research")
    def queue_research_route(
        workspace_id: str,
        signal_id: str,
        ctx: RequestContext = Depends(require_workspace_access()),
    ):
        try:
            signal = get_signal(root, workspace_id, signal_id)
        except SignalNotFound as exc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "not found") from exc
        try:
            event = queue_research(root, signal, requested_by=ctx.email)
        except SignalHandoffError as exc:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
        return event

    return router
