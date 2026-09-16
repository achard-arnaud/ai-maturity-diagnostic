"""/api/v1/workspaces/{workspace_id}/conversations read model (Epic 10
S05). Stop condition: "boucle fermée" -- same IDOR-safe, bounded-
pagination convention as every other v1 route (Epic 02-09).
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status

from app.authruntime.deps import RequestContext, require_workspace_access
from app.engagement_store import (
    ConversationNotFound,
    get_conversation,
    list_conversations,
    list_events_for_conversation,
    list_objections_for_event,
)


def create_v1_engagement_router(root: Path) -> APIRouter:
    router = APIRouter(prefix="/api/v1/workspaces/{workspace_id}")

    @router.get("/conversations")
    def list_conversations_route(
        workspace_id: str,
        status_filter: str | None = None,
        limit: int = 20,
        cursor: str | None = None,
        _ctx: RequestContext = Depends(require_workspace_access()),
    ):
        if not 1 <= limit <= 100:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "limit must be between 1 and 100")
        page = list_conversations(root, workspace_id, status=status_filter, limit=limit, cursor=cursor)
        return {"items": page.items, "next_cursor": page.next_cursor}

    @router.get("/conversations/{conversation_id}")
    def get_conversation_route(
        workspace_id: str,
        conversation_id: str,
        _ctx: RequestContext = Depends(require_workspace_access()),
    ):
        try:
            return get_conversation(root, workspace_id, conversation_id)
        except ConversationNotFound as exc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "not found") from exc

    @router.get("/conversations/{conversation_id}/events")
    def list_events_route(
        workspace_id: str,
        conversation_id: str,
        _ctx: RequestContext = Depends(require_workspace_access()),
    ):
        try:
            get_conversation(root, workspace_id, conversation_id)
        except ConversationNotFound as exc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "not found") from exc
        return {"items": list_events_for_conversation(root, workspace_id, conversation_id)}

    @router.get("/conversations/{conversation_id}/events/{engagement_event_id}/objections")
    def list_objections_route(
        workspace_id: str,
        conversation_id: str,
        engagement_event_id: str,
        _ctx: RequestContext = Depends(require_workspace_access()),
    ):
        try:
            get_conversation(root, workspace_id, conversation_id)
        except ConversationNotFound as exc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "not found") from exc
        return {"items": list_objections_for_event(root, workspace_id, engagement_event_id)}

    return router
