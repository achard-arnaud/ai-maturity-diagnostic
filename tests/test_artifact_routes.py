from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from starlette.testclient import TestClient

from app.artifact_routes import create_v1_artifact_router
from app.authruntime.app import create_app
from app.authruntime.config import AuthConfig
from app.authruntime.db import ControlStore
from app.research_case_store import put_case


def _case(research_case_id: str, workspace_id: str) -> dict:
    return {
        "research_case_id": research_case_id, "workspace_id": workspace_id,
        "company_entity_id": "entity_1", "status": "open", "owner": "alice@example.com",
        "created_at": "2026-06-01T00:00:00+00:00", "updated_at": "2026-06-01T00:00:00+00:00",
        "origin_signal_id": None, "blockers": [],
    }


class ArtifactRoutesTests(unittest.TestCase):
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

        put_case(self.root, "ws-a", _case("rc1", "ws-a"))

        app = create_app(control_store=self.store, oidc_client=None, config=self.config)
        app.include_router(create_v1_artifact_router(self.root))
        self.client = TestClient(app)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _cookie(self, token: str) -> dict:
        return {"aimd_session": token}

    def test_unauthenticated_is_401(self) -> None:
        response = self.client.get("/api/v1/workspaces/ws-a/artifacts")
        self.assertEqual(401, response.status_code)

    def test_authenticated_own_workspace_lists_seeded_artifact(self) -> None:
        response = self.client.get("/api/v1/workspaces/ws-a/artifacts", cookies=self._cookie(self.alice_token))
        self.assertEqual(200, response.status_code)
        items = response.json()["items"]
        self.assertEqual(1, len(items))
        self.assertEqual("artifact:research_case:rc1", items[0]["artifact_id"])

    def test_cross_workspace_list_is_404(self) -> None:
        response = self.client.get("/api/v1/workspaces/ws-a/artifacts", cookies=self._cookie(self.bob_token))
        self.assertEqual(404, response.status_code)

    def test_pagination_limit_is_bounded(self) -> None:
        response = self.client.get(
            "/api/v1/workspaces/ws-a/artifacts", params={"limit": 500}, cookies=self._cookie(self.alice_token)
        )
        self.assertEqual(400, response.status_code)

    def test_kind_filter(self) -> None:
        response = self.client.get(
            "/api/v1/workspaces/ws-a/artifacts",
            params={"kind": "research_case"},
            cookies=self._cookie(self.alice_token),
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.json()["items"]))

        response = self.client.get(
            "/api/v1/workspaces/ws-a/artifacts", params={"kind": "signal"}, cookies=self._cookie(self.alice_token)
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual([], response.json()["items"])

    def test_unknown_kind_is_400(self) -> None:
        response = self.client.get(
            "/api/v1/workspaces/ws-a/artifacts",
            params={"kind": "not_a_kind"},
            cookies=self._cookie(self.alice_token),
        )
        self.assertEqual(400, response.status_code)

    def test_deep_link_by_artifact_id(self) -> None:
        response = self.client.get(
            "/api/v1/workspaces/ws-a/artifacts/artifact:research_case:rc1", cookies=self._cookie(self.alice_token)
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual("research_case", response.json()["kind"])

    def test_unknown_artifact_is_404(self) -> None:
        response = self.client.get(
            "/api/v1/workspaces/ws-a/artifacts/artifact:research_case:nope", cookies=self._cookie(self.alice_token)
        )
        self.assertEqual(404, response.status_code)

    def test_cross_workspace_get_is_404(self) -> None:
        response = self.client.get(
            "/api/v1/workspaces/ws-a/artifacts/artifact:research_case:rc1", cookies=self._cookie(self.bob_token)
        )
        self.assertEqual(404, response.status_code)

    def test_archive_then_restore_round_trip(self) -> None:
        archived = self.client.post(
            "/api/v1/workspaces/ws-a/artifacts/artifact:research_case:rc1/archive",
            cookies=self._cookie(self.alice_token),
        )
        self.assertEqual(200, archived.status_code)
        self.assertEqual("archived", archived.json()["status"])

        listed_active = self.client.get(
            "/api/v1/workspaces/ws-a/artifacts", params={"status_filter": "active"}, cookies=self._cookie(self.alice_token)
        )
        self.assertEqual([], listed_active.json()["items"])

        double_archive = self.client.post(
            "/api/v1/workspaces/ws-a/artifacts/artifact:research_case:rc1/archive",
            cookies=self._cookie(self.alice_token),
        )
        self.assertEqual(400, double_archive.status_code)

        restored = self.client.post(
            "/api/v1/workspaces/ws-a/artifacts/artifact:research_case:rc1/restore",
            cookies=self._cookie(self.alice_token),
        )
        self.assertEqual(200, restored.status_code)
        self.assertEqual("active", restored.json()["status"])

    def test_cross_workspace_archive_is_404(self) -> None:
        response = self.client.post(
            "/api/v1/workspaces/ws-a/artifacts/artifact:research_case:rc1/archive",
            cookies=self._cookie(self.bob_token),
        )
        self.assertEqual(404, response.status_code)

    def test_archive_never_touches_the_underlying_research_case(self) -> None:
        # Epic 15's own "Don't": archiving an artifact must never mutate
        # the canonical object it points to.
        from app.research_case_store import get_case

        self.client.post(
            "/api/v1/workspaces/ws-a/artifacts/artifact:research_case:rc1/archive",
            cookies=self._cookie(self.alice_token),
        )
        case = get_case(self.root, "ws-a", "rc1")
        self.assertEqual("open", case["status"])


if __name__ == "__main__":
    unittest.main()
