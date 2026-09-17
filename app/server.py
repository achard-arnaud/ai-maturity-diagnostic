from __future__ import annotations

import json
import logging
import mimetypes
import os
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import FileResponse, JSONResponse, Response

from app.authruntime.app import create_app
from app.authruntime.config import AuthConfig, assert_safe_bind
from app.authruntime.db import ControlStore
from app.authruntime.deps import RequestContext, get_current_user, require_role
from app.authruntime.oidc import OIDCClient
from app.account_view import get_account_360
from app.blocker_actions import BlockerActionLog
from app import campaigns
from app.catalog import CatalogHarvester
from app.catalog_search import CatalogSearch
from app.catalog_promotion import (
    get_staged_candidate,
    list_staged_candidates,
    promote_candidate,
    update_offer_sheet,
)
from app.core import ControlPlaneError, RepoControlPlane
from app.dashboard import FollowUpDashboard, UseCaseHeritage
from app.demand import DemandCatalog
from app import kanban
from app import network_index
from app.duplicate_dismissals import dismiss_duplicate_group
from app.execution_context import correlation_scope
from app.network_index import (
    find_potential_duplicates,
    get_company,
    get_person,
    search_companies,
    search_people,
)
from app.network_v1_routes import create_v1_network_router
from app.network_writer import create_company, create_person, reassign_company_workspace
from app.signal_routes import create_v1_signal_router
from app.research_routes import create_v1_research_router
from app.demand_routes import create_v1_demand_router
from app.product_routes import create_v1_product_router
from app.fit_routes import create_v1_fit_router
from app.target_plan_routes import create_v1_target_plan_router
from app.reach_routes import create_v1_reach_router
from app.engagement_routes import create_v1_engagement_router
from app.opportunity_routes import create_v1_opportunity_router
from app.insights_routes import create_v1_insights_router
from app.nudging import UseCaseNudger
from app.qualification import QualificationCockpit
from app.reach import ReachMatchmaker
from app.uc_graph import UseCaseGraph
from app.value_chain import ValueChainCatalog
from app.workflows import WorkflowPlanner
from app.workspace_paths import DEFAULT_WORKSPACE_ID

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
NETWORK_DATA_ROOT = ROOT / "data" / "private"


def _workspace_id_for(ctx: RequestContext) -> str:
    """Concrete workspace_id a Category B domain module (ADR-007 §5) should
    be constructed against for this request. A context with no fixed
    membership (ctx.workspace_id is None -- an admin/global caller) resolves
    to the "default" workspace: WorkspacePaths.root()'s own definition of
    today's legacy mono-root, so this is byte-identical to the hardcoded
    Class(ROOT) singletons below for every caller until a route actually
    switches over to a per-request-scoped instance.
    See docs/governance/P0_LEGACY_WORKSPACE_IDOR_INVENTORY.md §3."""
    return ctx.workspace_id or DEFAULT_WORKSPACE_ID


def _demand_for(ctx: RequestContext) -> DemandCatalog:
    workspace_id = _workspace_id_for(ctx)
    if workspace_id == DEFAULT_WORKSPACE_ID:
        return DEMAND
    return DemandCatalog.for_workspace(workspace_id, repo_root=ROOT)


def _qualification_for(ctx: RequestContext) -> QualificationCockpit:
    workspace_id = _workspace_id_for(ctx)
    if workspace_id == DEFAULT_WORKSPACE_ID:
        return QUALIFICATION
    return QualificationCockpit.for_workspace(workspace_id, repo_root=ROOT)


def _followup_for(ctx: RequestContext) -> FollowUpDashboard:
    workspace_id = _workspace_id_for(ctx)
    if workspace_id == DEFAULT_WORKSPACE_ID:
        return FOLLOWUP
    return FollowUpDashboard.for_workspace(workspace_id, repo_root=ROOT)


def _heritage_for(ctx: RequestContext) -> UseCaseHeritage:
    workspace_id = _workspace_id_for(ctx)
    if workspace_id == DEFAULT_WORKSPACE_ID:
        return HERITAGE
    return UseCaseHeritage.for_workspace(workspace_id, repo_root=ROOT)

# Routes open to unauthenticated callers: the health probe (used by
# uptime/ops checks that have no session) and the static SPA shell/login
# page, whose own client-side JS is what performs the auth check (via
# /api/auth/me) and redirects to /login.html on a 401. Gating index.html
# itself would make that redirect impossible to reach. Every /api/* data
# route below is authenticated by default per ADR-007 §7 sprint scope.
_STATIC_FILES = {
    "/": "index.html",
    "/app.js": "app.js",
    "/router.js": "router.js",
    "/gtm-spaces.js": "gtm-spaces.js",
    "/styles.css": "styles.css",
    "/login.html": "login.html",
    "/vendor/mermaid.min.js": "vendor/mermaid.min.js",
}


def _effective_workspace_id(ctx: RequestContext, requested: str | None) -> str | None:
    """Resolve the workspace a legacy `/api/*` route should actually query.

    These routes predate the /api/v1/workspaces/{workspace_id}/... path
    convention and instead take an optional workspace_id query/body field.
    Never trust that field at face value: default to the caller's own
    membership, and only honor an explicit different value if the caller
    can access it (always true for admins) -- mirrors
    require_workspace_access()'s invariant for a route shape that doesn't
    put workspace_id in the path. See
    docs/governance/P0_LEGACY_WORKSPACE_IDOR_INVENTORY.md.

    Raises 404 (never 403) on a denied explicit request, matching ADR-007
    §1's "don't disclose another workspace's data exists" rule already
    used by every v1 route.
    """
    if not requested:
        return ctx.workspace_id
    if not ctx.can_access_workspace(requested):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "not found")
    return requested


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


_REQUEST_LOG = logging.getLogger("app.request")
_REQUEST_LOG.propagate = False
if not _REQUEST_LOG.handlers:
    _request_log_handler = logging.StreamHandler(sys.stdout)
    _request_log_handler.setFormatter(logging.Formatter("%(message)s"))
    _REQUEST_LOG.addHandler(_request_log_handler)
    _REQUEST_LOG.setLevel(logging.INFO)


async def _log_requests(request: Request, call_next):
    """Structured JSON access log: one line per request, no sensitive data.

    Per ADR-007's rule against logging sensitive data, this deliberately
    never logs the request body, cookies, Authorization header, or query
    string -- only method, path, status, duration, and a request id.
    """

    request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
    started = time.monotonic()
    with correlation_scope(request_id):
        response = await call_next(request)
    duration_ms = round((time.monotonic() - started) * 1000, 2)
    response.headers["X-Request-ID"] = request_id
    _REQUEST_LOG.info(
        json.dumps(
            {
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "duration_ms": duration_ms,
            }
        )
    )
    return response


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

    app.middleware("http")(_log_requests)
    app.include_router(create_v1_network_router(ROOT))
    app.include_router(create_v1_signal_router(ROOT))
    app.include_router(create_v1_research_router(ROOT))
    app.include_router(create_v1_demand_router(ROOT))
    app.include_router(create_v1_product_router(ROOT))
    app.include_router(create_v1_fit_router(ROOT))
    app.include_router(create_v1_target_plan_router(ROOT))
    app.include_router(create_v1_reach_router(ROOT))
    app.include_router(create_v1_engagement_router(ROOT))
    app.include_router(create_v1_opportunity_router(ROOT))
    app.include_router(create_v1_insights_router(ROOT))

    @app.get("/w/{workspace_slug}/{space}", include_in_schema=False)
    @app.get("/w/{workspace_slug}/{space}/{object_id}", include_in_schema=False)
    async def gtm_deep_link(workspace_slug: str, space: str, object_id: str | None = None) -> Response:
        return _static_response("index.html")

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
        logging.getLogger(__name__).exception("unhandled exception while serving %s", request.url.path)
        return JSONResponse(status_code=500, content={"status": "error", "error": "internal server error"})

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

    @app.get("/api/blocker-actions")
    async def list_blocker_actions_filtered(
        study_id: str = "",
        company_id: str = "",
        action: str = "",
        step_id: str = "",
        since: str = "",
        until: str = "",
        ctx: RequestContext = Depends(get_current_user),
    ) -> Any:
        resolved_study_id = study_id.strip()
        company_id = company_id.strip()
        if company_id and not resolved_study_id:
            for study_row in _qualification_for(ctx).list_studies():
                if study_row.get("company_id") == company_id:
                    resolved_study_id = str(study_row.get("study_id") or "")
                    break
            else:
                return []
        return BLOCKER_ACTIONS.list_actions(
            resolved_study_id,
            action=action.strip() or None,
            step_id=step_id.strip() or None,
            since=since.strip() or None,
            until=until.strip() or None,
        )

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
        return _demand_for(ctx).snapshot()

    @app.get("/api/demand/inventories")
    async def api_demand_inventories(ctx: RequestContext = Depends(get_current_user)) -> Any:
        return _demand_for(ctx).inventories()

    # Demand-profile intake (M2): writes a schema-conformant
    # 05_enterprise_demand_profile.yaml from the minimum a human can type,
    # closing the gap where DemandCatalog had no write path at all. See
    # app/demand.py's create_demand_profile docstring for the
    # study-directory collision rules.
    @app.post("/api/demand/intake")
    async def api_demand_intake(
        payload: dict[str, Any] = Depends(_json_body), ctx: RequestContext = Depends(get_current_user)
    ) -> Any:
        result = _demand_for(ctx).create_demand_profile(
            company=str(payload.get("company") or ""),
            problem_statement=str(payload.get("problem_statement") or ""),
            company_id=payload.get("company_id"),
            sector_code=payload.get("sector_code"),
            confidence=str(payload.get("confidence") or "low"),
            study_id=payload.get("study_id"),
        )
        return JSONResponse(status_code=201, content=result)

    @app.get("/api/qualification")
    async def api_qualification(ctx: RequestContext = Depends(get_current_user)) -> Any:
        return _qualification_for(ctx).list_studies()

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
        return _followup_for(ctx).items()

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
        workspace_id: str = "",
        ctx: RequestContext = Depends(get_current_user),
    ) -> Any:
        return search_people(
            NETWORK_INDEX_PATH,
            text=text.strip() or None,
            status=status.strip() or None,
            company_id=company_id.strip() or None,
            role=role.strip() or None,
            stale_only=stale,
            workspace_id=_effective_workspace_id(ctx, workspace_id.strip() or None),
        )

    @app.get("/api/accounts/{company_id}/360")
    async def api_account_360(
        company_id: str, ctx: RequestContext = Depends(get_current_user)
    ) -> Any:
        result = get_account_360(ROOT, company_id.strip(), index_path=NETWORK_INDEX_PATH)
        if result is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "unknown company_id")
        # Same generic-404 IDOR rule as /api/v1/...: a company from a
        # workspace the caller can't access is indistinguishable from an
        # unknown one, per ADR-007 §1 and docs/governance/
        # P0_LEGACY_WORKSPACE_IDOR_INVENTORY.md.
        if not ctx.can_access_workspace(result["company"].get("workspace_id")):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "unknown company_id")
        return result

    @app.get("/api/network/companies")
    async def api_network_companies(
        text: str = "",
        sector: str = "",
        workspace_id: str = "",
        ctx: RequestContext = Depends(get_current_user),
    ) -> Any:
        return search_companies(
            NETWORK_INDEX_PATH,
            text=text.strip() or None,
            sector=sector.strip() or None,
            workspace_id=_effective_workspace_id(ctx, workspace_id.strip() or None),
        )

    @app.get("/api/network/duplicates")
    async def api_network_duplicates(
        include_dismissed: bool = False, ctx: RequestContext = Depends(get_current_user)
    ) -> Any:
        return find_potential_duplicates(
            NETWORK_INDEX_PATH,
            root=ROOT,
            include_dismissed=include_dismissed,
            workspace_id=_effective_workspace_id(ctx, None),
        )

    @app.post("/api/network/duplicates/dismiss")
    async def api_network_duplicates_dismiss(
        payload: dict[str, Any] = Depends(_json_body), ctx: RequestContext = Depends(get_current_user)
    ) -> Any:
        person_ids = payload.get("person_ids") or []
        # Every named person must resolve, via their seed company, to a
        # workspace this caller can access -- otherwise this write would let
        # a caller confirm cross-workspace person_ids exist and mutate
        # dismissal state for a workspace they cannot see (ADR-007 SS1).
        for person_id in person_ids:
            person = get_person(NETWORK_INDEX_PATH, str(person_id))
            if person is None:
                continue
            company = get_company(NETWORK_INDEX_PATH, str(person.get("seed_company_id") or ""))
            company_workspace = company.get("workspace_id") if company else None
            if not ctx.can_access_workspace(company_workspace):
                raise HTTPException(status.HTTP_404_NOT_FOUND, "not found")
        record = dismiss_duplicate_group(ROOT, person_ids, actor=ctx.email, reason=payload.get("reason"))
        return JSONResponse(status_code=200, content=record)

    # ------------------------------------------------------------------
    # Admin-only network index rebuild trigger (manual/on-demand; the
    # search routes above read a derived SQLite index that otherwise only
    # scripts/rebuild_network_index.py can (re)build from a shell).
    # ------------------------------------------------------------------
    @app.post("/admin/network/rebuild-index")
    async def admin_network_rebuild_index(ctx: RequestContext = Depends(require_role("admin"))) -> Any:
        return network_index.rebuild(NETWORK_INDEX_PATH.parent, NETWORK_INDEX_PATH)

    # Account reassignment (CRM-audit gap #4): moves a company between
    # workspaces by updating its workspace_id in companies.jsonl. Never
    # touches the derived SQLite index -- an admin must rebuild it
    # afterwards (POST /admin/network/rebuild-index) for search results
    # to reflect the new workspace_id.
    @app.post("/admin/network/companies/{company_id}/reassign")
    async def admin_reassign_company(
        company_id: str,
        payload: dict[str, Any] = Depends(_json_body),
        ctx: RequestContext = Depends(require_role("admin")),
    ) -> Any:
        new_workspace_id = str(payload.get("workspace_id") or "").strip()
        updated = reassign_company_workspace(NETWORK_INDEX_PATH.parent, company_id.strip(), new_workspace_id)
        return {"company": updated, "index_rebuild_required": True}

    @app.get("/api/kanban/board")
    async def api_kanban_board(ctx: RequestContext = Depends(get_current_user)) -> Any:
        return kanban.build_board(ROOT)

    @app.get("/api/campaigns")
    async def api_campaigns_list(ctx: RequestContext = Depends(get_current_user)) -> Any:
        return campaigns.list_campaigns(ROOT)

    # Minimal, thin route exposing app.catalog_promotion.list_staged_candidates
    # (S6/S7 landed the promotion/edit endpoints with no way to list what can
    # be promoted). Reads only -- never touches product_catalog/*.yaml.
    @app.get("/api/catalog/candidates")
    async def api_catalog_candidates(
        text: str = "",
        promotion_status: str = "",
        shelf_id: str = "",
        company: str = "",
        ctx: RequestContext = Depends(get_current_user),
    ) -> Any:
        return list_staged_candidates(
            CONTROL.root,
            text=text.strip() or None,
            promotion_status=promotion_status.strip() or None,
            shelf_id=shelf_id.strip() or None,
            company=company.strip() or None,
        )

    @app.get("/api/catalog/candidates/{candidate_id:path}")
    async def api_catalog_candidate_detail(
        candidate_id: str, ctx: RequestContext = Depends(get_current_user)
    ) -> Any:
        return get_staged_candidate(CONTROL.root, candidate_id)

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

    @app.post("/api/nudges/{nudge_id}/accept")
    async def api_nudges_accept(
        nudge_id: str, payload: dict[str, Any] = Depends(_json_body), ctx: RequestContext = Depends(get_current_user)
    ) -> Any:
        record = NUDGING.accept_nudge(
            str(payload.get("study_id") or "").strip(), nudge_id.strip(), actor=ctx.email
        )
        return JSONResponse(status_code=200, content=record)

    @app.post("/api/nudges/{nudge_id}/reject")
    async def api_nudges_reject(
        nudge_id: str, payload: dict[str, Any] = Depends(_json_body), ctx: RequestContext = Depends(get_current_user)
    ) -> Any:
        record = NUDGING.reject_nudge(
            str(payload.get("study_id") or "").strip(),
            nudge_id.strip(),
            actor=ctx.email,
            reason=payload.get("reason"),
        )
        return JSONResponse(status_code=200, content=record)

    @app.post("/api/nudges/{nudge_id}/ack-falsifier")
    async def api_nudges_ack_falsifier(
        nudge_id: str, payload: dict[str, Any] = Depends(_json_body), ctx: RequestContext = Depends(get_current_user)
    ) -> Any:
        record = NUDGING.acknowledge_falsifier(
            str(payload.get("study_id") or "").strip(), nudge_id.strip(), actor=ctx.email
        )
        return JSONResponse(status_code=200, content=record)

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
        return _heritage_for(ctx).company(str(payload.get("study_id") or "").strip())

    @app.post("/api/heritage/sector")
    async def api_heritage_sector(
        payload: dict[str, Any] = Depends(_json_body), ctx: RequestContext = Depends(get_current_user)
    ) -> Any:
        return _heritage_for(ctx).sector(str(payload.get("sector_code") or "").strip())

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
    # Direct network contact/company creation (closes the journey B/C
    # "structured form, not skill-invoke facade" gap). Any authenticated
    # user may create -- unlike scripts/import_contacts.py this is a
    # single-record, human-typed entry, not a bulk data import, so there is
    # no elevated-role reason to restrict it further. M1 fix: immediately
    # rebuilds data/private/network/network_index.sqlite (the same
    # synchronous call POST /admin/network/rebuild-index makes) right after
    # the write succeeds, so the new record is searchable without a
    # separate admin call -- see docs/red-team-side-story/
    # trigger-journey-audit.md's M1 section.
    # ------------------------------------------------------------------
    @app.post("/api/network/people")
    async def api_network_create_person(
        payload: dict[str, Any] = Depends(_json_body), ctx: RequestContext = Depends(get_current_user)
    ) -> Any:
        seed_company_id = str(payload.get("seed_company_id") or "")
        # A person's workspace is implicit via their seed company (create_person
        # takes no workspace_id of its own -- see app/network_writer.py's
        # docstring); an unknown company_id still 400s below via create_person's
        # own ControlPlaneError, so only a *known-but-foreign* company is
        # rejected here, and with a 404 to match the "don't disclose another
        # workspace's data exists" rule used by every other Category A route.
        existing_company = get_company(NETWORK_INDEX_PATH, seed_company_id)
        if existing_company is not None and not ctx.can_access_workspace(
            existing_company.get("workspace_id")
        ):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "unknown seed_company_id")
        person = create_person(
            NETWORK_DATA_ROOT,
            display_name=str(payload.get("display_name") or ""),
            seed_company_id=seed_company_id,
            role_hypotheses=payload.get("role_hypotheses"),
            source=str(payload.get("source") or "manual_entry"),
        )
        network_index.rebuild(NETWORK_INDEX_PATH.parent, NETWORK_INDEX_PATH)
        return JSONResponse(status_code=201, content=person)

    @app.post("/api/network/companies")
    async def api_network_create_company(
        payload: dict[str, Any] = Depends(_json_body), ctx: RequestContext = Depends(get_current_user)
    ) -> Any:
        requested_workspace_id = payload.get("workspace_id")
        workspace_id = _effective_workspace_id(
            ctx, str(requested_workspace_id).strip() if requested_workspace_id else None
        )
        company = create_company(
            NETWORK_DATA_ROOT,
            canonical_name=str(payload.get("canonical_name") or ""),
            sector_code=payload.get("sector_code"),
            workspace_id=workspace_id,
        )
        network_index.rebuild(NETWORK_INDEX_PATH.parent, NETWORK_INDEX_PATH)
        return JSONResponse(status_code=201, content=company)

    # ------------------------------------------------------------------
    # Catalog candidate promotion + product_owner offer-sheet edit
    # (closes journey A's promotion/edit gaps). Promotion stays open to any
    # authenticated user (it never bypasses the human-review contract --
    # promoted offers land as status "draft" with honest unknowns, per
    # ADR-004; there is no stronger claim being made that would need
    # role-gating). Editing an existing offer sheet is product_owner/admin
    # scoped per the sprint's Part 3 RBAC plan.
    # ------------------------------------------------------------------
    @app.post("/api/catalog/candidates/{candidate_id:path}/promote")
    async def api_catalog_promote_candidate(
        candidate_id: str,
        payload: dict[str, Any] = Depends(_json_body),
        ctx: RequestContext = Depends(get_current_user),
    ) -> Any:
        offer = promote_candidate(
            CONTROL.root,
            candidate_id,
            offer_id=str(payload.get("offer_id") or ""),
            workspace_id=payload.get("workspace_id"),
        )
        return JSONResponse(status_code=201, content=offer)

    @app.patch("/api/catalog/offers/{offer_id}")
    async def api_catalog_update_offer(
        offer_id: str,
        payload: dict[str, Any] = Depends(_json_body),
        ctx: RequestContext = Depends(require_role("product_owner", "admin")),
    ) -> Any:
        updates = payload.get("updates")
        if not isinstance(updates, dict):
            raise ControlPlaneError("updates must be an object")
        offer = update_offer_sheet(
            CONTROL.root,
            offer_id,
            updates,
            workspace_id=payload.get("workspace_id") or ctx.workspace_id,
        )
        return JSONResponse(status_code=200, content=offer)

    @app.post("/api/campaigns/prospecting")
    async def api_campaigns_prospecting(
        payload: dict[str, Any] = Depends(_json_body), ctx: RequestContext = Depends(get_current_user)
    ) -> Any:
        criteria = dict(payload.get("criteria") or {})
        # launch_prospecting_campaign forwards criteria unchecked into
        # search_people/search_companies (app/campaigns.py's _CRITERIA_FIELDS
        # includes workspace_id) -- sanitize it the same way every other
        # Category A route resolves a client-supplied workspace_id.
        raw_workspace_id = criteria.get("workspace_id")
        criteria["workspace_id"] = _effective_workspace_id(
            ctx, str(raw_workspace_id).strip() if raw_workspace_id else None
        )
        record = campaigns.launch_prospecting_campaign(
            ROOT,
            name=str(payload.get("name") or "").strip(),
            criteria=criteria,
            actor=ctx.email,
        )
        return JSONResponse(status_code=201, content=record)

    @app.post("/api/campaigns/{campaign_id}/mark-sent")
    async def api_campaigns_mark_sent(
        campaign_id: str, ctx: RequestContext = Depends(get_current_user)
    ) -> Any:
        record = campaigns.mark_campaign_sent(ROOT, campaign_id.strip(), actor=ctx.email)
        return JSONResponse(status_code=200, content=record)

    @app.post("/api/campaigns/cross-sell")
    async def api_campaigns_cross_sell(
        payload: dict[str, Any] = Depends(_json_body), ctx: RequestContext = Depends(get_current_user)
    ) -> Any:
        result = campaigns.prepare_cross_sell(
            ROOT, study_id=str(payload.get("study_id") or "").strip(), actor=ctx.email
        )
        return JSONResponse(status_code=201, content=result)

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
