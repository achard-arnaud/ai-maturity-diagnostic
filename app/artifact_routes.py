"""/api/v1/workspaces/{workspace_id}/artifacts (Epic 15 S04).

Read/discovery API over app.artifact_index (S03) -- the same auth/
pagination/IDOR shape as every other v1 route (require_workspace_access,
cross-workspace 404, bounded pagination). Archive/restore (S05) live
here too since they are the one artifact-index-owned write.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status

from app.artifact_archive_store import archive_artifact, restore_artifact
from app.artifact_index import ArtifactNotFound, ArtifactPolicyError, get_artifact, list_artifacts
from app.artifact_policy import can_archive, can_restore
from app.authruntime.deps import RequestContext, require_workspace_access


def create_v1_artifact_router(root: Path) -> APIRouter:
    router = APIRouter(prefix="/api/v1/workspaces/{workspace_id}")

    @router.get("/artifacts")
    def list_artifacts_route(
        workspace_id: str,
        kind: str | None = None,
        related_to: str | None = None,
        run_id: str | None = None,
        status_filter: str | None = None,
        q: str | None = None,
        limit: int = 20,
        cursor: str | None = None,
        _ctx: RequestContext = Depends(require_workspace_access()),
    ):
        if not 1 <= limit <= 100:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "limit must be between 1 and 100")
        try:
            page = list_artifacts(
                root,
                workspace_id,
                kind=kind,
                related_to=related_to,
                run_id=run_id,
                status=status_filter,
                q=q,
                limit=limit,
                cursor=cursor,
            )
        except ArtifactPolicyError as exc:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
        return {"items": page.items, "next_cursor": page.next_cursor}

    @router.get("/artifacts/{artifact_id:path}")
    def get_artifact_route(
        workspace_id: str,
        artifact_id: str,
        _ctx: RequestContext = Depends(require_workspace_access()),
    ):
        try:
            return get_artifact(root, workspace_id, artifact_id)
        except ArtifactNotFound as exc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "not found") from exc

    @router.post("/artifacts/{artifact_id:path}/archive")
    def archive_artifact_route(
        workspace_id: str,
        artifact_id: str,
        ctx: RequestContext = Depends(require_workspace_access()),
    ):
        try:
            artifact = get_artifact(root, workspace_id, artifact_id)
        except ArtifactNotFound as exc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "not found") from exc
        if not can_archive(artifact):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"artifact is already {artifact['status']}")
        archive_artifact(root, workspace_id, artifact_id, actor=ctx.email, archived_at=datetime.now(timezone.utc).isoformat())
        return get_artifact(root, workspace_id, artifact_id)

    @router.post("/artifacts/{artifact_id:path}/restore")
    def restore_artifact_route(
        workspace_id: str,
        artifact_id: str,
        _ctx: RequestContext = Depends(require_workspace_access()),
    ):
        try:
            artifact = get_artifact(root, workspace_id, artifact_id)
        except ArtifactNotFound as exc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "not found") from exc
        if not can_restore(artifact):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"artifact is not archived (status={artifact['status']})")
        restore_artifact(root, workspace_id, artifact_id)
        return get_artifact(root, workspace_id, artifact_id)

    return router
