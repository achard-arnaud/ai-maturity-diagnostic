from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from starlette.testclient import TestClient

from app.authruntime.app import create_app
from app.authruntime.config import AuthConfig
from app.authruntime.db import ControlStore
from app.target_plan_routes import create_v1_target_plan_router
from app.target_plan_store import put_plan, put_stakeholder


def _plan(target_plan_id: str) -> dict:
    return {
        "target_plan_id": target_plan_id, "workspace_id": "ws-a", "company_entity_id": "c1",
        "fit_assessment_id": "fa1", "status": "active", "created_at": "2026-01-01T00:00:00+00:00", "updated_at": None,
    }


def _stakeholder(sid: str, target_plan_id: str, warm_path: str | None = None) -> dict:
    return {
        "stakeholder_role_id": sid, "target_plan_id": target_plan_id, "person_entity_id": "e1",
        "role": "sponsor", "title": "VP", "status": "active", "assigned_at": "2026-01-01T00:00:00+00:00",
        "assigned_by": "alice", "supersedes_stakeholder_role_id": None,
    }


class TargetPlanRoutesTests(unittest.TestCase):
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

        put_plan(self.root, "ws-a", _plan("tp1"))
        put_stakeholder(self.root, "ws-a", _stakeholder("sr1", "tp1"))

        app = create_app(control_store=self.store, oidc_client=None, config=self.config)
        app.include_router(create_v1_target_plan_router(self.root))
        self.client = TestClient(app)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _cookie(self, token: str) -> dict:
        return {"aimd_session": token}

    def test_unauthenticated_is_401(self) -> None:
        response = self.client.get("/api/v1/workspaces/ws-a/target-plans")
        self.assertEqual(401, response.status_code)

    def test_pagination_bounded_above_100(self) -> None:
        response = self.client.get(
            "/api/v1/workspaces/ws-a/target-plans", params={"limit": 500}, cookies=self._cookie(self.alice_token)
        )
        self.assertEqual(400, response.status_code)

    def test_pagination_bounded_below_1(self) -> None:
        response = self.client.get(
            "/api/v1/workspaces/ws-a/target-plans", params={"limit": 0}, cookies=self._cookie(self.alice_token)
        )
        self.assertEqual(400, response.status_code)

    def test_cross_workspace_plan_is_404(self) -> None:
        response = self.client.get(
            "/api/v1/workspaces/ws-a/target-plans/tp1", cookies=self._cookie(self.bob_token)
        )
        self.assertEqual(404, response.status_code)

    def test_cross_workspace_stakeholders_is_404(self) -> None:
        response = self.client.get(
            "/api/v1/workspaces/ws-a/target-plans/tp1/stakeholders", cookies=self._cookie(self.bob_token)
        )
        self.assertEqual(404, response.status_code)

    def test_own_workspace_stakeholders_succeeds(self) -> None:
        response = self.client.get(
            "/api/v1/workspaces/ws-a/target-plans/tp1/stakeholders", cookies=self._cookie(self.alice_token)
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.json()["items"]))

    def test_committee_graph_route(self) -> None:
        response = self.client.get(
            "/api/v1/workspaces/ws-a/target-plans/tp1/committee-graph", cookies=self._cookie(self.alice_token)
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.json()["nodes"]))

    def test_cross_workspace_committee_graph_is_404(self) -> None:
        response = self.client.get(
            "/api/v1/workspaces/ws-a/target-plans/tp1/committee-graph", cookies=self._cookie(self.bob_token)
        )
        self.assertEqual(404, response.status_code)


if __name__ == "__main__":
    unittest.main()
