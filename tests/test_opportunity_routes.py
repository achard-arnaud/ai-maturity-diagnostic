from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from starlette.testclient import TestClient

from app.authruntime.app import create_app
from app.authruntime.config import AuthConfig
from app.authruntime.db import ControlStore
from app.opportunity_routes import create_v1_opportunity_router
from app.opportunity_store import put_opportunity


def _opportunity(opportunity_id: str, workspace_id: str, status: str = "draft") -> dict:
    return {
        "opportunity_id": opportunity_id,
        "workspace_id": workspace_id,
        "lead_id": "lead-1",
        "demand_id": "demand-1",
        "fit_assessment_id": "fit-1",
        "target_plan_id": "plan-1",
        "status": status,
        "created_at": "2026-06-01T00:00:00+00:00",
        "updated_at": None,
    }


class OpportunityRoutesTests(unittest.TestCase):
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

        put_opportunity(self.root, "ws-a", _opportunity("opp1", "ws-a"))

        app = create_app(control_store=self.store, oidc_client=None, config=self.config)
        app.include_router(create_v1_opportunity_router(self.root))
        self.client = TestClient(app)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _cookie(self, token: str) -> dict:
        return {"aimd_session": token}

    def test_list_unauthenticated_is_401(self) -> None:
        response = self.client.get("/api/v1/workspaces/ws-a/opportunities")
        self.assertEqual(401, response.status_code)

    def test_list_authenticated_own_workspace_succeeds(self) -> None:
        response = self.client.get("/api/v1/workspaces/ws-a/opportunities", cookies=self._cookie(self.alice_token))
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.json()["items"]))
        self.assertEqual("opp1", response.json()["items"][0]["opportunity_id"])

    def test_list_pagination_limit_is_bounded(self) -> None:
        response = self.client.get(
            "/api/v1/workspaces/ws-a/opportunities", params={"limit": 500}, cookies=self._cookie(self.alice_token)
        )
        self.assertEqual(400, response.status_code)

    def test_list_cross_workspace_is_404(self) -> None:
        response = self.client.get("/api/v1/workspaces/ws-a/opportunities", cookies=self._cookie(self.bob_token))
        self.assertEqual(404, response.status_code)

    def test_deep_link_by_opportunity_id(self) -> None:
        response = self.client.get(
            "/api/v1/workspaces/ws-a/opportunities/opp1", cookies=self._cookie(self.alice_token)
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual("opp1", response.json()["opportunity_id"])

    def test_unknown_opportunity_is_404(self) -> None:
        response = self.client.get(
            "/api/v1/workspaces/ws-a/opportunities/nope", cookies=self._cookie(self.alice_token)
        )
        self.assertEqual(404, response.status_code)

    def test_cross_workspace_entity_lookup_is_404(self) -> None:
        response = self.client.get(
            "/api/v1/workspaces/ws-a/opportunities/opp1", cookies=self._cookie(self.bob_token)
        )
        self.assertEqual(404, response.status_code)

    def test_pipeline_board_unauthenticated_is_401(self) -> None:
        response = self.client.get("/api/v1/workspaces/ws-a/opportunities/pipeline-board")
        self.assertEqual(401, response.status_code)

    def test_pipeline_board_contains_every_stage_including_empty(self) -> None:
        response = self.client.get(
            "/api/v1/workspaces/ws-a/opportunities/pipeline-board", cookies=self._cookie(self.alice_token)
        )
        self.assertEqual(200, response.status_code)
        stages = response.json()["stages"]
        self.assertIn("draft", stages)
        self.assertIn("closed_won", stages)
        self.assertEqual(["opp1"], [item["opportunity_id"] for item in stages["draft"]])
        self.assertEqual([], stages["closed_won"])

    def test_pipeline_board_cross_workspace_is_404(self) -> None:
        response = self.client.get(
            "/api/v1/workspaces/ws-a/opportunities/pipeline-board", cookies=self._cookie(self.bob_token)
        )
        self.assertEqual(404, response.status_code)


if __name__ == "__main__":
    unittest.main()
