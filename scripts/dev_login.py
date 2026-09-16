"""Mint a real, working local session without going through Google OIDC.

For manually walking through the app's screens/journeys yourself. This
never calls any LLM/agent and never touches Google -- it uses the app's own
real session mechanism (ControlStore.create_session), the same one the E2E
Playwright suite uses to get an authenticated browser context. It creates
the user as a workspace admin so every tab/journey (including admin pages)
is reachable, since a partial role would hide some of the journeys you are
trying to walk.

Usage:
    python scripts/dev_login.py [email] [--hours N]

Then open the app in a browser, open devtools -> Application -> Cookies,
and set a cookie named aimd_session (see AuthConfig.session_cookie_name)
on the app's origin with the printed value. Reload: you are logged in.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.authruntime.config import AuthConfig
from app.authruntime.db import DEFAULT_WORKSPACE_ID, ControlStore


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("email", nargs="?", default="dev@example.com")
    parser.add_argument("--name", default="Dev User")
    parser.add_argument("--hours", type=int, default=24 * 30)
    parser.add_argument(
        "--db",
        default="data/control/control.sqlite3",
        help=(
            "Path to the control-plane SQLite file (default matches the app's own "
            "default -- see app/authruntime/app.py's ControlStore(...) construction)."
        ),
    )
    args = parser.parse_args()

    config = AuthConfig.from_env()
    db_path = Path(args.db)
    store = ControlStore(db_path)

    user = store.get_or_create_user(args.email, args.name)
    store.set_admin(user["id"], True)
    with store.connect() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO memberships (user_id, workspace_id, role) VALUES (?, ?, ?)",
            (user["id"], DEFAULT_WORKSPACE_ID, "product_owner"),
        )

    token = store.create_session(user["id"], ttl_hours=args.hours)

    print(f"User:    {args.email} (admin, workspace={DEFAULT_WORKSPACE_ID})")
    print(f"Cookie:  {config.session_cookie_name}={token}")
    print(f"Expires: in {args.hours}h")
    print()
    print("In your browser devtools (Application/Storage -> Cookies), on the app's origin, set:")
    print(f"  name  = {config.session_cookie_name}")
    print(f"  value = {token}")
    print("Then reload the page.")


if __name__ == "__main__":
    main()
