from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from starlette.testclient import TestClient

from app.authruntime.app import create_app
from app.authruntime.config import AuthConfig
from app.authruntime.db import ControlStore
from app.network_v1_routes import create_v1_network_router
from app.network_v1_store import put_entity


def _person(entity_id: str, workspace_id: str) -> dict:
    return {
        "entity_id": entity_id,
        "legacy_ids": [f"PERS-{entity_id}"],
        "display_name": f"Person {entity_id}",
        "workspace_id": workspace_id,
        "valid_from": "2026-01-01",
        "valid_to": None,
        "status": "active",
        "merged_into_entity_id": None,
        "provenance": {"source_refs": [], "epistemic_status": "inference", "evidence_grade": "U1"},
        "last_updated": "2026-01-01",
        "stale_after_months": 6,
    }


class NetworkV1RoutesTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.store = ControlStore(self.root / "control.sqlite3")
        self.config = AuthConfig(google_client_id=None, google_client_secret=None, auth_disabled=False)

        self.store.create_workspace("ws-a", "Workspace A")
        self.store.create_workspace("ws-b", "Workspace B")

        alice = self.store.get_or_create_user("alice@example.com", "Alice")
        self.store.set_membership(alice["id"], "ws-a", "standard_user")
        self.alice_token = self.store.create_session(alice["id"])

        bob = self.store.get_or_create_user("bob@example.com", "Bob")
        self.store.set_membership(bob["id"], "ws-b", "standard_user")
        self.bob_token = self.store.create_session(bob["id"])

        put_entity(self.root, "ws-a", "person", _person("p1", "ws-a"))

        app = create_app(control_store=self.store, oidc_client=None, config=self.config)
        app.include_router(create_v1_network_router(self.root))
        self.client = TestClient(app)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _cookie(self, token: str) -> dict:
        return {"aimd_session": token}

    # -- auth -------------------------------------------------------------

    def test_unauthenticated_request_is_401(self) -> None:
        response = self.client.get("/api/v1/workspaces/ws-a/people")
        self.assertEqual(401, response.status_code)

    def test_authenticated_own_workspace_request_succeeds(self) -> None:
        response = self.client.get("/api/v1/workspaces/ws-a/people", cookies=self._cookie(self.alice_token))
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.json()["items"]))

    # -- pagination ---------------------------------------------------------

    def test_deep_link_to_a_specific_entity_is_stable(self) -> None:
        response = self.client.get("/api/v1/workspaces/ws-a/people/p1", cookies=self._cookie(self.alice_token))
        self.assertEqual(200, response.status_code)
        self.assertEqual("p1", response.json()["entity_id"])

    def test_pagination_limit_is_bounded(self) -> None:
        response = self.client.get(
            "/api/v1/workspaces/ws-a/people",
            params={"limit": 500},
            cookies=self._cookie(self.alice_token),
        )
        self.assertEqual(400, response.status_code)

    def test_unknown_entity_is_404(self) -> None:
        response = self.client.get("/api/v1/workspaces/ws-a/people/does-not-exist", cookies=self._cookie(self.alice_token))
        self.assertEqual(404, response.status_code)

    # -- IDOR -----------------------------------------------------------------

    def test_cross_workspace_list_is_404_not_leaked(self) -> None:
        # Bob (member of ws-b) tries to list ws-a's people.
        response = self.client.get("/api/v1/workspaces/ws-a/people", cookies=self._cookie(self.bob_token))
        self.assertEqual(404, response.status_code)

    def test_cross_workspace_entity_lookup_is_404_not_leaked(self) -> None:
        # Bob knows ws-a's entity_id "p1" (e.g. guessed or leaked elsewhere)
        # but is not a member of ws-a -- must not be able to fetch it.
        response = self.client.get("/api/v1/workspaces/ws-a/people/p1", cookies=self._cookie(self.bob_token))
        self.assertEqual(404, response.status_code)

    def test_person_360_composes_without_fusing_truths(self) -> None:
        response = self.client.get("/api/v1/workspaces/ws-a/people/p1/360", cookies=self._cookie(self.alice_token))
        self.assertEqual(200, response.status_code)
        body = response.json()
        self.assertIn("person", body)
        self.assertIn("relationships", body)
        self.assertIn("companies", body)

    def test_person_360_cross_workspace_is_404(self) -> None:
        response = self.client.get("/api/v1/workspaces/ws-a/people/p1/360", cookies=self._cookie(self.bob_token))
        self.assertEqual(404, response.status_code)

    def test_admin_can_access_any_workspace(self) -> None:
        admin = self.store.get_or_create_user("admin@example.com", "Admin")
        self.store.set_admin(admin["id"], True)
        admin_token = self.store.create_session(admin["id"])
        response = self.client.get("/api/v1/workspaces/ws-a/people", cookies=self._cookie(admin_token))
        self.assertEqual(200, response.status_code)


if __name__ == "__main__":
    unittest.main()
