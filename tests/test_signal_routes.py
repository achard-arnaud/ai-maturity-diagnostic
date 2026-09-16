from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from starlette.testclient import TestClient

from app.authruntime.app import create_app
from app.authruntime.config import AuthConfig
from app.authruntime.db import ControlStore
from app.signal_routes import create_v1_signal_router
from app.signal_store import put_signal


def _signal(signal_id: str, workspace_id: str) -> dict:
    return {
        "signal_id": signal_id,
        "workspace_id": workspace_id,
        "source": {"kind": "public", "ref": "ref"},
        "observed_at": "2026-06-01T00:00:00+00:00",
        "status": "new",
        "company_entity_id": None,
        "dedup_key": f"key-{signal_id}",
        "freshness": {"stale_after_days": 30},
        "provenance": {"source_refs": ["ref"], "epistemic_status": "fact", "evidence_grade": "P1"},
    }


class SignalRoutesTests(unittest.TestCase):
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

        put_signal(self.root, "ws-a", _signal("s1", "ws-a"))

        app = create_app(control_store=self.store, oidc_client=None, config=self.config)
        app.include_router(create_v1_signal_router(self.root))
        self.client = TestClient(app)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _cookie(self, token: str) -> dict:
        return {"aimd_session": token}

    def test_unauthenticated_is_401(self) -> None:
        response = self.client.get("/api/v1/workspaces/ws-a/signals")
        self.assertEqual(401, response.status_code)

    def test_authenticated_own_workspace_succeeds(self) -> None:
        response = self.client.get("/api/v1/workspaces/ws-a/signals", cookies=self._cookie(self.alice_token))
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.json()["items"]))

    def test_pagination_limit_is_bounded(self) -> None:
        response = self.client.get("/api/v1/workspaces/ws-a/signals", params={"limit": 500}, cookies=self._cookie(self.alice_token))
        self.assertEqual(400, response.status_code)

    def test_deep_link_by_signal_id(self) -> None:
        response = self.client.get("/api/v1/workspaces/ws-a/signals/s1", cookies=self._cookie(self.alice_token))
        self.assertEqual(200, response.status_code)
        self.assertEqual("s1", response.json()["signal_id"])

    def test_unknown_signal_is_404(self) -> None:
        response = self.client.get("/api/v1/workspaces/ws-a/signals/nope", cookies=self._cookie(self.alice_token))
        self.assertEqual(404, response.status_code)

    def test_cross_workspace_list_is_404(self) -> None:
        response = self.client.get("/api/v1/workspaces/ws-a/signals", cookies=self._cookie(self.bob_token))
        self.assertEqual(404, response.status_code)

    def test_cross_workspace_entity_lookup_is_404(self) -> None:
        response = self.client.get("/api/v1/workspaces/ws-a/signals/s1", cookies=self._cookie(self.bob_token))
        self.assertEqual(404, response.status_code)

    def test_e2e_new_signal_cannot_be_queued_for_research(self) -> None:
        # s1 is status "new" (unreviewed) -- the E2E "signal -> queue"
        # handoff must reject it, not silently queue an unreviewed signal.
        response = self.client.post("/api/v1/workspaces/ws-a/signals/s1/queue-research", cookies=self._cookie(self.alice_token))
        self.assertEqual(400, response.status_code)

    def test_e2e_linked_signal_can_be_queued_for_research(self) -> None:
        linked = _signal("s2", "ws-a")
        linked["status"] = "linked"
        linked["company_entity_id"] = "entity_1"
        put_signal(self.root, "ws-a", linked)

        response = self.client.post("/api/v1/workspaces/ws-a/signals/s2/queue-research", cookies=self._cookie(self.alice_token))

        self.assertEqual(200, response.status_code)
        self.assertEqual("ResearchQueued", response.json()["event_type"])


if __name__ == "__main__":
    unittest.main()
