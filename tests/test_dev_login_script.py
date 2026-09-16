"""Regression test for scripts/dev_login.py's default --db path.

dev_login.py exists so a human (or an E2E run) can mint a real session
without going through Google OIDC. Its --db default must point at the same
SQLite file the running app actually authenticates sessions against
(app/authruntime/app.py's ControlStore(...) construction), or a session
minted with the documented default command is silently written to the wrong
file and every subsequent authenticated request comes back "session invalid
or expired" even though the token is genuine.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class DevLoginDefaultDbTests(unittest.TestCase):
    def test_default_db_matches_control_store_path(self) -> None:
        dev_login_source = (ROOT / "scripts" / "dev_login.py").read_text()
        match = re.search(r'"--db",\s*\n\s*default="([^"]+)"', dev_login_source)
        self.assertIsNotNone(match, "could not find --db default in scripts/dev_login.py")
        default_db = match.group(1)  # type: ignore[union-attr]

        app_source = (ROOT / "app" / "authruntime" / "app.py").read_text()
        control_store_match = re.search(
            r'ControlStore\(ROOT / "([^"]+)" / "([^"]+)" / "([^"]+)"\)', app_source
        )
        self.assertIsNotNone(
            control_store_match, "could not find the real ControlStore(...) path in app/authruntime/app.py"
        )
        expected = "/".join(control_store_match.groups())  # type: ignore[union-attr]

        self.assertEqual(
            default_db,
            expected,
            "scripts/dev_login.py --db default must match the path app/authruntime/app.py "
            "uses for its real ControlStore, or a session minted with the documented "
            "default command lands in the wrong SQLite file and every request comes "
            "back 'session invalid or expired'",
        )


if __name__ == "__main__":
    unittest.main()
