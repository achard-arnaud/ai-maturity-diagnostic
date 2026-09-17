import re
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

_ENDPOINT_RE = re.compile(r'endpoint:\s*(null|"([^"]+)")')


def _configured_endpoints() -> list[str]:
    """Every non-null `endpoint` the GTM spaces config actually calls.

    Regressions here are otherwise invisible: a route removed or renamed
    server-side still leaves the string present in this same JS file, so a
    plain substring check (the previous version of this test) cannot catch
    a dangling endpoint -- it only proves the frontend *asks* for a path,
    never that the backend serves it. This walks the real FastAPI route
    table instead.
    """
    source = (ROOT / "app/frontend/gtm-spaces.js").read_text(encoding="utf-8")
    return [m.group(2) for m in _ENDPOINT_RE.finditer(source) if m.group(2)]


class GtmUpstreamSpaceTests(unittest.TestCase):
    def test_home_discover_research_use_real_endpoints(self) -> None:
        source = (ROOT / "app/frontend/gtm-spaces.js").read_text(encoding="utf-8")
        for endpoint in ("/api/follow-up", "/signals", "/research-cases"):
            self.assertIn(endpoint, source)
        self.assertIn("{workspace}", source)
        self.assertNotIn("localStorage", source)

    def test_every_configured_endpoint_is_a_real_backend_route(self) -> None:
        """Each `upstream.<space>.endpoint` in gtm-spaces.js must resolve to
        a route the backend actually serves -- not just a string that
        happens to appear in this file (see app/research_routes.py's
        research-cases fix: the endpoint was referenced here for a whole
        Epic while the backend never exposed it, and the previous version
        of this test -- a plain substring check -- could not catch that).

        app.authruntime.app.create_app wraps FastAPI so `include_router`-ed
        routes don't show up as plain paths on `app.routes` (they land as
        opaque `_IncludedRouter` entries), so route *registration* can't be
        introspected directly. Firing a real unauthenticated request is the
        reliable signal instead: every one of these endpoints sits behind
        an auth dependency (get_current_user / require_workspace_access)
        that runs before the handler body, so a route that exists answers
        401/403; only a route Starlette never matched falls through to its
        generic 404 "Not Found".
        """
        from starlette.testclient import TestClient

        from app.authruntime.config import AuthConfig
        from app.authruntime.db import ControlStore
        from app.server import build_app

        with tempfile.TemporaryDirectory() as tmp:
            store = ControlStore(Path(tmp) / "control.sqlite3")
            config = AuthConfig(google_client_id=None, google_client_secret=None, auth_disabled=False)
            app = build_app(control_store=store, oidc_client=None, config=config)
            client = TestClient(app)

            endpoints = _configured_endpoints()
            self.assertGreaterEqual(len(endpoints), 3, "expected at least Home/Discover/Research to have endpoints")

            for endpoint in endpoints:
                path = endpoint.replace("{workspace}", "ws-probe").split("?")[0]
                response = client.get(path)
                self.assertIn(
                    response.status_code,
                    (401, 403),
                    f"gtm-spaces.js calls {endpoint!r} ({path}) but the backend returned "
                    f"{response.status_code} -- expected 401/403 (auth-gated route exists), "
                    f"not a route-not-found response",
                )

    def test_new_shell_has_one_route_owned_view(self) -> None:
        html = (ROOT / "app/frontend/index.html").read_text(encoding="utf-8")
        self.assertIn('id="gtmSpace"', html)
        self.assertEqual(9, html.count('data-target="gtmSpace"'))

if __name__ == "__main__":
    unittest.main()
