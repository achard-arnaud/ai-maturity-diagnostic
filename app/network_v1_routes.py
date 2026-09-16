"""/api/v1/workspaces/{workspace_id}/{people,companies,relationships} read
models (Epic 02 S04).

The first routes in this repo to use the target `/api/v1/...` shape from
docs/gtm-transformation/06_ROUTE_CONTEXT_AND_API_MODEL.md, instead of the
legacy flat `/api/network/...` surface. Read-only: GET list (paginated)
and GET by entity_id (stable deep link). Auth and workspace-scoping reuse
the same app.authruntime.deps dependencies every other workspace-scoped
route in this repo already uses, so a cross-workspace lookup 404s exactly
like app.authruntime.deps.require_workspace_access already documents
(ADR-007 §1: do not disclose that another workspace owns the object).
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status

from app.authruntime.deps import RequestContext, require_workspace_access
from app.network_v1_store import EntityNotFound, get_entity, list_entities
from app.person_view import get_person_360


def _paginated_response(root: Path, workspace_id: str, kind: str, limit: int, cursor: str | None) -> dict:
    if not 1 <= limit <= 100:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "limit must be between 1 and 100")
    page = list_entities(root, workspace_id, kind, limit=limit, cursor=cursor)
    return {"items": page.items, "next_cursor": page.next_cursor}


def _get_or_404(root: Path, workspace_id: str, kind: str, entity_id: str) -> dict:
    try:
        return get_entity(root, workspace_id, kind, entity_id)
    except EntityNotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "not found") from exc


def create_v1_network_router(root: Path) -> APIRouter:
    router = APIRouter(prefix="/api/v1/workspaces/{workspace_id}")

    @router.get("/people")
    def list_people(
        workspace_id: str,
        limit: int = 20,
        cursor: str | None = None,
        _ctx: RequestContext = Depends(require_workspace_access()),
    ):
        return _paginated_response(root, workspace_id, "person", limit, cursor)

    @router.get("/people/{entity_id}")
    def get_person(
        workspace_id: str,
        entity_id: str,
        _ctx: RequestContext = Depends(require_workspace_access()),
    ):
        return _get_or_404(root, workspace_id, "person", entity_id)

    @router.get("/companies")
    def list_companies(
        workspace_id: str,
        limit: int = 20,
        cursor: str | None = None,
        _ctx: RequestContext = Depends(require_workspace_access()),
    ):
        return _paginated_response(root, workspace_id, "company", limit, cursor)

    @router.get("/companies/{entity_id}")
    def get_company(
        workspace_id: str,
        entity_id: str,
        _ctx: RequestContext = Depends(require_workspace_access()),
    ):
        return _get_or_404(root, workspace_id, "company", entity_id)

    @router.get("/relationships")
    def list_relationships(
        workspace_id: str,
        limit: int = 20,
        cursor: str | None = None,
        _ctx: RequestContext = Depends(require_workspace_access()),
    ):
        return _paginated_response(root, workspace_id, "relationship", limit, cursor)

    @router.get("/relationships/{entity_id}")
    def get_relationship(
        workspace_id: str,
        entity_id: str,
        _ctx: RequestContext = Depends(require_workspace_access()),
    ):
        return _get_or_404(root, workspace_id, "relationship", entity_id)

    @router.get("/people/{entity_id}/360")
    def person_360(
        workspace_id: str,
        entity_id: str,
        _ctx: RequestContext = Depends(require_workspace_access()),
    ):
        view = get_person_360(root, workspace_id, entity_id)
        if view is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "not found")
        return view

    return router
