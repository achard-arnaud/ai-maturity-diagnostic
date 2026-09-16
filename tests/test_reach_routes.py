from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from starlette.testclient import TestClient

from app.authruntime.app import create_app
from app.authruntime.config import AuthConfig
from app.authruntime.db import ControlStore
from app.reach_routes import create_v1_reach_router
from app.reach_store import put_sequence, put_step, put_task, put_touchpoint


def _sequence(sequence_id: str) -> dict:
    return {
        "sequence_id": sequence_id, "workspace_id": "ws-a", "target_plan_id": "tp1",
        "stakeholder_role_id": "sr1", "status": "active", "created_at": "2026-01-01T00:00:00Z",
    }


def _step(step_id: str, sequence_id: str) -> dict:
    return {"step_id": step_id, "sequence_id": sequence_id, "order": 1, "channel": "email", "status": "pending"}


def _task(task_id: str, sequence_id: str, step_id: str) -> dict:
    return {
        "task_id": task_id, "sequence_id": sequence_id, "step_id": step_id, "assignee": "alice",
        "due_at": "2026-01-02T00:00:00Z", "status": "open", "created_at": "2026-01-01T00:00:00Z",
    }


def _touchpoint(touchpoint_id: str, step_id: str) -> dict:
    return {
        "touchpoint_id": touchpoint_id, "step_id": step_id, "channel": "email", "content_ref": "msg-1",
        "status": "prepared", "prepared_at": "2026-01-01T00:00:00Z", "sent_at": None, "sent_by": None,
    }


class ReachRoutesTests(unittest.TestCase):
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

        put_sequence(self.root, "ws-a", _sequence("seq1"))
        put_step(self.root, "ws-a", _step("s1", "seq1"))
        put_task(self.root, "ws-a", _task("t1", "seq1", "s1"))
        put_touchpoint(self.root, "ws-a", _touchpoint("tp1", "s1"))

        app = create_app(control_store=self.store, oidc_client=None, config=self.config)
        app.include_router(create_v1_reach_router(self.root))
        self.client = TestClient(app)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _cookie(self, token: str) -> dict:
        return {"aimd_session": token}

    def test_unauthenticated_is_401(self) -> None:
        response = self.client.get("/api/v1/workspaces/ws-a/sequences")
        self.assertEqual(401, response.status_code)

    def test_pagination_bounded_above_100(self) -> None:
        response = self.client.get(
            "/api/v1/workspaces/ws-a/sequences", params={"limit": 500}, cookies=self._cookie(self.alice_token)
        )
        self.assertEqual(400, response.status_code)

    def test_pagination_bounded_below_1(self) -> None:
        response = self.client.get(
            "/api/v1/workspaces/ws-a/sequences", params={"limit": 0}, cookies=self._cookie(self.alice_token)
        )
        self.assertEqual(400, response.status_code)

    def test_own_workspace_sequences_succeeds(self) -> None:
        response = self.client.get(
            "/api/v1/workspaces/ws-a/sequences", cookies=self._cookie(self.alice_token)
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.json()["items"]))

    def test_cross_workspace_sequence_is_404(self) -> None:
        response = self.client.get(
            "/api/v1/workspaces/ws-a/sequences/seq1", cookies=self._cookie(self.bob_token)
        )
        self.assertEqual(404, response.status_code)

    def test_own_workspace_steps_succeeds(self) -> None:
        response = self.client.get(
            "/api/v1/workspaces/ws-a/sequences/seq1/steps", cookies=self._cookie(self.alice_token)
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.json()["items"]))

    def test_cross_workspace_steps_is_404(self) -> None:
        response = self.client.get(
            "/api/v1/workspaces/ws-a/sequences/seq1/steps", cookies=self._cookie(self.bob_token)
        )
        self.assertEqual(404, response.status_code)

    def test_own_workspace_tasks_succeeds(self) -> None:
        response = self.client.get(
            "/api/v1/workspaces/ws-a/sequences/seq1/tasks", cookies=self._cookie(self.alice_token)
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.json()["items"]))

    def test_own_workspace_touchpoints_succeeds(self) -> None:
        response = self.client.get(
            "/api/v1/workspaces/ws-a/sequences/seq1/steps/s1/touchpoints", cookies=self._cookie(self.alice_token)
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.json()["items"]))

    def test_cross_workspace_touchpoints_is_404(self) -> None:
        response = self.client.get(
            "/api/v1/workspaces/ws-a/sequences/seq1/steps/s1/touchpoints", cookies=self._cookie(self.bob_token)
        )
        self.assertEqual(404, response.status_code)


if __name__ == "__main__":
    unittest.main()
