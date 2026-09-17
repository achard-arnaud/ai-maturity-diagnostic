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
from app.research_case_store import put_case
from app.research_routes import create_v1_research_router
from scripts.social_search import Result


def _case(research_case_id: str, workspace_id: str, company_entity_id: str = "entity_1") -> dict:
    return {
        "research_case_id": research_case_id,
        "workspace_id": workspace_id,
        "company_entity_id": company_entity_id,
        "status": "open",
        "owner": None,
        "created_at": "2026-06-01T00:00:00+00:00",
        "updated_at": "2026-06-01T00:00:00+00:00",
        "origin_signal_id": None,
        "blockers": [],
    }


class ResearchAcquireRouteTests(unittest.TestCase):
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
        app.include_router(create_v1_research_router(self.root))
        self.client = TestClient(app)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _cookie(self, token: str) -> dict:
        return {"aimd_session": token}

    def test_unauthenticated_is_401(self) -> None:
        response = self.client.post("/api/v1/workspaces/ws-a/research-cases/rc1/acquire", json={})
        self.assertEqual(401, response.status_code)

    def test_cross_workspace_is_404(self) -> None:
        response = self.client.post(
            "/api/v1/workspaces/ws-a/research-cases/rc1/acquire",
            json={},
            cookies=self._cookie(self.bob_token),
        )
        self.assertEqual(404, response.status_code)

    def test_unknown_case_is_404(self) -> None:
        response = self.client.post(
            "/api/v1/workspaces/ws-a/research-cases/unknown/acquire",
            json={},
            cookies=self._cookie(self.alice_token),
        )
        self.assertEqual(404, response.status_code)

    def test_acquire_creates_evidence_tied_to_the_case_company(self) -> None:
        fake = mock.Mock(
            return_value=[Result("reddit", "Discussion about Acme", "https://reddit.com/r/x/1", "snippet")]
        )
        with mock.patch.dict(harvest_runner.SEARCHERS, {"reddit": fake}):
            response = self.client.post(
                "/api/v1/workspaces/ws-a/research-cases/rc1/acquire",
                json={"query": "Acme", "sources": ["reddit"]},
                cookies=self._cookie(self.alice_token),
            )
        self.assertEqual(200, response.status_code)
        body = response.json()
        self.assertEqual("rc1", body["research_case_id"])
        self.assertEqual(1, len(body["evidence"]))
        evidence = body["evidence"][0]
        self.assertEqual(["entity_1"], evidence["entity_refs"])
        self.assertEqual("ws-a", evidence["workspace_id"])

    def test_repeated_acquire_does_not_duplicate_evidence(self) -> None:
        fake = mock.Mock(
            return_value=[Result("reddit", "Discussion about Acme", "https://reddit.com/r/x/1", "snippet")]
        )
        with mock.patch.dict(harvest_runner.SEARCHERS, {"reddit": fake}):
            first = self.client.post(
                "/api/v1/workspaces/ws-a/research-cases/rc1/acquire",
                json={"query": "Acme", "sources": ["reddit"]},
                cookies=self._cookie(self.alice_token),
            )
            second = self.client.post(
                "/api/v1/workspaces/ws-a/research-cases/rc1/acquire",
                json={"query": "Acme", "sources": ["reddit"]},
                cookies=self._cookie(self.alice_token),
            )
        self.assertEqual(
            first.json()["evidence"][0]["evidence_id"],
            second.json()["evidence"][0]["evidence_id"],
        )

    def test_missing_sources_falls_back_to_research_space_recommended_sources(self) -> None:
        empty = mock.Mock(return_value=[])
        with mock.patch.dict(
            harvest_runner.SEARCHERS, {name: empty for name in ("youtube", "reddit", "perplexity")}
        ):
            response = self.client.post(
                "/api/v1/workspaces/ws-a/research-cases/rc1/acquire",
                json={"query": "Acme"},
                cookies=self._cookie(self.alice_token),
            )
        self.assertEqual(200, response.status_code)
        sources_called = {r["source"] for r in response.json()["source_runs"]}
        self.assertEqual({"youtube", "reddit", "perplexity"}, sources_called)


if __name__ == "__main__":
    unittest.main()
