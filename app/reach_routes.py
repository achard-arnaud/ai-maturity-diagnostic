"""/api/v1/workspaces/{workspace_id}/sequences read model (Epic 09
S05). Stop condition: "stable v1" -- same IDOR-safe, bounded-pagination
convention as every other v1 route (Epic 02-08).
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status

from app.authruntime.deps import RequestContext, require_workspace_access
from app.reach_store import (
    SequenceNotFound,
    get_sequence,
    list_sequences,
    list_steps_for_sequence,
    list_tasks_for_sequence,
    list_touchpoints_for_step,
)


def create_v1_reach_router(root: Path) -> APIRouter:
    router = APIRouter(prefix="/api/v1/workspaces/{workspace_id}")

    @router.get("/sequences")
    def list_sequences_route(
        workspace_id: str,
        status_filter: str | None = None,
        limit: int = 20,
        cursor: str | None = None,
        _ctx: RequestContext = Depends(require_workspace_access()),
    ):
        if not 1 <= limit <= 100:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "limit must be between 1 and 100")
        page = list_sequences(root, workspace_id, status=status_filter, limit=limit, cursor=cursor)
        return {"items": page.items, "next_cursor": page.next_cursor}

    @router.get("/sequences/{sequence_id}")
    def get_sequence_route(
        workspace_id: str,
        sequence_id: str,
        _ctx: RequestContext = Depends(require_workspace_access()),
    ):
        try:
            return get_sequence(root, workspace_id, sequence_id)
        except SequenceNotFound as exc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "not found") from exc

    @router.get("/sequences/{sequence_id}/steps")
    def list_steps_route(
        workspace_id: str,
        sequence_id: str,
        _ctx: RequestContext = Depends(require_workspace_access()),
    ):
        try:
            get_sequence(root, workspace_id, sequence_id)
        except SequenceNotFound as exc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "not found") from exc
        return {"items": list_steps_for_sequence(root, workspace_id, sequence_id)}

    @router.get("/sequences/{sequence_id}/tasks")
    def list_tasks_route(
        workspace_id: str,
        sequence_id: str,
        _ctx: RequestContext = Depends(require_workspace_access()),
    ):
        try:
            get_sequence(root, workspace_id, sequence_id)
        except SequenceNotFound as exc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "not found") from exc
        return {"items": list_tasks_for_sequence(root, workspace_id, sequence_id)}

    @router.get("/sequences/{sequence_id}/steps/{step_id}/touchpoints")
    def list_touchpoints_route(
        workspace_id: str,
        sequence_id: str,
        step_id: str,
        _ctx: RequestContext = Depends(require_workspace_access()),
    ):
        try:
            get_sequence(root, workspace_id, sequence_id)
        except SequenceNotFound as exc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "not found") from exc
        return {"items": list_touchpoints_for_step(root, workspace_id, step_id)}

    return router
