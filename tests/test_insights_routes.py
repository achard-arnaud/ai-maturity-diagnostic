from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from starlette.testclient import TestClient

from app.authruntime.app import create_app
from app.authruntime.config import AuthConfig
from app.authruntime.db import ControlStore
from app.event_journal import EventJournal
from app.insights_routes import create_v1_insights_router


class InsightsRoutesTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(); self.root = Path(self.tmp.name)
        store = ControlStore(self.root / "control.sqlite3")
        store.create_workspace("ws-a", "A"); store.create_workspace("ws-b", "B")
        alice = store.get_or_create_user("alice@example.com", "Alice"); store.set_membership(alice["id"], "ws-a", "product_owner")
        bob = store.get_or_create_user("bob@example.com", "Bob"); store.set_membership(bob["id"], "ws-b", "standard_user")
        self.alice = store.create_session(alice["id"]); self.bob = store.create_session(bob["id"])
        app = create_app(control_store=store, oidc_client=None, config=AuthConfig(google_client_id=None, google_client_secret=None, auth_disabled=False))
        app.include_router(create_v1_insights_router(self.root)); self.client = TestClient(app)
        journal = EventJournal(self.root)
        for index, (kind, data) in enumerate((("journey.started", {}), ("journey.completed", {}), ("quality.checked", {"passed": True}), ("execution.completed", {"cost_units": 1.25})), start=1):
            journal.append(kind, workspace_id="ws-a", actor_id="test", data={"source": "outbound", "sector": "software", **data}, idempotency_key=f"fixture-{index}")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def cookie(self, token: str) -> dict:
        return {"aimd_session": token}

    def test_projection_is_aggregated_rebuildable_and_private(self) -> None:
        response = self.client.get("/api/v1/workspaces/ws-a/insights", params={"source": "outbound", "sector": "software"}, cookies=self.cookie(self.alice))
        self.assertEqual(200, response.status_code)
        body = response.json(); self.assertFalse(body["authoritative"]); self.assertFalse(body["privacy"]["suppressed"])
        self.assertNotIn("events", body); self.assertEqual(4, body["source_event_count"])

    def test_small_cohort_is_suppressed_and_cross_workspace_is_hidden(self) -> None:
        small = self.client.get("/api/v1/workspaces/ws-a/insights", params={"source": "missing"}, cookies=self.cookie(self.alice)).json()
        self.assertTrue(small["privacy"]["suppressed"]); self.assertEqual([], small["metrics"])
        denied = self.client.get("/api/v1/workspaces/ws-a/insights", cookies=self.cookie(self.bob))
        self.assertEqual(404, denied.status_code)

    def test_proposal_can_be_created_reviewed_and_accepted_without_mutating_target(self) -> None:
        target = self.root / "prompts" / "x.md"; target.parent.mkdir(); target.write_text("baseline", encoding="utf-8")
        created = self.client.post("/api/v1/workspaces/ws-a/learning-proposals", cookies=self.cookie(self.alice), json={"origin": "retrospective", "target_kind": "prompt", "target_ref": "prompts/x.md", "hypothesis": "improve quality", "evidence_refs": ["evt-1"]})
        self.assertEqual(201, created.status_code); proposal_id = created.json()["proposal_id"]
        for to_status in ("in_review", "accepted"):
            changed = self.client.post(f"/api/v1/workspaces/ws-a/learning-proposals/{proposal_id}/transitions", cookies=self.cookie(self.alice), json={"to_status": to_status, "rationale": "bounded review"})
            self.assertEqual(200, changed.status_code)
        self.assertEqual("baseline", target.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
