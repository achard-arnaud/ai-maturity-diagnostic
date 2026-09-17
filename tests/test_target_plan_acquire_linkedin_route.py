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
from app.target_plan_routes import create_v1_target_plan_router
from app.target_plan_store import put_plan, put_stakeholder
from scripts.social_search import Result


def _plan(target_plan_id: str, workspace_id: str = "ws-a") -> dict:
    return {
        "target_plan_id": target_plan_id, "workspace_id": workspace_id, "company_entity_id": "c1",
        "fit_assessment_id": "fa1", "status": "active", "created_at": "2026-01-01T00:00:00+00:00", "updated_at": None,
    }


def _stakeholder(sid: str, target_plan_id: str, person_entity_id: str = "e1") -> dict:
    return {
        "stakeholder_role_id": sid, "target_plan_id": target_plan_id, "person_entity_id": person_entity_id,
        "role": "sponsor", "title": "VP Engineering", "status": "active", "assigned_at": "2026-01-01T00:00:00+00:00",
        "assigned_by": "alice", "supersedes_stakeholder_role_id": None,
    }


class AcquireLinkedInRouteTests(unittest.TestCase):
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
        response = self.client.post(
            "/api/v1/workspaces/ws-a/target-plans/tp1/stakeholders/sr1/acquire-linkedin", json={}
        )
        self.assertEqual(401, response.status_code)

    def test_cross_workspace_is_404(self) -> None:
        response = self.client.post(
            "/api/v1/workspaces/ws-a/target-plans/tp1/stakeholders/sr1/acquire-linkedin",
            json={},
            cookies=self._cookie(self.bob_token),
        )
        self.assertEqual(404, response.status_code)

    def test_unknown_plan_is_404(self) -> None:
        response = self.client.post(
            "/api/v1/workspaces/ws-a/target-plans/unknown/stakeholders/sr1/acquire-linkedin",
            json={},
            cookies=self._cookie(self.alice_token),
        )
        self.assertEqual(404, response.status_code)

    def test_unknown_stakeholder_is_404(self) -> None:
        response = self.client.post(
            "/api/v1/workspaces/ws-a/target-plans/tp1/stakeholders/unknown/acquire-linkedin",
            json={},
            cookies=self._cookie(self.alice_token),
        )
        self.assertEqual(404, response.status_code)

    def test_acquire_creates_candidate_only_identity_mappings(self) -> None:
        fake = mock.Mock(
            return_value=[
                Result(
                    "linkedin",
                    "Jane Doe - VP Engineering",
                    "https://linkedin.com/in/jane-doe",
                    "snippet",
                    metadata={"live_role_validation": False, "canonical_identity_resolution": False},
                )
            ]
        )
        with mock.patch.dict(harvest_runner.SEARCHERS, {"linkedin": fake}):
            response = self.client.post(
                "/api/v1/workspaces/ws-a/target-plans/tp1/stakeholders/sr1/acquire-linkedin",
                json={},
                cookies=self._cookie(self.alice_token),
            )
        self.assertEqual(200, response.status_code)
        body = response.json()
        self.assertEqual(1, len(body["identity_mappings"]))
        mapping = body["identity_mappings"][0]
        self.assertEqual("candidate", mapping["status"])
        self.assertEqual("e1", mapping["internal_entity_id"])
        self.assertEqual("person", mapping["internal_entity_type"])

        listed = self.client.get(
            "/api/v1/workspaces/ws-a/target-plans/tp1/stakeholders/sr1/identity-mappings",
            cookies=self._cookie(self.alice_token),
        )
        self.assertEqual(200, listed.status_code)
        self.assertEqual(1, len(listed.json()["items"]))

    def test_repeated_acquire_does_not_duplicate_mapping(self) -> None:
        fake = mock.Mock(
            return_value=[Result("linkedin", "Jane Doe", "https://linkedin.com/in/jane-doe", "snippet")]
        )
        with mock.patch.dict(harvest_runner.SEARCHERS, {"linkedin": fake}):
            first = self.client.post(
                "/api/v1/workspaces/ws-a/target-plans/tp1/stakeholders/sr1/acquire-linkedin",
                json={},
                cookies=self._cookie(self.alice_token),
            )
            second = self.client.post(
                "/api/v1/workspaces/ws-a/target-plans/tp1/stakeholders/sr1/acquire-linkedin",
                json={},
                cookies=self._cookie(self.alice_token),
            )
        self.assertEqual(
            first.json()["identity_mappings"][0]["mapping_id"],
            second.json()["identity_mappings"][0]["mapping_id"],
        )


if __name__ == "__main__":
    unittest.main()
