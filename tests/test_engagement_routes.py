from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from starlette.testclient import TestClient

from app.authruntime.app import create_app
from app.authruntime.config import AuthConfig
from app.authruntime.db import ControlStore
from app.engagement_routes import create_v1_engagement_router
from app.engagement_store import put_conversation, put_engagement_event, put_objection


def _conversation(conversation_id: str) -> dict:
    return {
        "conversation_id": conversation_id, "workspace_id": "ws-a", "target_plan_id": "tp1",
        "stakeholder_role_id": "sr1", "sequence_id": "seq1", "status": "open",
        "created_at": "2026-01-01T00:00:00Z",
    }


def _event(engagement_event_id: str, conversation_id: str) -> dict:
    return {
        "engagement_event_id": engagement_event_id, "conversation_id": conversation_id,
        "touchpoint_id": None, "kind": "replied", "channel": "email", "occurred_at": "2026-01-01T00:00:00Z",
        "source_ref": "src-1", "raw_ref": None,
    }


def _objection(objection_id: str, engagement_event_id: str) -> dict:
    return {
        "objection_id": objection_id, "engagement_event_id": engagement_event_id, "category": "price",
        "confidence": 0.5, "status": "draft", "raised_at": "2026-01-01T00:00:00Z",
        "reviewed_by": None, "reviewed_at": None,
    }


class EngagementRoutesTests(unittest.TestCase):
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

        put_conversation(self.root, "ws-a", _conversation("c1"))
        put_engagement_event(self.root, "ws-a", _event("ee1", "c1"))
        put_objection(self.root, "ws-a", _objection("o1", "ee1"))

        app = create_app(control_store=self.store, oidc_client=None, config=self.config)
        app.include_router(create_v1_engagement_router(self.root))
        self.client = TestClient(app)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _cookie(self, token: str) -> dict:
        return {"aimd_session": token}

    def test_unauthenticated_is_401(self) -> None:
        response = self.client.get("/api/v1/workspaces/ws-a/conversations")
        self.assertEqual(401, response.status_code)

    def test_pagination_bounded_above_100(self) -> None:
        response = self.client.get(
            "/api/v1/workspaces/ws-a/conversations", params={"limit": 500}, cookies=self._cookie(self.alice_token)
        )
        self.assertEqual(400, response.status_code)

    def test_own_workspace_conversations_succeeds(self) -> None:
        response = self.client.get(
            "/api/v1/workspaces/ws-a/conversations", cookies=self._cookie(self.alice_token)
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.json()["items"]))

    def test_cross_workspace_conversation_is_404(self) -> None:
        response = self.client.get(
            "/api/v1/workspaces/ws-a/conversations/c1", cookies=self._cookie(self.bob_token)
        )
        self.assertEqual(404, response.status_code)

    def test_own_workspace_events_succeeds(self) -> None:
        response = self.client.get(
            "/api/v1/workspaces/ws-a/conversations/c1/events", cookies=self._cookie(self.alice_token)
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.json()["items"]))

    def test_own_workspace_objections_succeeds(self) -> None:
        response = self.client.get(
            "/api/v1/workspaces/ws-a/conversations/c1/events/ee1/objections", cookies=self._cookie(self.alice_token)
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.json()["items"]))

    def test_cross_workspace_events_is_404(self) -> None:
        response = self.client.get(
            "/api/v1/workspaces/ws-a/conversations/c1/events", cookies=self._cookie(self.bob_token)
        )
        self.assertEqual(404, response.status_code)


if __name__ == "__main__":
    unittest.main()
