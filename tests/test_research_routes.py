from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from starlette.testclient import TestClient

from app.authruntime.app import create_app
from app.authruntime.config import AuthConfig
from app.authruntime.db import ControlStore
from app.claim_store import put_claim
from app.research_case_store import put_case
from app.research_routes import create_v1_research_router


def _claim(claim_id: str, company_entity_id: str) -> dict:
    return {
        "claim_id": claim_id,
        "workspace_id": "ws-a",
        "research_case_id": "rc1",
        "company_entity_id": company_entity_id,
        "statement": "stmt",
        "claim_type": "fact",
        "evidence_ids": [],
        "derived_from_claim_ids": [],
        "status": "active",
        "contradicted_by_claim_ids": [],
    }


def _case(research_case_id: str, workspace_id: str) -> dict:
    return {
        "research_case_id": research_case_id,
        "workspace_id": workspace_id,
        "company_entity_id": "entity_1",
        "status": "open",
        "owner": None,
        "created_at": "2026-06-01T00:00:00+00:00",
        "updated_at": "2026-06-01T00:00:00+00:00",
        "origin_signal_id": None,
        "blockers": [],
    }


class ResearchRoutesTests(unittest.TestCase):
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

        put_claim(self.root, "ws-a", _claim("c1", "entity_1"))
        put_case(self.root, "ws-a", _case("rc1", "ws-a"))

        app = create_app(control_store=self.store, oidc_client=None, config=self.config)
        app.include_router(create_v1_research_router(self.root))
        self.client = TestClient(app)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _cookie(self, token: str) -> dict:
        return {"aimd_session": token}

    def test_unauthenticated_is_401(self) -> None:
        response = self.client.get("/api/v1/workspaces/ws-a/companies/entity_1/360")
        self.assertEqual(401, response.status_code)

    def test_authenticated_own_workspace_succeeds(self) -> None:
        response = self.client.get(
            "/api/v1/workspaces/ws-a/companies/entity_1/360", cookies=self._cookie(self.alice_token)
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.json()["claims"]["fact"]))

    def test_cross_workspace_is_404(self) -> None:
        response = self.client.get(
            "/api/v1/workspaces/ws-a/companies/entity_1/360", cookies=self._cookie(self.bob_token)
        )
        self.assertEqual(404, response.status_code)

    def test_list_cases_unauthenticated_is_401(self) -> None:
        response = self.client.get("/api/v1/workspaces/ws-a/research-cases")
        self.assertEqual(401, response.status_code)

    def test_list_cases_authenticated_own_workspace_succeeds(self) -> None:
        response = self.client.get(
            "/api/v1/workspaces/ws-a/research-cases", cookies=self._cookie(self.alice_token)
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.json()["items"]))
        self.assertEqual("rc1", response.json()["items"][0]["research_case_id"])

    def test_list_cases_pagination_limit_is_bounded(self) -> None:
        response = self.client.get(
            "/api/v1/workspaces/ws-a/research-cases", params={"limit": 500}, cookies=self._cookie(self.alice_token)
        )
        self.assertEqual(400, response.status_code)

    def test_list_cases_cross_workspace_is_404(self) -> None:
        response = self.client.get(
            "/api/v1/workspaces/ws-a/research-cases", cookies=self._cookie(self.bob_token)
        )
        self.assertEqual(404, response.status_code)

    def test_deep_link_by_research_case_id(self) -> None:
        response = self.client.get(
            "/api/v1/workspaces/ws-a/research-cases/rc1", cookies=self._cookie(self.alice_token)
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual("rc1", response.json()["research_case_id"])

    def test_unknown_case_is_404(self) -> None:
        response = self.client.get(
            "/api/v1/workspaces/ws-a/research-cases/nope", cookies=self._cookie(self.alice_token)
        )
        self.assertEqual(404, response.status_code)

    def test_cross_workspace_case_lookup_is_404(self) -> None:
        response = self.client.get(
            "/api/v1/workspaces/ws-a/research-cases/rc1", cookies=self._cookie(self.bob_token)
        )
        self.assertEqual(404, response.status_code)


if __name__ == "__main__":
    unittest.main()
