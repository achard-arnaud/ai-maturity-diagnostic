"""FastAPI ASGI adapter for ADR-007 (replaces only the HTTP adapter, §6).

Existing plain-Python business modules are never imported for their
FastAPI/Starlette/Authlib side here beyond what this file needs; the
override endpoint calls into app.qualification only to read blocker
context, never to mutate the hard-gate logic itself.
"""

from __future__ import annotations

import html
import os
import uuid
from pathlib import Path
from typing import Any, Callable

from fastapi import Depends, FastAPI, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

from app.authruntime.config import AuthConfig
from app.authruntime.db import ControlStore
from app.authruntime.deps import RequestContext, get_current_user, get_store, require_role, require_workspace_access
from app.authruntime.oidc import GoogleOIDCClient, OIDCClient, OIDCUserInfo

ROOT = Path(__file__).resolve().parents[2]


def create_app(
    *,
    control_store: ControlStore | None = None,
    oidc_client: OIDCClient | None = None,
    config: AuthConfig | None = None,
    session_secret: str | None = None,
) -> FastAPI:
    config = config or AuthConfig.from_env()
    control_store = control_store or ControlStore(ROOT / "data" / "control" / "control.sqlite3")
    session_secret = session_secret or os.environ.get("AI_DIAGNOSTIC_SESSION_SECRET") or uuid.uuid4().hex

    app = FastAPI(title="AI Maturity Diagnostic — Auth Runtime")
    app.state.control_store = control_store
    app.state.session_cookie_name = config.session_cookie_name
    app.state.auth_config = config
    # Transient OIDC state/nonce only — short-lived, one-time-use per
    # ADR-007 §2/§3. This is never used to carry membership or provider
    # tokens to the browser; that lives solely in the opaque session
    # cookie issued after /auth/callback succeeds.
    app.add_middleware(SessionMiddleware, secret_key=session_secret, session_cookie="aimd_oauth_state")

    if oidc_client is None and config.google_client_id and config.google_client_secret:
        oidc_client = GoogleOIDCClient(config.google_client_id, config.google_client_secret, session_secret)
    app.state.oidc_client = oidc_client

    def _oidc(request: Request) -> OIDCClient:
        client = getattr(request.app.state, "oidc_client", None)
        if client is None:
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "OIDC provider not configured")
        return client

    # ------------------------------------------------------------------
    # Auth
    # ------------------------------------------------------------------
    @app.get("/auth/login")
    async def login(request: Request, client: OIDCClient = Depends(_oidc)):
        redirect_uri = str(request.url_for("callback"))
        return await client.authorize_redirect(request, redirect_uri)

    @app.get("/auth/callback", name="callback")
    async def callback(request: Request, client: OIDCClient = Depends(_oidc)):
        userinfo: OIDCUserInfo = await client.authorize_userinfo(request)
        user = control_store.get_or_create_user(userinfo.email, userinfo.name)
        token = control_store.create_session(user["id"], ttl_hours=config.session_ttl_hours)
        control_store.record_audit(actor=user["email"], action="login", target=None, reason=None)
        response = RedirectResponse(url="/admin/workspaces", status_code=status.HTTP_303_SEE_OTHER)
        response.set_cookie(
            config.session_cookie_name,
            token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=config.session_ttl_hours * 3600,
        )
        return response

    @app.post("/auth/logout")
    async def logout(request: Request, store: ControlStore = Depends(get_store)):
        token = request.cookies.get(config.session_cookie_name)
        if token:
            store.revoke_session(token)
        response = RedirectResponse(url="/auth/login", status_code=status.HTTP_303_SEE_OTHER)
        response.delete_cookie(config.session_cookie_name)
        return response

    # ------------------------------------------------------------------
    # Admin
    # ------------------------------------------------------------------
    @app.get("/admin/workspaces", response_class=HTMLResponse)
    async def admin_page(request: Request, ctx: RequestContext = Depends(require_role("admin")), store: ControlStore = Depends(get_store)):
        return HTMLResponse(_render_admin_page(store))

    @app.post("/admin/workspaces")
    async def create_workspace(
        request: Request,
        workspace_id: str = Form(...),
        name: str = Form(...),
        ctx: RequestContext = Depends(require_role("admin")),
        store: ControlStore = Depends(get_store),
    ):
        if store.get_workspace(workspace_id) is not None:
            raise HTTPException(status.HTTP_409_CONFLICT, "workspace id already exists")
        store.create_workspace(workspace_id, name)
        store.record_audit(actor=ctx.email, action="create_workspace", target=workspace_id, reason=None)
        return RedirectResponse(url="/admin/workspaces", status_code=status.HTTP_303_SEE_OTHER)

    @app.post("/admin/memberships")
    async def set_membership(
        request: Request,
        user_id: str = Form(...),
        workspace_id: str = Form(...),
        role: str = Form(...),
        ctx: RequestContext = Depends(require_role("admin")),
        store: ControlStore = Depends(get_store),
    ):
        if store.get_workspace(workspace_id) is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "workspace does not exist")
        if store.get_user(user_id) is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "user does not exist")
        try:
            store.set_membership(user_id, workspace_id, role)
        except ValueError as exc:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
        store.record_audit(
            actor=ctx.email, action="set_membership", target=f"{user_id}->{workspace_id}:{role}", reason=None
        )
        return RedirectResponse(url="/admin/workspaces", status_code=status.HTTP_303_SEE_OTHER)

    @app.get("/admin/memberships", response_class=HTMLResponse)
    async def admin_memberships(
        request: Request, ctx: RequestContext = Depends(require_role("admin")), store: ControlStore = Depends(get_store)
    ):
        users = store.list_users()
        return HTMLResponse(_render_memberships_page(users))

    @app.get("/admin/users", response_class=HTMLResponse)
    async def admin_users(
        request: Request,
        text: str | None = None,
        role: str | None = None,
        workspace_id: str | None = None,
        ctx: RequestContext = Depends(require_role("admin")),
        store: ControlStore = Depends(get_store),
    ):
        users = store.search_users(text=text or None, role=role or None, workspace_id=workspace_id or None)
        return HTMLResponse(_render_users_page(users, text=text, role=role, workspace_id=workspace_id))

    @app.get("/admin/audit", response_class=HTMLResponse)
    async def admin_audit(request: Request, ctx: RequestContext = Depends(require_role("admin")), store: ControlStore = Depends(get_store)):
        return HTMLResponse(_render_audit_page(store))

    @app.get("/admin/overrides", response_class=HTMLResponse)
    async def admin_overrides(
        request: Request,
        workspace_id: str | None = None,
        ctx: RequestContext = Depends(require_role("admin")),
        store: ControlStore = Depends(get_store),
    ):
        overrides = store.list_overrides(workspace_id=workspace_id or None)
        return HTMLResponse(_render_overrides_page(overrides, workspace_id=workspace_id))

    # ------------------------------------------------------------------
    # Qualification override (product_owner scoped mutation)
    # ------------------------------------------------------------------
    @app.post("/api/workspaces/{workspace_id}/qualification/{blocker_id}/override")
    async def override_blocker(
        workspace_id: str,
        blocker_id: str,
        reason: str = Form(...),
        ctx: RequestContext = Depends(require_workspace_access()),
        store: ControlStore = Depends(get_store),
    ):
        if not ctx.is_admin and ctx.role != "product_owner":
            raise HTTPException(status.HTTP_403_FORBIDDEN, "only a product_owner may override a qualification blocker")
        reason = reason.strip()
        if not reason:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "a reason is mandatory for a qualification override")
        override_id = store.record_override(workspace_id, blocker_id, ctx.email, reason)
        # NOTE: this only records a tracked human override on top of the
        # existing hard gate; it never mutates app.qualification's blocker
        # computation or the underlying artifacts. See ADR-007 §7.
        store.record_audit(
            actor=ctx.email,
            action="qualification_override",
            target=f"{workspace_id}:{blocker_id}",
            reason=reason,
        )
        return {"override_id": override_id, "workspace_id": workspace_id, "blocker_id": blocker_id, "reason": reason}

    return app


def _render_admin_page(store: ControlStore) -> str:
    workspaces = store.list_workspaces()
    users = store.list_users()

    def esc(value: Any) -> str:
        return html.escape(str(value)) if value is not None else ""

    ws_rows = "".join(
        f"<tr><td>{esc(w['id'])}</td><td>{esc(w['name'])}</td><td>{esc(w['created_at'])}</td></tr>"
        for w in workspaces
    )
    user_rows = "".join(
        f"<tr><td>{esc(u['id'])}</td><td>{esc(u['email'])}</td>"
        f"<td>{'admin' if u['is_admin'] else esc(u['role'] or '(none)')}</td>"
        f"<td>{esc(u['workspace_id'] or '')}</td></tr>"
        for u in users
    )
    return f"""<!doctype html>
<html><head><title>Admin — Workspaces &amp; Roles</title></head>
<body>
<h1>Workspaces</h1>
<table border="1"><tr><th>id</th><th>name</th><th>created_at</th></tr>{ws_rows}</table>
<h2>Create workspace</h2>
<form method="post" action="/admin/workspaces">
<input name="workspace_id" placeholder="workspace id" required>
<input name="name" placeholder="name" required>
<button type="submit">Create</button>
</form>
<h1>Users &amp; memberships</h1>
<table border="1"><tr><th>id</th><th>email</th><th>role</th><th>workspace_id</th></tr>{user_rows}</table>
<h2>Set membership</h2>
<form method="post" action="/admin/memberships">
<input name="user_id" placeholder="user id" required>
<input name="workspace_id" placeholder="workspace id" required>
<select name="role"><option value="product_owner">product_owner</option><option value="standard_user">standard_user</option></select>
<button type="submit">Save</button>
</form>
<p><a href="/admin/audit">Audit log</a></p>
</body></html>"""


def _render_memberships_page(users: list[Any]) -> str:
    def esc(value: Any) -> str:
        return html.escape(str(value)) if value is not None else ""

    members = [u for u in users if u["workspace_id"] is not None]
    rows = "".join(
        f"<tr><td>{esc(u['email'])}</td><td>{esc(u['workspace_id'])}</td><td>{esc(u['role'])}</td></tr>"
        for u in members
    )
    return f"""<!doctype html>
<html><head><title>Admin — Memberships</title></head>
<body>
<h1>Memberships</h1>
<table border="1"><tr><th>email</th><th>workspace_id</th><th>role</th></tr>{rows}</table>
<h2>Set membership</h2>
<form method="post" action="/admin/memberships">
<input name="user_id" placeholder="user id" required>
<input name="workspace_id" placeholder="workspace id" required>
<select name="role"><option value="product_owner">product_owner</option><option value="standard_user">standard_user</option></select>
<button type="submit">Save</button>
</form>
<p><a href="/admin/workspaces">Back</a></p>
</body></html>"""


def _render_users_page(users: list[Any], *, text: str | None, role: str | None, workspace_id: str | None) -> str:
    def esc(value: Any) -> str:
        return html.escape(str(value)) if value is not None else ""

    rows = "".join(
        f"<tr><td>{esc(u['email'])}</td>"
        f"<td>{'admin' if u['is_admin'] else esc(u['role'] or '(none)')}</td>"
        f"<td>{esc(u['workspace_id'] or '')}</td>"
        f"<td>{'yes' if u['is_admin'] else 'no'}</td></tr>"
        for u in users
    )
    return f"""<!doctype html>
<html><head><title>Admin — Users</title></head>
<body>
<h1>Users</h1>
<form method="get" action="/admin/users">
<input name="text" placeholder="email contains" value="{esc(text)}">
<input name="role" placeholder="role (admin/product_owner/standard_user)" value="{esc(role)}">
<input name="workspace_id" placeholder="workspace id" value="{esc(workspace_id)}">
<button type="submit">Search</button>
</form>
<table border="1"><tr><th>email</th><th>role</th><th>workspace_id</th><th>is_admin</th></tr>{rows}</table>
<p><a href="/admin/workspaces">Back</a></p>
</body></html>"""


def _render_overrides_page(overrides: list[Any], *, workspace_id: str | None) -> str:
    """Centralized approval inbox (CRM-audit gap #2): lists recorded
    qualification-blocker overrides from app.authruntime.db's `overrides`
    table. Every row here is a human decision already recorded -- there
    is no resolved/unresolved state in the schema (see
    ControlStore.list_overrides's docstring finding); this page therefore
    reads as a log of overrides, not a queue of pending approvals."""

    def esc(value: Any) -> str:
        return html.escape(str(value)) if value is not None else ""

    rows = "".join(
        f"<tr><td>{esc(o['created_at'])}</td><td>{esc(o['workspace_id'])}</td>"
        f"<td>{esc(o['blocker_id'])}</td><td>{esc(o['actor'])}</td><td>{esc(o['reason'])}</td></tr>"
        for o in overrides
    )
    return f"""<!doctype html>
<html><head><title>Admin — Overrides</title></head>
<body>
<h1>Overrides</h1>
<p>Every recorded qualification-blocker override, most recent first. This table has no resolved/unresolved
state today: an override is itself the record of a human decision already made.</p>
<form method="get" action="/admin/overrides">
<input name="workspace_id" placeholder="workspace id" value="{esc(workspace_id)}">
<button type="submit">Filter</button>
</form>
<table border="1"><tr><th>created_at</th><th>workspace_id</th><th>blocker_id</th><th>actor</th><th>reason</th></tr>{rows}</table>
<p><a href="/admin/workspaces">Back</a></p>
</body></html>"""


def _render_audit_page(store: ControlStore) -> str:
    events = store.list_audit()

    def esc(value: Any) -> str:
        return html.escape(str(value)) if value is not None else ""

    rows = "".join(
        f"<tr><td>{esc(e['timestamp'])}</td><td>{esc(e['actor'])}</td><td>{esc(e['action'])}</td>"
        f"<td>{esc(e['target'])}</td><td>{esc(e['reason'])}</td></tr>"
        for e in events
    )
    return f"""<!doctype html>
<html><head><title>Audit log</title></head>
<body>
<h1>Audit log</h1>
<table border="1"><tr><th>timestamp</th><th>actor</th><th>action</th><th>target</th><th>reason</th></tr>{rows}</table>
<p><a href="/admin/workspaces">Back</a></p>
</body></html>"""
