"""FastAPI dependencies enforcing RBAC (ADR-007 §7).

RBAC here only ever gates a *technical* operation. It never turns an
unproven claim into proof, changes evidence confidence, or overrides a
product-fit blocker — see app.qualification.QualificationCockpit, which
this layer never mutates or reimplements.
"""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, HTTPException, Request, status

from app.authruntime.db import ControlStore


@dataclass(frozen=True)
class RequestContext:
    """Immutable, verified identity+membership context for one request."""

    user_id: str
    email: str
    is_admin: bool
    role: str | None  # 'product_owner' | 'standard_user' | None (admin has no membership row)
    workspace_id: str | None  # None only for an admin with no personal membership

    def can_access_workspace(self, workspace_id: str) -> bool:
        if self.is_admin:
            return True
        return self.workspace_id == workspace_id


def get_store(request: Request) -> ControlStore:
    store = getattr(request.app.state, "control_store", None)
    if store is None:
        raise RuntimeError("control store not configured on FastAPI app state")
    return store


def get_current_user(request: Request, store: ControlStore = Depends(get_store)) -> RequestContext:
    cookie_name = getattr(request.app.state, "session_cookie_name", "aimd_session")
    token = request.cookies.get(cookie_name)
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "not authenticated")
    row = store.get_session_user(token)
    if row is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "session invalid or expired")
    membership = store.get_membership(row["user_id_col"])
    return RequestContext(
        user_id=row["user_id_col"],
        email=row["email"],
        is_admin=bool(row["is_admin"]),
        role=membership["role"] if membership else None,
        workspace_id=membership["workspace_id"] if membership else None,
    )


def require_role(*roles: str):
    """Dependency factory: allow only the given technical roles ('admin' always allowed)."""

    def _dependency(ctx: RequestContext = Depends(get_current_user)) -> RequestContext:
        if ctx.is_admin:
            return ctx
        if ctx.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "role does not permit this operation")
        return ctx

    return _dependency


def require_workspace_access(workspace_id_param: str = "workspace_id"):
    """Dependency factory: the path param workspace_id must match membership.

    Per ADR-007 §1, an unauthorized cross-workspace object lookup resolves
    as 404 (not 403) so as not to disclose that another workspace owns the
    object.
    """

    def _dependency(request: Request, ctx: RequestContext = Depends(get_current_user)) -> RequestContext:
        workspace_id = request.path_params.get(workspace_id_param)
        if workspace_id is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "missing workspace_id")
        if not ctx.can_access_workspace(workspace_id):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "not found")
        return ctx

    return _dependency
