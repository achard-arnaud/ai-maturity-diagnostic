from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from starlette.testclient import TestClient

from app import harvest_runner
from app.authruntime.app import create_app
from app.authruntime.config import AuthConfig
from app.authruntime.db import ControlStore
from app.discover_routes import create_v1_discover_router
from app.signal_routes import create_v1_signal_router
from scripts.social_search import Result


class DiscoverRoutesTests(unittest.TestCase):
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

        app = create_app(control_store=self.store, oidc_client=None, config=self.config)
        app.include_router(create_v1_discover_router(self.root))
        app.include_router(create_v1_signal_router(self.root))
        self.client = TestClient(app)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _cookie(self, token: str) -> dict:
        return {"aimd_session": token}

    def test_unauthenticated_is_401(self) -> None:
        response = self.client.post("/api/v1/workspaces/ws-a/discover/search", json={"query": "x"})
        self.assertEqual(401, response.status_code)

    def test_cross_workspace_search_is_404(self) -> None:
        response = self.client.post(
            "/api/v1/workspaces/ws-a/discover/search",
            json={"query": "x", "sources": ["hackernews"]},
            cookies=self._cookie(self.bob_token),
        )
        self.assertEqual(404, response.status_code)

    def test_missing_query_is_400(self) -> None:
        response = self.client.post(
            "/api/v1/workspaces/ws-a/discover/search",
            json={"sources": ["hackernews"]},
            cookies=self._cookie(self.alice_token),
        )
        self.assertEqual(400, response.status_code)

    def test_search_creates_signals_and_they_are_readable_via_get_signals(self) -> None:
        fake = mock.Mock(
            return_value=[
                Result("hackernews", "Acme ships an AI feature", "https://news.ycombinator.com/item?id=1", "snippet")
            ]
        )
        with mock.patch.dict(harvest_runner.SEARCHERS, {"hackernews": fake}):
            response = self.client.post(
                "/api/v1/workspaces/ws-a/discover/search",
                json={"query": "acme AI", "sources": ["hackernews"]},
                cookies=self._cookie(self.alice_token),
            )
        self.assertEqual(200, response.status_code)
        body = response.json()
        self.assertEqual("completed", body["status"])
        self.assertEqual(1, len(body["signals"]))
        self.assertEqual("hackernews", body["signals"][0]["why_matched"]["acquisition_source"])
        self.assertEqual("acme AI", body["signals"][0]["why_matched"]["query"])
        signal = body["signals"][0]["signal"]
        self.assertEqual("new", signal["status"])
        self.assertEqual("ws-a", signal["workspace_id"])

        listed = self.client.get("/api/v1/workspaces/ws-a/signals", cookies=self._cookie(self.alice_token))
        self.assertEqual(200, listed.status_code)
        self.assertEqual([signal["signal_id"]], [item["signal_id"] for item in listed.json()["items"]])

    def test_repeated_search_does_not_duplicate_the_same_signal(self) -> None:
        fake = mock.Mock(
            return_value=[
                Result("hackernews", "Acme ships an AI feature", "https://news.ycombinator.com/item?id=1", "snippet")
            ]
        )
        with mock.patch.dict(harvest_runner.SEARCHERS, {"hackernews": fake}):
            first = self.client.post(
                "/api/v1/workspaces/ws-a/discover/search",
                json={"query": "acme AI", "sources": ["hackernews"]},
                cookies=self._cookie(self.alice_token),
            )
            second = self.client.post(
                "/api/v1/workspaces/ws-a/discover/search",
                json={"query": "acme AI", "sources": ["hackernews"]},
                cookies=self._cookie(self.alice_token),
            )
        first_signal_id = first.json()["signals"][0]["signal"]["signal_id"]
        second_signal_id = second.json()["signals"][0]["signal"]["signal_id"]
        self.assertEqual(first_signal_id, second_signal_id)

        listed = self.client.get("/api/v1/workspaces/ws-a/signals", cookies=self._cookie(self.alice_token))
        self.assertEqual(1, len(listed.json()["items"]))

    def test_no_sources_given_falls_back_to_discover_recommended_sources(self) -> None:
        empty = mock.Mock(return_value=[])
        with mock.patch.dict(
            harvest_runner.SEARCHERS,
            {name: empty for name in ("hackernews", "arxiv", "github", "web", "x")},
        ):
            response = self.client.post(
                "/api/v1/workspaces/ws-a/discover/search",
                json={"query": "acme AI"},
                cookies=self._cookie(self.alice_token),
            )
        self.assertEqual(200, response.status_code)
        sources_called = {r["source"] for r in response.json()["source_runs"]}
        self.assertEqual({"hackernews", "arxiv", "github", "web", "x"}, sources_called)

    def test_linkedin_from_discover_space_is_rejected(self) -> None:
        # ADR-011 S6: linkedin is Targets-space (post-Fit) only.
        response = self.client.post(
            "/api/v1/workspaces/ws-a/discover/search",
            json={"query": "acme", "sources": ["linkedin"]},
            cookies=self._cookie(self.alice_token),
        )
        self.assertEqual(400, response.status_code)


if __name__ == "__main__":
    unittest.main()
