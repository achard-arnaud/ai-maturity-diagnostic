from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from starlette.testclient import TestClient

from app.authruntime.app import create_app
from app.authruntime.config import AuthConfig
from app.authruntime.db import ControlStore
from app.demand_routes import create_v1_demand_router
from app.demand_store import create_demand
from app.demand_policy import known, unknown


def _demand(demand_id: str, company_entity_id: str = "entity_1") -> dict:
    return {
        "demand_id": demand_id,
        "workspace_id": "ws-a",
        "company_entity_id": company_entity_id,
        "status": "observed",
        "problem": known("manual onboarding"),
        "population": unknown(),
        "impact": unknown(),
        "urgency": unknown(),
        "initiative": unknown(),
        "sponsor": unknown(),
        "budget": unknown(),
        "timing": unknown(),
        "claim_ids": [],
        "origin_profile_ref": None,
        "created_at": "2026-01-01T00:00:00+00:00",
        "updated_at": "2026-01-01T00:00:00+00:00",
    }


class DemandRoutesTests(unittest.TestCase):
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

        create_demand(self.root, "ws-a", _demand("d1"))

        app = create_app(control_store=self.store, oidc_client=None, config=self.config)
        app.include_router(create_v1_demand_router(self.root))
        self.client = TestClient(app)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _cookie(self, token: str) -> dict:
        return {"aimd_session": token}

    def test_unauthenticated_list_is_401(self) -> None:
        response = self.client.get("/api/v1/workspaces/ws-a/demands")
        self.assertEqual(401, response.status_code)

    def test_authenticated_list_succeeds(self) -> None:
        response = self.client.get("/api/v1/workspaces/ws-a/demands", cookies=self._cookie(self.alice_token))
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.json()["items"]))

    def test_cross_workspace_get_is_404(self) -> None:
        response = self.client.get("/api/v1/workspaces/ws-a/demands/d1", cookies=self._cookie(self.bob_token))
        self.assertEqual(404, response.status_code)

    def test_get_returns_version(self) -> None:
        response = self.client.get("/api/v1/workspaces/ws-a/demands/d1", cookies=self._cookie(self.alice_token))
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, response.json()["version"])

    def test_create_duplicate_id_is_409(self) -> None:
        response = self.client.post(
            "/api/v1/workspaces/ws-a/demands", json=_demand("d1"), cookies=self._cookie(self.alice_token)
        )
        self.assertEqual(409, response.status_code)

    def test_patch_with_correct_version_succeeds(self) -> None:
        response = self.client.patch(
            "/api/v1/workspaces/ws-a/demands/d1",
            json={"expected_version": 1, "status": "qualifying"},
            cookies=self._cookie(self.alice_token),
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual("qualifying", response.json()["status"])
        self.assertEqual(2, response.json()["version"])

    def test_patch_with_stale_version_is_409(self) -> None:
        self.client.patch(
            "/api/v1/workspaces/ws-a/demands/d1",
            json={"expected_version": 1, "status": "qualifying"},
            cookies=self._cookie(self.alice_token),
        )
        response = self.client.patch(
            "/api/v1/workspaces/ws-a/demands/d1",
            json={"expected_version": 1, "status": "rejected"},
            cookies=self._cookie(self.alice_token),
        )
        self.assertEqual(409, response.status_code)

    def test_patch_missing_expected_version_is_400(self) -> None:
        response = self.client.patch(
            "/api/v1/workspaces/ws-a/demands/d1",
            json={"status": "qualifying"},
            cookies=self._cookie(self.alice_token),
        )
        self.assertEqual(400, response.status_code)

    def test_patch_unknown_demand_is_404(self) -> None:
        response = self.client.patch(
            "/api/v1/workspaces/ws-a/demands/nope",
            json={"expected_version": 1, "status": "qualifying"},
            cookies=self._cookie(self.alice_token),
        )
        self.assertEqual(404, response.status_code)

    def test_resolver_blocked_when_no_buying_signal(self) -> None:
        response = self.client.get(
            "/api/v1/workspaces/ws-a/demands/d1/resolver", cookies=self._cookie(self.alice_token)
        )
        self.assertEqual(200, response.status_code)
        self.assertTrue(response.json()["blocked"])
        self.assertIn("buying signal", response.json()["why_blocked"])

    def test_e2e_detect_to_qualify_keeps_unknowns_visible(self) -> None:
        # "Detect": a fresh demand exists with several dimensions unknown
        # (d1's fixture already models this).
        get_response = self.client.get(
            "/api/v1/workspaces/ws-a/demands/d1", cookies=self._cookie(self.alice_token)
        )
        self.assertEqual(200, get_response.status_code)
        demand = get_response.json()
        self.assertFalse(demand["sponsor"]["known"])
        self.assertFalse(demand["population"]["known"])

        # Blocked: no buying signal known yet -- the resolver says so.
        resolver_response = self.client.get(
            "/api/v1/workspaces/ws-a/demands/d1/resolver", cookies=self._cookie(self.alice_token)
        )
        self.assertTrue(resolver_response.json()["blocked"])

        # Move to qualifying, then supply the missing buying signal.
        self.client.patch(
            "/api/v1/workspaces/ws-a/demands/d1",
            json={"expected_version": demand["version"], "status": "qualifying"},
            cookies=self._cookie(self.alice_token),
        )
        patched = self.client.patch(
            "/api/v1/workspaces/ws-a/demands/d1",
            json={"expected_version": demand["version"] + 1, "sponsor": {"known": True, "value": "VP Sales"}},
            cookies=self._cookie(self.alice_token),
        )
        self.assertEqual(200, patched.status_code)

        # Now unblocked -- the resolver clears.
        resolver_after = self.client.get(
            "/api/v1/workspaces/ws-a/demands/d1/resolver", cookies=self._cookie(self.alice_token)
        )
        self.assertFalse(resolver_after.json()["blocked"])

        # "unknowns visibles": population/impact/etc. are still explicitly
        # unknown in the response -- qualifying never hides or fabricates them.
        final = patched.json()
        self.assertFalse(final["population"]["known"])
        self.assertFalse(final["budget"]["known"])
        self.assertTrue(final["sponsor"]["known"])


if __name__ == "__main__":
    unittest.main()
