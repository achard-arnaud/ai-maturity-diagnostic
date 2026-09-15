from __future__ import annotations

import mimetypes
import os
import subprocess
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse, Response

from app.authruntime.app import create_app
from app.authruntime.config import AuthConfig, assert_safe_bind
from app.authruntime.db import ControlStore
from app.authruntime.deps import RequestContext, get_current_user
from app.authruntime.oidc import OIDCClient
from app.blocker_actions import BlockerActionLog
from app.catalog import CatalogHarvester
from app.catalog_search import CatalogSearch
from app.core import ControlPlaneError, RepoControlPlane
from app.dashboard import FollowUpDashboard, UseCaseHeritage
from app.demand import DemandCatalog
from app.network_index import search_companies, search_people
from app.nudging import UseCaseNudger
from app.qualification import QualificationCockpit
from app.reach import ReachMatchmaker
from app.uc_graph import UseCaseGraph
from app.value_chain import ValueChainCatalog
from app.workflows import WorkflowPlanner

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "app" / "frontend"
CONTROL = RepoControlPlane(ROOT)
HARVESTER = CatalogHarvester(ROOT)
CATALOG_SEARCH = CatalogSearch(ROOT)
DEMAND = DemandCatalog(ROOT)
QUALIFICATION = QualificationCockpit(ROOT)
NUDGING = UseCaseNudger(ROOT)
VALUE_CHAIN = ValueChainCatalog(ROOT)
UC_GRAPH = UseCaseGraph(ROOT)
REACH = ReachMatchmaker(ROOT)
FOLLOWUP = FollowUpDashboard(ROOT)
HERITAGE = UseCaseHeritage(ROOT)
WORKFLOWS = WorkflowPlanner(ROOT)
BLOCKER_ACTIONS = BlockerActionLog(ROOT)
# Derived, rebuildable SQLite search index over data/private/network/*.jsonl
# (see app/network_index.py). Never a write target; rebuilt out-of-band via
# scripts/rebuild_network_index.py, not on every request.
NETWORK_INDEX_PATH = ROOT / "data" / "private" / "network" / "network_index.sqlite"

# Routes open to unauthenticated callers: the health probe (used by
# uptime/ops checks that have no session) and the static SPA shell/login
# page, whose own client-side JS is what performs the auth check (via
# /api/auth/me) and redirects to /login.html on a 401. Gating index.html
# itself would make that redirect impossible to reach. Every /api/* data
# route below is authenticated by default per ADR-007 §7 sprint scope.
_STATIC_FILES = {
    "/": "index.html",
    "/app.js": "app.js",
    "/styles.css": "styles.css",
    "/login.html": "login.html",
    "/vendor/mermaid.min.js": "vendor/mermaid.min.js",
}


async def _json_body(request: Request) -> dict[str, Any]:
    raw = await request.body()
    if len(raw) > 1_000_000:
        raise ControlPlaneError("request body too large")
    if not raw:
        return {}
    import json

    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as exc:
        raise ControlPlaneError("invalid JSON body") from exc
    if not isinstance(data, dict):
        raise ControlPlaneError("JSON body must be an object")
    return data


def _static_response(name: str) -> Response:
    target = (FRONTEND / name).resolve()
    try:
        target.relative_to(FRONTEND.resolve())
    except ValueError:
        return Response(status_code=404)
    if not target.is_file():
        return Response(status_code=404)
    content_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
    if content_type.startswith("text/") or content_type == "application/javascript":
        content_type += "; charset=utf-8"
    return FileResponse(target, media_type=content_type)


def build_app(
    *,
    control_store: ControlStore | None = None,
    oidc_client: OIDCClient | None = None,
    config: AuthConfig | None = None,
    session_secret: str | None = None,
) -> FastAPI:
    """Build the single ASGI app: authruntime (S8a) plus the business routes.

    Per ADR-007 §6, this is the only module allowed to depend on
    FastAPI/Starlette outside app/authruntime/*; the business module
    singletons above stay plain Python and are called, never subclassed
    or reimplemented, from these thin route handlers.
    """

    app = create_app(
        control_store=control_store,
        oidc_client=oidc_client,
        config=config,
        session_secret=session_secret,
    )

    # ------------------------------------------------------------------
    # Error handling parity with the old stdlib Handler (ADR-004/S1).
    # ------------------------------------------------------------------
    @app.exception_handler(ControlPlaneError)
    async def _control_plane_error(request: Request, exc: ControlPlaneError) -> JSONResponse:
        return JSONResponse(status_code=400, content={"status": "error", "error": str(exc)})

    @app.exception_handler(subprocess.TimeoutExpired)
    async def _timeout(request: Request, exc: subprocess.TimeoutExpired) -> JSONResponse:
        return JSONResponse(status_code=504, content={"status": "error", "error": "skill executor timed out"})

    @app.exception_handler(Exception)
    async def _unexpected(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(status_code=500, content={"status": "error", "error": str(exc)})

    # ------------------------------------------------------------------
    # Auth introspection for the frontend (drives the /login.html redirect).
    # ------------------------------------------------------------------
    @app.get("/api/auth/me")
    async def auth_me(ctx: RequestContext = Depends(get_current_user)) -> dict[str, Any]:
        return {
            "user_id": ctx.user_id,
            "email": ctx.email,
            "is_admin": ctx.is_admin,
            "role": ctx.role,
            "workspace_id": ctx.workspace_id,
        }

    # ------------------------------------------------------------------
    # GET data routes (open: /api/health; authenticated: everything else).
    # ------------------------------------------------------------------
    @app.get("/api/health")
    async def health() -> dict[str, Any]:
        return {
            "status": "ok",
            "version": "0.7",
            "executor_configured": bool(os.getenv("AI_DIAGNOSTIC_SKILL_EXECUTOR", "").strip()),
        }

    @app.get("/api/qualification/actions")
    async def list_blocker_actions(study_id: str = "", ctx: RequestContext = Depends(get_current_user)) -> Any:
        return BLOCKER_ACTIONS.list_actions(study_id.strip())

    @app.get("/api/skills")
    async def api_skills(ctx: RequestContext = Depends(get_current_user)) -> Any:
        return CONTROL.list_skills()

    @app.get("/api/offers")
    async def api_offers(ctx: RequestContext = Depends(get_current_user)) -> Any:
        return CONTROL.list_offers()

    @app.get("/api/shelves")
    async def api_shelves(ctx: RequestContext = Depends(get_current_user)) -> Any:
        return CONTROL.list_shelves()

    @app.get("/api/backlog")
    async def api_backlog(ctx: RequestContext = Depends(get_current_user)) -> Any:
        return CONTROL.backlog()

    @app.get("/api/demand")
    async def api_demand(ctx: RequestContext = Depends(get_current_user)) -> Any:
        return DEMAND.snapshot()

    @app.get("/api/demand/inventories")
    async def api_demand_inventories(ctx: RequestContext = Depends(get_current_user)) -> Any:
        return DEMAND.inventories()

    @app.get("/api/qualification")
    async def api_qualification(ctx: RequestContext = Depends(get_current_user)) -> Any:
        return QUALIFICATION.list_studies()

    @app.get("/api/nudging/inventories")
    async def api_nudging_inventories(ctx: RequestContext = Depends(get_current_user)) -> Any:
        return NUDGING.list_inventories()

    @app.get("/api/value-chain")
    async def api_value_chain(ctx: RequestContext = Depends(get_current_user)) -> Any:
        return VALUE_CHAIN.list_studies()

    @app.get("/api/reach")
    async def api_reach(ctx: RequestContext = Depends(get_current_user)) -> Any:
        return REACH.list_ready()

    @app.get("/api/follow-up")
    async def api_follow_up(ctx: RequestContext = Depends(get_current_user)) -> Any:
        return FOLLOWUP.items()

    @app.get("/api/catalog/search")
    async def api_catalog_search(
        q: str = "", category: str = "", status: str = "", ctx: RequestContext = Depends(get_current_user)
    ) -> Any:
        return CATALOG_SEARCH.search(query=q, category=category, status=status)

    @app.get("/api/network/people")
    async def api_network_people(
        text: str = "",
        status: str = "",
        company_id: str = "",
        role: str = "",
        stale: bool = False,
        ctx: RequestContext = Depends(get_current_user),
    ) -> Any:
        return search_people(
            NETWORK_INDEX_PATH,
            text=text.strip() or None,
            status=status.strip() or None,
            company_id=company_id.strip() or None,
            role=role.strip() or None,
            stale_only=stale,
        )

    @app.get("/api/network/companies")
    async def api_network_companies(
        text: str = "",
        sector: str = "",
        ctx: RequestContext = Depends(get_current_user),
    ) -> Any:
        return search_companies(NETWORK_INDEX_PATH, text=text.strip() or None, sector=sector.strip() or None)

    # ------------------------------------------------------------------
    # POST domain routes (all authenticated).
    # ------------------------------------------------------------------
    @app.post("/api/skills/{skill_id:path}/invoke")
    async def api_invoke_skill(
        skill_id: str,
        payload: dict[str, Any] = Depends(_json_body),
        ctx: RequestContext = Depends(get_current_user),
    ) -> Any:
        return JSONResponse(status_code=200, content=CONTROL.invoke(skill_id.strip("/"), payload))

    @app.post("/api/catalog/harvest")
    async def api_catalog_harvest(
        payload: dict[str, Any] = Depends(_json_body), ctx: RequestContext = Depends(get_current_user)
    ) -> Any:
        persist = payload.get("persist", True)
        if not isinstance(persist, bool):
            raise ControlPlaneError("persist must be a boolean")
        return JSONResponse(status_code=201, content=HARVESTER.stage(payload, persist=persist))

    @app.post("/api/catalog/discover")
    async def api_catalog_discover(
        payload: dict[str, Any] = Depends(_json_body), ctx: RequestContext = Depends(get_current_user)
    ) -> Any:
        persist = payload.get("persist", True)
        if not isinstance(persist, bool):
            raise ControlPlaneError("persist must be a boolean")
        return JSONResponse(status_code=201, content=HARVESTER.discover_public(payload, persist=persist))

    @app.post("/api/nudging/generate")
    async def api_nudging_generate(
        payload: dict[str, Any] = Depends(_json_body), ctx: RequestContext = Depends(get_current_user)
    ) -> Any:
        return NUDGING.generate_request(payload)

    @app.post("/api/value-chain/study")
    async def api_value_chain_study(
        payload: dict[str, Any] = Depends(_json_body), ctx: RequestContext = Depends(get_current_user)
    ) -> Any:
        return VALUE_CHAIN.study(str(payload.get("study_id") or "").strip())

    @app.post("/api/value-chain/prepare")
    async def api_value_chain_prepare(
        payload: dict[str, Any] = Depends(_json_body), ctx: RequestContext = Depends(get_current_user)
    ) -> Any:
        return VALUE_CHAIN.prepare_request(payload)

    @app.post("/api/uc-graph/company")
    async def api_uc_graph_company(
        payload: dict[str, Any] = Depends(_json_body), ctx: RequestContext = Depends(get_current_user)
    ) -> Any:
        return UC_GRAPH.company(str(payload.get("study_id") or "").strip())

    @app.post("/api/uc-graph/sector")
    async def api_uc_graph_sector(
        payload: dict[str, Any] = Depends(_json_body), ctx: RequestContext = Depends(get_current_user)
    ) -> Any:
        return UC_GRAPH.sector(str(payload.get("sector_code") or "").strip())

    @app.post("/api/heritage/company")
    async def api_heritage_company(
        payload: dict[str, Any] = Depends(_json_body), ctx: RequestContext = Depends(get_current_user)
    ) -> Any:
        return HERITAGE.company(str(payload.get("study_id") or "").strip())

    @app.post("/api/heritage/sector")
    async def api_heritage_sector(
        payload: dict[str, Any] = Depends(_json_body), ctx: RequestContext = Depends(get_current_user)
    ) -> Any:
        return HERITAGE.sector(str(payload.get("sector_code") or "").strip())

    @app.post("/api/reach/preview")
    async def api_reach_preview(
        payload: dict[str, Any] = Depends(_json_body), ctx: RequestContext = Depends(get_current_user)
    ) -> Any:
        return REACH.preview(str(payload.get("study_id") or "").strip())

    @app.post("/api/reach/prepare")
    async def api_reach_prepare(
        payload: dict[str, Any] = Depends(_json_body), ctx: RequestContext = Depends(get_current_user)
    ) -> Any:
        return REACH.prepare_request(payload)

    @app.post("/api/workflows/plan")
    async def api_workflows_plan(
        payload: dict[str, Any] = Depends(_json_body), ctx: RequestContext = Depends(get_current_user)
    ) -> Any:
        return WORKFLOWS.plan(payload)

    @app.post("/api/qualification/actions")
    async def api_qualification_actions(
        payload: dict[str, Any] = Depends(_json_body), ctx: RequestContext = Depends(get_current_user)
    ) -> Any:
        action = str(payload.get("action") or "").strip()
        # Decision (flagged in the sprint report): a "force" override of a
        # qualification blocker requires the same technical role as the
        # workspace-level qualification override endpoint (product_owner
        # or admin, per ADR-007 §7); "cancel"/"step_back" only require any
        # authenticated session, since they merely retreat/withdraw a step
        # rather than forcing past a hard gate.
        if action == "force" and not (ctx.is_admin or ctx.role == "product_owner"):
            from fastapi import HTTPException

            raise HTTPException(status_code=403, detail="only a product_owner may force past a qualification blocker")
        entry = BLOCKER_ACTIONS.record(
            study_id=str(payload.get("study_id") or "").strip(),
            step_id=str(payload.get("step_id") or "").strip(),
            action=action,
            actor=ctx.email,
            reason=payload.get("reason"),
            target_step_id=payload.get("target_step_id"),
        )
        return JSONResponse(
            status_code=201,
            content={"entry": entry, "actions": BLOCKER_ACTIONS.list_actions(entry["study_id"])},
        )

    # ------------------------------------------------------------------
    # Static frontend (open, unauthenticated: the SPA shell + login page).
    # ------------------------------------------------------------------
    def _make_static_route(relative_name: str):
        async def _route() -> Response:
            return _static_response(relative_name)

        return _route

    for url_path, relative_name in _STATIC_FILES.items():
        app.add_api_route(url_path, _make_static_route(relative_name), methods=["GET"], include_in_schema=False)

    return app


APP = build_app()


def main() -> None:
    host = os.getenv("AI_DIAGNOSTIC_HOST", "127.0.0.1")
    port = int(os.getenv("AI_DIAGNOSTIC_PORT", "8080"))
    config = AuthConfig.from_env()
    assert_safe_bind(host, config.auth_disabled)
    print(f"AI diagnostic control plane: http://{host}:{port}")
    import uvicorn

    uvicorn.run(APP, host=host, port=port, log_level=os.getenv("AI_DIAGNOSTIC_UVICORN_LOG_LEVEL", "info"))


if __name__ == "__main__":
    main()
