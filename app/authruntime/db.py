"""SQLite/WAL control store for ADR-007.

Stores ONLY runtime control-plane state: users, workspaces, memberships,
sessions and audit events. It is never a store for canonical business
artifacts (studies, product catalog, qualification, reach, ...), which
remain file-based under the repository root per ADR-004/ADR-007 §4.
"""

from __future__ import annotations

import sqlite3
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterator, Optional

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    name TEXT,
    is_admin INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS workspaces (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TEXT NOT NULL
);

-- A non-admin user belongs to exactly one workspace (product_owner or
-- standard_user). Admin users typically have no membership row: their
-- access is global and is derived from users.is_admin, never from RBAC
-- membership rows, per ADR-007 §7 (roles are flat, not hierarchical).
CREATE TABLE IF NOT EXISTS memberships (
    user_id TEXT PRIMARY KEY REFERENCES users(id),
    workspace_id TEXT NOT NULL REFERENCES workspaces(id),
    role TEXT NOT NULL CHECK (role IN ('product_owner', 'standard_user')),
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
    token TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id),
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    revoked_at TEXT
);

CREATE TABLE IF NOT EXISTS audit_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    actor TEXT NOT NULL,
    action TEXT NOT NULL,
    target TEXT,
    reason TEXT,
    timestamp TEXT NOT NULL
);

-- A qualification-blocker override is a tracked human decision layered
-- on top of the business hard gate in app/qualification.py. It never
-- mutates or deletes the underlying blocker; the dashboard may later
-- choose to surface it alongside the still-present blocker.
CREATE TABLE IF NOT EXISTS overrides (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workspace_id TEXT NOT NULL REFERENCES workspaces(id),
    blocker_id TEXT NOT NULL,
    actor TEXT NOT NULL,
    reason TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""

DEFAULT_WORKSPACE_ID = "default"
DEFAULT_WORKSPACE_NAME = "Default (legacy mono-root)"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class ControlStore:
    """Thin, explicit wrapper around the SQLite control database.

    Kept deliberately small and dependency-free (stdlib sqlite3 only) so
    that plain-Python business modules never need to know it exists.
    """

    path: Path

    def __post_init__(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.init_schema()

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.path, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def init_schema(self) -> None:
        with self.connect() as conn:
            conn.executescript(SCHEMA)
            row = conn.execute(
                "SELECT id FROM workspaces WHERE id = ?", (DEFAULT_WORKSPACE_ID,)
            ).fetchone()
            if row is None:
                conn.execute(
                    "INSERT INTO workspaces (id, name, created_at) VALUES (?, ?, ?)",
                    (DEFAULT_WORKSPACE_ID, DEFAULT_WORKSPACE_NAME, _now()),
                )

    # -- users -----------------------------------------------------------
    def get_or_create_user(self, email: str, name: str | None) -> sqlite3.Row:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
            if row is not None:
                return row
            user_id = str(uuid.uuid4())
            conn.execute(
                "INSERT INTO users (id, email, name, is_admin, created_at) VALUES (?, ?, ?, 0, ?)",
                (user_id, email, name, _now()),
            )
            return conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

    def get_user(self, user_id: str) -> Optional[sqlite3.Row]:
        with self.connect() as conn:
            return conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

    def list_users(self) -> list[sqlite3.Row]:
        with self.connect() as conn:
            return conn.execute(
                """
                SELECT users.*, memberships.workspace_id AS workspace_id, memberships.role AS role
                FROM users LEFT JOIN memberships ON memberships.user_id = users.id
                ORDER BY users.created_at
                """
            ).fetchall()

    def search_users(
        self,
        *,
        text: str | None = None,
        role: str | None = None,
        workspace_id: str | None = None,
    ) -> list[sqlite3.Row]:
        """List users with their membership, optionally filtered.

        `text` matches a case-insensitive substring of the email. `role`
        is either 'admin' (users.is_admin) or a memberships.role value
        ('product_owner' / 'standard_user'). `workspace_id` filters by
        the user's membership workspace. All filters combine with AND.
        """
        clauses: list[str] = []
        params: list[str] = []
        if text:
            clauses.append("users.email LIKE ?")
            params.append(f"%{text}%")
        if role == "admin":
            clauses.append("users.is_admin = 1")
        elif role is not None:
            clauses.append("memberships.role = ?")
            params.append(role)
        if workspace_id is not None:
            clauses.append("memberships.workspace_id = ?")
            params.append(workspace_id)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        with self.connect() as conn:
            return conn.execute(
                f"""
                SELECT users.*, memberships.workspace_id AS workspace_id, memberships.role AS role
                FROM users LEFT JOIN memberships ON memberships.user_id = users.id
                {where}
                ORDER BY users.created_at
                """,
                params,
            ).fetchall()

    def set_admin(self, user_id: str, is_admin: bool) -> None:
        with self.connect() as conn:
            conn.execute("UPDATE users SET is_admin = ? WHERE id = ?", (1 if is_admin else 0, user_id))

    # -- workspaces --------------------------------------------------------
    def create_workspace(self, workspace_id: str, name: str) -> sqlite3.Row:
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO workspaces (id, name, created_at) VALUES (?, ?, ?)",
                (workspace_id, name, _now()),
            )
            return conn.execute("SELECT * FROM workspaces WHERE id = ?", (workspace_id,)).fetchone()

    def get_workspace(self, workspace_id: str) -> Optional[sqlite3.Row]:
        with self.connect() as conn:
            return conn.execute("SELECT * FROM workspaces WHERE id = ?", (workspace_id,)).fetchone()

    def list_workspaces(self) -> list[sqlite3.Row]:
        with self.connect() as conn:
            return conn.execute("SELECT * FROM workspaces ORDER BY created_at").fetchall()

    # -- memberships -------------------------------------------------------
    def set_membership(self, user_id: str, workspace_id: str, role: str) -> None:
        if role not in {"product_owner", "standard_user"}:
            raise ValueError(f"invalid membership role: {role}")
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO memberships (user_id, workspace_id, role, created_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET workspace_id = excluded.workspace_id, role = excluded.role
                """,
                (user_id, workspace_id, role, _now()),
            )

    def get_membership(self, user_id: str) -> Optional[sqlite3.Row]:
        with self.connect() as conn:
            return conn.execute(
                "SELECT * FROM memberships WHERE user_id = ?", (user_id,)
            ).fetchone()

    # -- sessions ------------------------------------------------------------
    def create_session(self, user_id: str, ttl_hours: int = 12) -> str:
        token = uuid.uuid4().hex + uuid.uuid4().hex
        now = datetime.now(timezone.utc)
        expires = now + timedelta(hours=ttl_hours)
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO sessions (token, user_id, created_at, expires_at, revoked_at) VALUES (?, ?, ?, ?, NULL)",
                (token, user_id, now.isoformat(), expires.isoformat()),
            )
        return token

    def get_session_user(self, token: str) -> Optional[sqlite3.Row]:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT sessions.*, users.id AS user_id_col, users.email AS email,
                       users.name AS name, users.is_admin AS is_admin
                FROM sessions JOIN users ON users.id = sessions.user_id
                WHERE sessions.token = ?
                """,
                (token,),
            ).fetchone()
            if row is None:
                return None
            if row["revoked_at"] is not None:
                return None
            expires_at = datetime.fromisoformat(row["expires_at"])
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if expires_at < datetime.now(timezone.utc):
                return None
            return row

    def revoke_session(self, token: str) -> None:
        with self.connect() as conn:
            conn.execute(
                "UPDATE sessions SET revoked_at = ? WHERE token = ? AND revoked_at IS NULL",
                (_now(), token),
            )

    # -- audit ---------------------------------------------------------------
    def record_audit(self, actor: str, action: str, target: str | None, reason: str | None) -> None:
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO audit_events (actor, action, target, reason, timestamp) VALUES (?, ?, ?, ?, ?)",
                (actor, action, target, reason, _now()),
            )

    def list_audit(self, limit: int = 200) -> list[sqlite3.Row]:
        with self.connect() as conn:
            return conn.execute(
                "SELECT * FROM audit_events ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()

    # -- overrides -------------------------------------------------------------
    def record_override(self, workspace_id: str, blocker_id: str, actor: str, reason: str) -> int:
        with self.connect() as conn:
            cur = conn.execute(
                "INSERT INTO overrides (workspace_id, blocker_id, actor, reason, created_at) VALUES (?, ?, ?, ?, ?)",
                (workspace_id, blocker_id, actor, reason, _now()),
            )
            return int(cur.lastrowid)

    def list_overrides(self, workspace_id: str | None = None) -> list[sqlite3.Row]:
        with self.connect() as conn:
            if workspace_id is None:
                return conn.execute("SELECT * FROM overrides ORDER BY id DESC").fetchall()
            return conn.execute(
                "SELECT * FROM overrides WHERE workspace_id = ? ORDER BY id DESC", (workspace_id,)
            ).fetchall()
