"""Runtime configuration and the local-dev safety guard (ADR-007 §2, invariants).

Local development may run with auth disabled, but ONLY while bound to a
loopback interface. This module provides the guard so any future launcher
cannot accidentally start an auth-disabled instance reachable from the
network.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}


class InsecureBindError(RuntimeError):
    """Raised when auth-disabled mode would bind to a non-loopback interface."""


def assert_safe_bind(host: str, auth_disabled: bool) -> None:
    """Refuse to start auth-disabled mode on anything but loopback.

    This is the concrete enforcement of the ADR-007 security invariant:
    "Local auth-disabled mode cannot start on a non-loopback interface."
    """
    if auth_disabled and host not in LOOPBACK_HOSTS:
        raise InsecureBindError(
            f"refusing to bind host={host!r} with auth disabled; "
            f"auth-disabled mode is only permitted on {sorted(LOOPBACK_HOSTS)}"
        )


@dataclass(frozen=True)
class AuthConfig:
    google_client_id: str | None
    google_client_secret: str | None
    auth_disabled: bool
    session_cookie_name: str = "aimd_session"
    session_ttl_hours: int = 12

    @classmethod
    def from_env(cls) -> "AuthConfig":
        return cls(
            google_client_id=os.environ.get("GOOGLE_CLIENT_ID") or None,
            google_client_secret=os.environ.get("GOOGLE_CLIENT_SECRET") or None,
            auth_disabled=os.environ.get("AI_DIAGNOSTIC_AUTH_DISABLED", "").strip().lower()
            in {"1", "true", "yes"},
        )
