from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from starlette.testclient import TestClient

from app.authruntime.app import create_app
from app.authruntime.config import AuthConfig
from app.authruntime.db import ControlStore
from app.fit_routes import create_v1_fit_router
from app.fit_store import create_fit


def _assessment(fit_assessment_id: str, *, input_hash: str = "h1") -> dict:
    return {
        "fit_assessment_id": fit_assessment_id,
        "workspace_id": "ws-a",
        "input_lock": {"demand_id": "d1", "demand_version": 1, "product_snapshot_id": "snap1", "input_hash": input_hash},
        "status": "draft",
        "gates": [],
        "coverage": None,
        "gaps": [],
        "alternatives": [],
        "counter_evidence": [],
        "score": None,
        "verdict": None,
        "created_at": "2026-01-01T00:00:00+00:00",
        "updated_at": None,
    }


class FitRoutesTests(unittest.TestCase):
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

        create_fit(self.root, "ws-a", _assessment("fa1", input_hash="h1"))
        create_fit(self.root, "ws-a", _assessment("fa2", input_hash="h1"))

        app = create_app(control_store=self.store, oidc_client=None, config=self.config)
        app.include_router(create_v1_fit_router(self.root))
        self.client = TestClient(app)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _cookie(self, token: str) -> dict:
        return {"aimd_session": token}

    def test_unauthenticated_is_401(self) -> None:
        response = self.client.get("/api/v1/workspaces/ws-a/fit-assessments")
        self.assertEqual(401, response.status_code)

    def test_cross_workspace_get_is_404(self) -> None:
        response = self.client.get("/api/v1/workspaces/ws-a/fit-assessments/fa1", cookies=self._cookie(self.bob_token))
        self.assertEqual(404, response.status_code)

    def test_create_duplicate_is_409(self) -> None:
        response = self.client.post(
            "/api/v1/workspaces/ws-a/fit-assessments", json=_assessment("fa1"), cookies=self._cookie(self.alice_token)
        )
        self.assertEqual(409, response.status_code)

    def test_patch_with_stale_version_is_409(self) -> None:
        self.client.patch(
            "/api/v1/workspaces/ws-a/fit-assessments/fa1",
            json={"expected_version": 1, "status": "in_review"},
            cookies=self._cookie(self.alice_token),
        )
        response = self.client.patch(
            "/api/v1/workspaces/ws-a/fit-assessments/fa1",
            json={"expected_version": 1, "status": "decided"},
            cookies=self._cookie(self.alice_token),
        )
        self.assertEqual(409, response.status_code)

    def test_patch_missing_expected_version_is_400(self) -> None:
        response = self.client.patch(
            "/api/v1/workspaces/ws-a/fit-assessments/fa1",
            json={"status": "in_review"},
            cookies=self._cookie(self.alice_token),
        )
        self.assertEqual(400, response.status_code)

    def test_compare_route_reports_same_input_lock(self) -> None:
        response = self.client.get(
            "/api/v1/workspaces/ws-a/fit-assessments/compare",
            params={"left_id": "fa1", "right_id": "fa2"},
            cookies=self._cookie(self.alice_token),
        )
        self.assertEqual(200, response.status_code)
        self.assertTrue(response.json()["same_input_lock"])

    def test_idempotent_patch_with_same_change_and_correct_version(self) -> None:
        # Applying the identical update twice with the version each
        # returned is safe -- second call still succeeds against its own
        # freshly-returned version, no double-application hazard.
        first = self.client.patch(
            "/api/v1/workspaces/ws-a/fit-assessments/fa1",
            json={"expected_version": 1, "status": "in_review"},
            cookies=self._cookie(self.alice_token),
        )
        self.assertEqual(200, first.status_code)
        second = self.client.patch(
            "/api/v1/workspaces/ws-a/fit-assessments/fa1",
            json={"expected_version": first.json()["version"], "status": "in_review"},
            cookies=self._cookie(self.alice_token),
        )
        self.assertEqual(200, second.status_code)


if __name__ == "__main__":
    unittest.main()
