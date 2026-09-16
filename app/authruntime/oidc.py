"""Google OIDC client wrapper (Authlib), the single configured provider (ADR-007 §2).

Kept as a thin, mockable seam: `/auth/callback` tests stub `GoogleOIDCClient`
instead of exercising a real Google redirect, since that needs live
GOOGLE_CLIENT_ID/GOOGLE_CLIENT_SECRET credentials.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from authlib.integrations.starlette_client import OAuth
from starlette.requests import Request

GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"


@dataclass(frozen=True)
class OIDCUserInfo:
    email: str
    name: str | None
    sub: str


class OIDCClient(Protocol):
    async def authorize_redirect(self, request: Request, redirect_uri: str) -> Any: ...

    async def authorize_userinfo(self, request: Request) -> OIDCUserInfo: ...


class GoogleOIDCClient:
    """Real Authlib-backed client. Requires GOOGLE_CLIENT_ID/SECRET at runtime."""

    def __init__(self, client_id: str, client_secret: str, session_secret: str) -> None:
        self._oauth = OAuth()
        self._oauth.register(
            name="google",
            client_id=client_id,
            client_secret=client_secret,
            server_metadata_url=GOOGLE_DISCOVERY_URL,
            client_kwargs={"scope": "openid email profile"},
        )

    async def authorize_redirect(self, request: Request, redirect_uri: str) -> Any:
        return await self._oauth.google.authorize_redirect(request, redirect_uri)

    async def authorize_userinfo(self, request: Request) -> OIDCUserInfo:
        token = await self._oauth.google.authorize_access_token(request)
        userinfo = token.get("userinfo") or {}
        email = userinfo.get("email")
        if not email:
            raise ValueError("OIDC provider did not return an email claim")
        return OIDCUserInfo(email=email, name=userinfo.get("name"), sub=userinfo.get("sub", email))
