"""/api/v1/workspaces/{workspace_id}/fit-assessments read/write model
(Epic 07 S05). Same auth/optimistic-concurrency shape as
app.demand_routes -- PATCH requires expected_version, 409 on stale or
duplicate, 404 on unknown, IDOR-safe cross-workspace 404s.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, status

from app.authruntime.deps import RequestContext, require_workspace_access
from app.fit_store import (
    FitAlreadyExists,
    FitConflict,
    FitNotFound,
    create_fit,
    get_fit,
    list_fits,
    update_fit,
)


def create_v1_fit_router(root: Path) -> APIRouter:
    router = APIRouter(prefix="/api/v1/workspaces/{workspace_id}")

    @router.get("/fit-assessments")
    def list_fits_route(
        workspace_id: str,
        status_filter: str | None = None,
        demand_id: str | None = None,
        limit: int = 20,
        cursor: str | None = None,
        _ctx: RequestContext = Depends(require_workspace_access()),
    ):
        if not 1 <= limit <= 100:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "limit must be between 1 and 100")
        page = list_fits(root, workspace_id, status=status_filter, demand_id=demand_id, limit=limit, cursor=cursor)
        return {"items": page.items, "next_cursor": page.next_cursor}

    @router.get("/fit-assessments/compare")
    def compare_fits_route(
        workspace_id: str,
        left_id: str,
        right_id: str,
        _ctx: RequestContext = Depends(require_workspace_access()),
    ):
        try:
            left, _ = get_fit(root, workspace_id, left_id)
            right, _ = get_fit(root, workspace_id, right_id)
        except FitNotFound as exc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "not found") from exc
        return {
            "left_id": left_id,
            "right_id": right_id,
            "left_verdict": (left.get("verdict") or {}).get("verdict"),
            "right_verdict": (right.get("verdict") or {}).get("verdict"),
            "same_input_lock": left["input_lock"]["input_hash"] == right["input_lock"]["input_hash"],
        }

    @router.get("/fit-assessments/{fit_assessment_id}")
    def get_fit_route(
        workspace_id: str,
        fit_assessment_id: str,
        _ctx: RequestContext = Depends(require_workspace_access()),
    ):
        try:
            assessment, version = get_fit(root, workspace_id, fit_assessment_id)
        except FitNotFound as exc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "not found") from exc
        return {**assessment, "version": version}

    @router.post("/fit-assessments")
    def create_fit_route(
        workspace_id: str,
        assessment: dict[str, Any] = Body(...),
        _ctx: RequestContext = Depends(require_workspace_access()),
    ):
        try:
            version = create_fit(root, workspace_id, assessment)
        except FitAlreadyExists as exc:
            raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
        return {**assessment, "version": version}

    @router.patch("/fit-assessments/{fit_assessment_id}")
    def patch_fit_route(
        workspace_id: str,
        fit_assessment_id: str,
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
            updated, new_version = update_fit(
                root, workspace_id, fit_assessment_id, _mutator, expected_version=expected_version,
            )
        except FitNotFound as exc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "not found") from exc
        except FitConflict as exc:
            raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
        return {**updated, "version": new_version}

    return router
