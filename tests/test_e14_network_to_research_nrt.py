"""Epic 14 S07: full Network(Discover) -> Research NRT.

Proves the whole chain this Epic assembled actually composes end to end,
using only E14's own routes (discover/search, research-cases/acquire)
plus the existing, already-closed Epic 03/04 primitives they hand off
through (signal review -> queue-research -> ResearchCase). The review
(signal "new" -> "linked") and ResearchCase-creation-from-a-ResearchQueued-
event steps are Epic 03/04's own territory (no HTTP route exists for
either yet -- see app/signal_handoff.py's own docstring: "this module
does not create a ResearchCase ... Epic 04 S02's queue consumes these
events"), so this test performs them directly via their stores, exactly
as tests/test_signal_routes.py already does for the review step.

This is the workspace-safety half of S07's "Workspace-safe API, degraded
states, telemetry, full Network->Research NRT": every step is exercised
through both a same-workspace and a cross-workspace caller.
"""

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
from app.research_case_store import put_case
from app.research_routes import create_v1_research_router
from app.signal_routes import create_v1_signal_router
from app.signal_store import get_signal, put_signal
from scripts.social_search import Result


class NetworkToResearchNrtTests(unittest.TestCase):
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
        app.include_router(create_v1_research_router(self.root))
        self.client = TestClient(app)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _cookie(self, token: str) -> dict:
        return {"aimd_session": token}

    def test_full_discover_to_research_evidence_chain(self) -> None:
        # 1. Discover: a broad, pre-Fit search surfaces a signal.
        discover_fn = mock.Mock(
            return_value=[
                Result("hackernews", "Acme Corp ships an AI copilot", "https://news.ycombinator.com/item?id=1", "s")
            ]
        )
        with mock.patch.dict(harvest_runner.SEARCHERS, {"hackernews": discover_fn}):
            search_response = self.client.post(
                "/api/v1/workspaces/ws-a/discover/search",
                json={"query": "Acme Corp AI", "sources": ["hackernews"]},
                cookies=self._cookie(self.alice_token),
            )
        self.assertEqual(200, search_response.status_code)
        signal = search_response.json()["signals"][0]["signal"]
        self.assertEqual("new", signal["status"])

        # 2. Human review (Epic 03's own territory, no HTTP route yet):
        # link the signal to a known company.
        signal["status"] = "linked"
        signal["company_entity_id"] = "company_acme"
        put_signal(self.root, "ws-a", signal)

        # 3. Queue for research -- now legal since the signal is linked.
        queue_response = self.client.post(
            f"/api/v1/workspaces/ws-a/signals/{signal['signal_id']}/queue-research",
            cookies=self._cookie(self.alice_token),
        )
        self.assertEqual(200, queue_response.status_code)
        self.assertEqual("ResearchQueued", queue_response.json()["event_type"])

        # 4. ResearchCase creation from that event (Epic 04's own
        # territory -- no consumer route exists yet either).
        put_case(
            self.root,
            "ws-a",
            {
                "research_case_id": "rc-nrt-1",
                "workspace_id": "ws-a",
                "company_entity_id": "company_acme",
                "status": "open",
                "owner": None,
                "created_at": "2026-06-01T00:00:00+00:00",
                "updated_at": "2026-06-01T00:00:00+00:00",
                "origin_signal_id": signal["signal_id"],
                "blockers": [],
            },
        )

        # 5. Research-space acquisition against the now-open case:
        # product-blind, complementary evidence for the same company.
        research_fn = mock.Mock(
            return_value=[
                Result("reddit", "Discussion: Acme Corp's new AI copilot", "https://reddit.com/r/x/2", "s")
            ]
        )
        with mock.patch.dict(harvest_runner.SEARCHERS, {"reddit": research_fn}):
            acquire_response = self.client.post(
                "/api/v1/workspaces/ws-a/research-cases/rc-nrt-1/acquire",
                json={"query": "Acme Corp", "sources": ["reddit"]},
                cookies=self._cookie(self.alice_token),
            )
        self.assertEqual(200, acquire_response.status_code)
        evidence = acquire_response.json()["evidence"]
        self.assertEqual(1, len(evidence))
        self.assertEqual(["company_acme"], evidence[0]["entity_refs"])

        # The signal itself never picked up a demand/fit field anywhere
        # along the chain (defense-in-depth check on the persisted record).
        stored_signal = get_signal(self.root, "ws-a", signal["signal_id"])
        for forbidden in ("problem", "sponsor", "budget", "decision", "score"):
            self.assertNotIn(forbidden, stored_signal)

    def test_every_step_is_workspace_isolated(self) -> None:
        discover_fn = mock.Mock(
            return_value=[Result("hackernews", "Acme Corp news", "https://news.ycombinator.com/item?id=9", "s")]
        )
        with mock.patch.dict(harvest_runner.SEARCHERS, {"hackernews": discover_fn}):
            search_response = self.client.post(
                "/api/v1/workspaces/ws-a/discover/search",
                json={"query": "Acme", "sources": ["hackernews"]},
                cookies=self._cookie(self.alice_token),
            )
        signal_id = search_response.json()["signals"][0]["signal"]["signal_id"]

        put_case(
            self.root,
            "ws-a",
            {
                "research_case_id": "rc-nrt-2",
                "workspace_id": "ws-a",
                "company_entity_id": "company_acme",
                "status": "open",
                "owner": None,
                "created_at": "2026-06-01T00:00:00+00:00",
                "updated_at": "2026-06-01T00:00:00+00:00",
                "origin_signal_id": None,
                "blockers": [],
            },
        )

        # Bob (ws-b) can reach none of ws-a's Discover, Signal or Research
        # surfaces for this same data.
        self.assertEqual(
            404,
            self.client.post(
                "/api/v1/workspaces/ws-a/discover/search",
                json={"query": "x", "sources": ["hackernews"]},
                cookies=self._cookie(self.bob_token),
            ).status_code,
        )
        self.assertEqual(
            404,
            self.client.get(
                f"/api/v1/workspaces/ws-a/signals/{signal_id}", cookies=self._cookie(self.bob_token)
            ).status_code,
        )
        self.assertEqual(
            404,
            self.client.post(
                "/api/v1/workspaces/ws-a/research-cases/rc-nrt-2/acquire",
                json={},
                cookies=self._cookie(self.bob_token),
            ).status_code,
        )


if __name__ == "__main__":
    unittest.main()
