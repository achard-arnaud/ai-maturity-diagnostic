from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from starlette.requests import Request
from starlette.testclient import TestClient

from app.authruntime.app import create_app
from app.authruntime.config import AuthConfig
from app.authruntime.db import ControlStore
from app.authruntime.oidc import OIDCUserInfo


class _StubOIDCClient:
    """Stand-in for GoogleOIDCClient — no real Google credentials needed.

    Mirrors the Authlib-facing surface (`authorize_redirect`,
    `authorize_userinfo`) so /auth/callback can be exercised end-to-end
    without a live OIDC round trip.
    """

    def __init__(self, userinfo: OIDCUserInfo) -> None:
        self.userinfo = userinfo
        self.redirect_calls = 0

    async def authorize_redirect(self, request: Request, redirect_uri: str):
        from starlette.responses import RedirectResponse

        self.redirect_calls += 1
        return RedirectResponse(url="https://accounts.google.com/o/oauth2/fake")

    async def authorize_userinfo(self, request: Request) -> OIDCUserInfo:
        return self.userinfo


class AuthRuntimeAppTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.store = ControlStore(Path(self._tmp.name) / "control.sqlite3")
        self.config = AuthConfig(google_client_id=None, google_client_secret=None, auth_disabled=False)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _client(self, oidc_client=None) -> TestClient:
        app = create_app(
            control_store=self.store,
            oidc_client=oidc_client,
            config=self.config,
            session_secret="test-secret",
        )
        return TestClient(app, base_url="https://testserver")

    def _login_as(self, client: TestClient, email: str, name: str = "Test User"):
        stub = _StubOIDCClient(OIDCUserInfo(email=email, name=name, sub=email))
        client.app.state.oidc_client = stub
        response = client.get("/auth/callback", follow_redirects=False)
        self.assertEqual(response.status_code, 303)
        return response

    # -- login/callback -----------------------------------------------------
    def test_login_without_configured_provider_is_503(self) -> None:
        client = self._client(oidc_client=None)
        response = client.get("/auth/login")
        self.assertEqual(response.status_code, 503)

    def test_callback_creates_user_and_opaque_session_cookie(self) -> None:
        client = self._client()
        self._login_as(client, "newuser@example.com")
        cookie = client.cookies.get(self.config.session_cookie_name)
        self.assertIsNotNone(cookie)
        # The cookie is opaque: never the raw email/provider token.
        self.assertNotIn("newuser@example.com", cookie)
        user = self.store.get_or_create_user("newuser@example.com", "Test User")
        self.assertIsNotNone(user)

    def test_callback_redirects_admin_to_admin_workspaces(self) -> None:
        client = self._client()
        user = self.store.get_or_create_user("admin@example.com", "Admin")
        self.store.set_admin(user["id"], True)
        response = self._login_as(client, "admin@example.com")
        self.assertEqual("/admin/workspaces", response.headers["location"])

    def test_callback_redirects_member_to_their_workspace_home(self) -> None:
        client = self._client()
        self.store.create_workspace("acme", "Acme Corp")
        user = self.store.get_or_create_user("member@example.com", "Member")
        self.store.set_membership(user["id"], "acme", "standard_user")
        response = self._login_as(client, "member@example.com")
        self.assertEqual("/w/acme/home", response.headers["location"])

    def test_callback_redirects_user_without_membership_to_pending_page(self) -> None:
        client = self._client()
        response = self._login_as(client, "nobody@example.com")
        self.assertEqual("/auth/pending", response.headers["location"])

    def test_pending_page_requires_authentication(self) -> None:
        client = self._client()
        response = client.get("/auth/pending")
        self.assertEqual(401, response.status_code)

    def test_pending_page_renders_for_authenticated_user_without_membership(self) -> None:
        client = self._client()
        self._login_as(client, "waiting@example.com")
        response = client.get("/auth/pending")
        self.assertEqual(200, response.status_code)

    def test_logout_revokes_session(self) -> None:
        client = self._client()
        self._login_as(client, "logout@example.com")
        response = client.post("/auth/logout", follow_redirects=False)
        self.assertEqual(response.status_code, 303)
        # Session cookie should no longer grant admin access.
        page = client.get("/admin/workspaces")
        self.assertEqual(page.status_code, 401)

    # -- RBAC -----------------------------------------------------------------
    def test_admin_page_requires_authentication(self) -> None:
        client = self._client()
        response = client.get("/admin/workspaces")
        self.assertEqual(response.status_code, 401)

    def test_non_admin_cannot_reach_admin_page(self) -> None:
        client = self._client()
        self._login_as(client, "plain@example.com")
        response = client.get("/admin/workspaces")
        self.assertEqual(response.status_code, 403)

    def test_admin_can_create_workspace_and_see_it_listed(self) -> None:
        client = self._client()
        self._login_as(client, "admin@example.com")
        user = self.store.get_or_create_user("admin@example.com", "Admin")
        self.store.set_admin(user["id"], True)

        create = client.post(
            "/admin/workspaces", data={"workspace_id": "acme", "name": "Acme Corp"}, follow_redirects=False
        )
        self.assertEqual(create.status_code, 303)
        page = client.get("/admin/workspaces")
        self.assertIn("Acme Corp", page.text)

    def test_admin_can_change_membership_role(self) -> None:
        client = self._client()
        self._login_as(client, "admin2@example.com")
        admin_user = self.store.get_or_create_user("admin2@example.com", "Admin2")
        self.store.set_admin(admin_user["id"], True)
        target_user = self.store.get_or_create_user("target@example.com", "Target")
        self.store.create_workspace("ws-1", "Workspace One")

        resp = client.post(
            "/admin/memberships",
            data={"user_id": target_user["id"], "workspace_id": "ws-1", "role": "product_owner"},
            follow_redirects=False,
        )
        self.assertEqual(resp.status_code, 303)
        membership = self.store.get_membership(target_user["id"])
        self.assertEqual(membership["role"], "product_owner")

    def test_admin_can_view_audit_log(self) -> None:
        client = self._client()
        self._login_as(client, "admin3@example.com")
        admin_user = self.store.get_or_create_user("admin3@example.com", "Admin3")
        self.store.set_admin(admin_user["id"], True)
        client.post("/admin/workspaces", data={"workspace_id": "ws-audit", "name": "Audited"}, follow_redirects=False)

        audit_page = client.get("/admin/audit")
        self.assertEqual(audit_page.status_code, 200)
        self.assertIn("create_workspace", audit_page.text)

    def test_admin_overrides_page_forbidden_for_non_admin(self) -> None:
        client = self._client()
        self._login_as(client, "plain-overrides@example.com")
        response = client.get("/admin/overrides")
        self.assertEqual(response.status_code, 403)

    def test_admin_overrides_page_lists_overrides_for_admin(self) -> None:
        client = self._client()
        self._login_as(client, "admin-overrides@example.com")
        admin_user = self.store.get_or_create_user("admin-overrides@example.com", "AdminOverrides")
        self.store.set_admin(admin_user["id"], True)
        self.store.create_workspace("ws-overrides", "Workspace Overrides")
        self.store.record_override("ws-overrides", "study-1:demand", "po@example.com", "Exec-sponsored timebox")

        response = client.get("/admin/overrides")
        self.assertEqual(response.status_code, 200)
        self.assertIn("study-1:demand", response.text)
        self.assertIn("Exec-sponsored timebox", response.text)

    def test_admin_overrides_page_filters_by_workspace(self) -> None:
        client = self._client()
        self._login_as(client, "admin-overrides2@example.com")
        admin_user = self.store.get_or_create_user("admin-overrides2@example.com", "AdminOverrides2")
        self.store.set_admin(admin_user["id"], True)
        self.store.create_workspace("ws-ov-a", "Workspace Ov A")
        self.store.create_workspace("ws-ov-b", "Workspace Ov B")
        self.store.record_override("ws-ov-a", "study-a:demand", "po-a@example.com", "reason a")
        self.store.record_override("ws-ov-b", "study-b:demand", "po-b@example.com", "reason b")

        response = client.get("/admin/overrides", params={"workspace_id": "ws-ov-a"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("study-a:demand", response.text)
        self.assertNotIn("study-b:demand", response.text)

    def test_admin_overrides_page_splits_open_and_resolved(self) -> None:
        client = self._client()
        self._login_as(client, "admin-overrides3@example.com")
        admin_user = self.store.get_or_create_user("admin-overrides3@example.com", "AdminOverrides3")
        self.store.set_admin(admin_user["id"], True)
        self.store.create_workspace("ws-ov-c", "Workspace Ov C")
        open_id = self.store.record_override("ws-ov-c", "study-open:demand", "po-c@example.com", "reason open")
        resolved_id = self.store.record_override(
            "ws-ov-c", "study-resolved:demand", "po-c@example.com", "reason resolved"
        )
        self.store.resolve_override(resolved_id, actor="admin-overrides3@example.com")

        response = client.get("/admin/overrides")
        self.assertEqual(response.status_code, 200)
        text = response.text
        self.assertIn("Open", text)
        self.assertIn("Resolved", text)
        self.assertIn("study-open:demand", text)
        self.assertIn("study-resolved:demand", text)
        self.assertIn(f"/admin/overrides/{open_id}/resolve", text)
        # The already-resolved row has no Resolve form for it.
        self.assertNotIn(f"/admin/overrides/{resolved_id}/resolve", text)

    def test_resolve_override_route_requires_admin(self) -> None:
        client = self._client()
        self._login_as(client, "plain-resolver@example.com")
        self.store.create_workspace("ws-resolve-auth", "Workspace Resolve Auth")
        override_id = self.store.record_override(
            "ws-resolve-auth", "study-x:demand", "po-x@example.com", "reason x"
        )
        response = client.post(f"/admin/overrides/{override_id}/resolve", follow_redirects=False)
        self.assertEqual(response.status_code, 403)

    def test_resolve_override_route_records_real_actor(self) -> None:
        client = self._client()
        self._login_as(client, "admin-resolver@example.com")
        admin_user = self.store.get_or_create_user("admin-resolver@example.com", "AdminResolver")
        self.store.set_admin(admin_user["id"], True)
        self.store.create_workspace("ws-resolve", "Workspace Resolve")
        override_id = self.store.record_override(
            "ws-resolve", "study-y:demand", "po-y@example.com", "reason y"
        )

        response = client.post(f"/admin/overrides/{override_id}/resolve", follow_redirects=False)
        self.assertEqual(response.status_code, 303)

        rows = self.store.list_overrides(workspace_id="ws-resolve")
        self.assertEqual(rows[0]["resolved_by"], "admin-resolver@example.com")
        self.assertIsNotNone(rows[0]["resolved_at"])

        audit = self.store.list_audit()
        self.assertTrue(any(e["action"] == "resolve_override" for e in audit))

    def test_admin_users_page_forbidden_for_non_admin(self) -> None:
        client = self._client()
        self._login_as(client, "plain2@example.com")
        response = client.get("/admin/users")
        self.assertEqual(response.status_code, 403)

    def test_admin_users_page_lists_users_for_admin(self) -> None:
        client = self._client()
        self._login_as(client, "admin5@example.com")
        admin_user = self.store.get_or_create_user("admin5@example.com", "Admin5")
        self.store.set_admin(admin_user["id"], True)
        self.store.get_or_create_user("searchable@example.com", "Searchable")

        response = client.get("/admin/users")
        self.assertEqual(response.status_code, 200)
        self.assertIn("searchable@example.com", response.text)
        self.assertIn("admin5@example.com", response.text)

    def test_admin_memberships_listing_forbidden_for_non_admin(self) -> None:
        client = self._client()
        self._login_as(client, "plain7@example.com")
        response = client.get("/admin/memberships")
        self.assertEqual(response.status_code, 403)

    def test_admin_memberships_listing_shows_memberships_for_admin(self) -> None:
        client = self._client()
        self._login_as(client, "admin7@example.com")
        admin_user = self.store.get_or_create_user("admin7@example.com", "Admin7")
        self.store.set_admin(admin_user["id"], True)
        member_user = self.store.get_or_create_user("member7@example.com", "Member7")
        self.store.create_workspace("ws-7", "Workspace Seven")
        self.store.set_membership(member_user["id"], "ws-7", "product_owner")

        response = client.get("/admin/memberships")
        self.assertEqual(response.status_code, 200)
        self.assertIn("member7@example.com", response.text)
        self.assertIn("ws-7", response.text)
        self.assertIn("product_owner", response.text)

    def test_admin_users_page_text_filter_narrows_results(self) -> None:
        client = self._client()
        self._login_as(client, "admin6@example.com")
        admin_user = self.store.get_or_create_user("admin6@example.com", "Admin6")
        self.store.set_admin(admin_user["id"], True)
        self.store.get_or_create_user("keepme@example.com", "KeepMe")
        self.store.get_or_create_user("excludeme@example.com", "ExcludeMe")

        response = client.get("/admin/users", params={"text": "keepme"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("keepme@example.com", response.text)
        self.assertNotIn("excludeme@example.com", response.text)

    # -- workspace scoping / IDOR -----------------------------------------
    def test_product_owner_cannot_override_another_workspace_blocker(self) -> None:
        client = self._client()
        self._login_as(client, "owner@example.com")
        owner = self.store.get_or_create_user("owner@example.com", "Owner")
        self.store.create_workspace("ws-mine", "Mine")
        self.store.create_workspace("ws-other", "Other")
        self.store.set_membership(owner["id"], "ws-mine", "product_owner")

        response = client.post(
            "/api/workspaces/ws-other/qualification/study-1:demand/override",
            data={"reason": "trying to reach across workspaces"},
        )
        self.assertEqual(response.status_code, 404)  # per ADR-007 §1: no ownership disclosure

    def test_standard_user_cannot_override_own_workspace_blocker(self) -> None:
        client = self._client()
        self._login_as(client, "viewer@example.com")
        viewer = self.store.get_or_create_user("viewer@example.com", "Viewer")
        self.store.create_workspace("ws-view", "Viewable")
        self.store.set_membership(viewer["id"], "ws-view", "standard_user")

        response = client.post(
            "/api/workspaces/ws-view/qualification/study-1:demand/override",
            data={"reason": "should not be permitted"},
        )
        self.assertEqual(response.status_code, 403)

    def test_product_owner_can_override_own_workspace_blocker_with_audit_trail(self) -> None:
        client = self._client()
        self._login_as(client, "owner2@example.com")
        owner = self.store.get_or_create_user("owner2@example.com", "Owner2")
        self.store.create_workspace("ws-own", "Own")
        self.store.set_membership(owner["id"], "ws-own", "product_owner")

        response = client.post(
            "/api/workspaces/ws-own/qualification/study-1:demand/override",
            data={"reason": "Exec sponsor accepted the risk in writing"},
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["workspace_id"], "ws-own")
        self.assertEqual(body["blocker_id"], "study-1:demand")

        overrides = self.store.list_overrides("ws-own")
        self.assertEqual(len(overrides), 1)
        self.assertEqual(overrides[0]["actor"], "owner2@example.com")
        audit = self.store.list_audit()
        self.assertTrue(any(e["action"] == "qualification_override" for e in audit))

    def test_override_requires_mandatory_reason(self) -> None:
        client = self._client()
        self._login_as(client, "owner3@example.com")
        owner = self.store.get_or_create_user("owner3@example.com", "Owner3")
        self.store.create_workspace("ws-r", "R")
        self.store.set_membership(owner["id"], "ws-r", "product_owner")

        response = client.post(
            "/api/workspaces/ws-r/qualification/study-1:demand/override",
            data={"reason": "   "},
        )
        self.assertEqual(response.status_code, 400)

    def test_admin_can_override_any_workspace_blocker(self) -> None:
        client = self._client()
        self._login_as(client, "admin4@example.com")
        admin_user = self.store.get_or_create_user("admin4@example.com", "Admin4")
        self.store.set_admin(admin_user["id"], True)
        self.store.create_workspace("ws-any", "Any")

        response = client.post(
            "/api/workspaces/ws-any/qualification/study-1:demand/override",
            data={"reason": "Admin override with justification"},
        )
        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
