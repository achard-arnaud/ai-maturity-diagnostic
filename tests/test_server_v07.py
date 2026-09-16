from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from starlette.testclient import TestClient

from app import network_index, server as server_module
from app.authruntime.deps import RequestContext, get_current_user


class FakeControl:
    def list_skills(self): return [{"id": "skill"}]
    def list_offers(self): return [{"offer_id": "O1"}]
    def list_shelves(self): return [{"shelf_id": "s1"}]
    def backlog(self): return [{"id": "T1"}]
    def invoke(self, skill_id, payload): return {"status": "prepared", "skill": skill_id, "payload": payload}


class FakeHarvester:
    def stage(self, payload, persist=True): return {"status": "staged", "persist": persist, "payload": payload}
    def discover_public(self, payload, persist=True): return {"status": "discovered", "persist": persist, "payload": payload}


class FakeDemand:
    def snapshot(self): return {"sectors": []}
    def inventories(self): return []
    def create_demand_profile(self, **kwargs): return {"study_id": "s-new", "profile_path": "studies/s-new/05_enterprise_demand_profile.yaml", "profile": {**kwargs}, "created_study": True}


class FakeQualification:
    def list_studies(self): return [{"study_id": "s1", "company_id": "c1"}]


class FakeNudging:
    def list_inventories(self): return [{"study_id": "s1"}]
    def generate_request(self, payload): return {"nudges": [], "payload": payload}
    def accept_nudge(self, study_id, nudge_id, *, actor):
        return {"study_id": study_id, "nudge_id": nudge_id, "status": "accepted", "decided_by": actor}
    def reject_nudge(self, study_id, nudge_id, *, actor, reason=None):
        return {"study_id": study_id, "nudge_id": nudge_id, "status": "rejected", "decided_by": actor, "decision_reason": reason}


class FakeValueChain:
    def list_studies(self): return [{"study_id": "s1", "pending_count": 1}]
    def study(self, study_id): return {"study_id": study_id, "use_cases": []}
    def prepare_request(self, payload): return {"status": "prepared", "payload": payload}


class FakeGraph:
    def company(self, study_id): return {"scope": {"kind": "company", "study_id": study_id}, "nodes": [], "edges": []}
    def sector(self, sector_code): return {"scope": {"kind": "sector", "sector_code": sector_code}, "nodes": [], "edges": []}


class FakeReach:
    def list_ready(self): return [{"study_id": "s1", "status": "ready"}]
    def preview(self, study_id): return {"study_id": study_id, "stakeholders": []}
    def prepare_request(self, payload): return {"status": "prepared", "payload": payload}


class FakeFollowUp:
    def items(self): return [{"id": "F1"}]


class FakeHeritage:
    def company(self, study_id): return {"scope": {"kind": "company", "study_id": study_id}, "graph": {"nodes": [], "edges": []}}
    def sector(self, sector_code): return {"scope": {"kind": "sector", "sector_code": sector_code}, "graph": {"nodes": [], "edges": []}}


class FakeWorkflows:
    def plan(self, payload): return {"kind": payload.get("kind"), "steps": []}


class FakeCatalogSearch:
    def search(self, query="", category="", status=""):
        return [{"offer_id": "OFFER-A", "matched_query": query, "category": category, "status": status}]


class FakeBlockerActions:
    def record(self, *, study_id, step_id, action, actor, reason=None, target_step_id=None):
        return {"study_id": study_id, "step_id": step_id, "action": action, "actor": actor, "reason": reason, "target_step_id": target_step_id, "timestamp": "2026-01-01T00:00:00+00:00"}

    def list_actions(self, study_id="", *, action=None, step_id=None, since=None, until=None):
        return [{
            "study_id": study_id, "action": action or "cancel", "step_id": step_id,
            "since": since, "until": until,
        }]


class FakeKanban:
    def build_board(self, root):
        return {"columns": [{"stage": "matching", "cards": [{"study_id": "s1"}]}]}


class FakeCampaigns:
    def list_campaigns(self, root):
        return [{"campaign_id": "CAMP-1", "kind": "prospecting"}]

    def launch_prospecting_campaign(self, root, *, name, criteria, actor):
        return {"campaign_id": "CAMP-2", "name": name, "criteria": criteria, "actor": actor, "target_count": 3, "status": "draft"}

    def prepare_cross_sell(self, root, *, study_id, actor):
        return {"nudging": {"study_id": study_id, "nudges": []}, "event": {"campaign_id": "XSELL-1", "study_id": study_id, "actor": actor}}

    def mark_campaign_sent(self, root, campaign_id, *, actor):
        return {"campaign_id": campaign_id, "status": "sent", "sent_by": actor, "sent_at": "2026-01-01T00:00:00+00:00"}


AUTH_CTX = RequestContext(
    user_id="u1", email="a@b.com", is_admin=True, role=None, workspace_id=None
)


class ServerV07Tests(unittest.TestCase):
    """Exercises app.server's FastAPI app in-process (ADR-007 §6 transport migration).

    The route/status/JSON-shape assertions below are unchanged from the
    stdlib-http.server era; only the client mechanism (Starlette's
    TestClient instead of raw http.client) and the authentication setup
    (every route but /api/health now requires a session, so we override
    the get_current_user dependency with a fixed admin identity) changed.
    """

    def setUp(self) -> None:
        self.patches = patch.multiple(
            server_module,
            CONTROL=FakeControl(), HARVESTER=FakeHarvester(), DEMAND=FakeDemand(),
            QUALIFICATION=FakeQualification(), NUDGING=FakeNudging(), VALUE_CHAIN=FakeValueChain(),
            UC_GRAPH=FakeGraph(), REACH=FakeReach(), FOLLOWUP=FakeFollowUp(),
            HERITAGE=FakeHeritage(), WORKFLOWS=FakeWorkflows(), BLOCKER_ACTIONS=FakeBlockerActions(),
            CATALOG_SEARCH=FakeCatalogSearch(),
            kanban=FakeKanban(), campaigns=FakeCampaigns(),
        )
        self.patches.start()
        self.env = patch.dict(os.environ, {"AI_DIAGNOSTIC_HTTP_LOG": "0"}, clear=False)
        self.env.start()
        server_module.APP.dependency_overrides[get_current_user] = lambda: AUTH_CTX
        self.client = TestClient(server_module.APP, raise_server_exceptions=False)

    def tearDown(self) -> None:
        server_module.APP.dependency_overrides.pop(get_current_user, None)
        self.env.stop()
        self.patches.stop()

    def request(self, method: str, path: str, payload=None, raw: bytes | None = None, headers=None):
        kwargs: dict = {"headers": dict(headers or {})}
        if raw is not None:
            kwargs["content"] = raw
        elif payload is not None:
            kwargs["content"] = json.dumps(payload).encode("utf-8")
            kwargs["headers"].setdefault("Content-Type", "application/json")
        response = self.client.request(method, path, **kwargs)
        content_type = response.headers.get("Content-Type") or ""
        data = response.json() if "application/json" in content_type and response.content else response.content
        return response.status_code, data, content_type

    def test_get_api_routes_and_static_assets(self) -> None:
        expected = {
            "/api/skills": list,
            "/api/offers": list,
            "/api/shelves": list,
            "/api/backlog": list,
            "/api/demand": dict,
            "/api/demand/inventories": list,
            "/api/qualification": list,
            "/api/nudging/inventories": list,
            "/api/value-chain": list,
            "/api/reach": list,
            "/api/follow-up": list,
            "/api/kanban/board": dict,
            "/api/campaigns": list,
        }
        for path, kind in expected.items():
            status, data, _ = self.request("GET", path)
            self.assertEqual(200, status, path)
            self.assertIsInstance(data, kind, path)
        status, health, _ = self.request("GET", "/api/health")
        self.assertEqual(200, status)
        self.assertEqual("0.7", health["version"])
        status, html, content_type = self.request("GET", "/")
        self.assertEqual(200, status)
        self.assertIn("text/html", content_type)
        self.assertIn(b"Control plane", html)
        status, js, content_type = self.request("GET", "/app.js")
        self.assertEqual(200, status)
        self.assertIn("javascript", content_type)
        self.assertIn(b"openWorkflow", js)
        status, _, _ = self.request("GET", "/missing")
        self.assertEqual(404, status)
        status, actions, _ = self.request("GET", "/api/qualification/actions?study_id=s1")
        self.assertEqual(200, status)
        self.assertIsInstance(actions, list)

    def test_catalog_search_route(self) -> None:
        status, data, _ = self.request("GET", "/api/catalog/search?q=agent&category=cat1&status=sourced")
        self.assertEqual(200, status)
        self.assertIsInstance(data, list)
        self.assertEqual(data[0]["matched_query"], "agent")
        self.assertEqual(data[0]["category"], "cat1")
        self.assertEqual(data[0]["status"], "sourced")

    def test_network_routes_return_empty_when_index_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(server_module, "NETWORK_INDEX_PATH", Path(tmp) / "missing.sqlite"):
                status, people, _ = self.request("GET", "/api/network/people")
                self.assertEqual(200, status)
                self.assertEqual(people, [])
                status, companies, _ = self.request("GET", "/api/network/companies")
                self.assertEqual(200, status)
                self.assertEqual(companies, [])

    def test_network_routes_search_built_index(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_root = Path(tmp) / "network"
            data_root.mkdir(parents=True)
            (data_root / "people.jsonl").write_text(
                json.dumps(
                    {
                        "person_id": "PERS-1",
                        "display_name": "Alice Martin",
                        "normalized_name": "alice martin",
                        "seed_company_id": "COMP-1",
                        "identity_confidence": "high",
                        "role_hypotheses": ["economic_sponsor"],
                        "status": "active",
                        "last_updated": "2026-08-01",
                        "stale_after_months": 6,
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (data_root / "companies.jsonl").write_text(
                json.dumps(
                    {
                        "company_id": "COMP-1",
                        "canonical_name": "EDF",
                        "normalized_name": "edf",
                        "status": "active",
                        "icb_mapping": {"sector": {"code": "651010"}},
                        "workspace_id": "acme-ws",
                        "last_updated": "2026-08-01",
                        "stale_after_months": 6,
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            index_path = Path(tmp) / "index.sqlite"
            network_index.rebuild(data_root, index_path)
            with patch.object(server_module, "NETWORK_INDEX_PATH", index_path):
                status, people, _ = self.request("GET", "/api/network/people?text=alice")
                self.assertEqual(200, status)
                self.assertEqual([p["person_id"] for p in people], ["PERS-1"])

                status, people, _ = self.request("GET", "/api/network/people?status=active&role=economic_sponsor")
                self.assertEqual(200, status)
                self.assertEqual(len(people), 1)

                status, people, _ = self.request("GET", "/api/network/people?company_id=COMP-1&stale=true")
                self.assertEqual(200, status)
                self.assertEqual(people, [])

                status, companies, _ = self.request("GET", "/api/network/companies?sector=651010")
                self.assertEqual(200, status)
                self.assertEqual([c["company_id"] for c in companies], ["COMP-1"])

                status, people, _ = self.request("GET", "/api/network/people?workspace_id=acme-ws")
                self.assertEqual(200, status)
                self.assertEqual([p["person_id"] for p in people], ["PERS-1"])

                status, people, _ = self.request("GET", "/api/network/people?workspace_id=default")
                self.assertEqual(200, status)
                self.assertEqual(people, [])

                status, companies, _ = self.request("GET", "/api/network/companies?workspace_id=acme-ws")
                self.assertEqual(200, status)
                self.assertEqual([c["company_id"] for c in companies], ["COMP-1"])

    def test_kanban_board_route(self) -> None:
        status, data, _ = self.request("GET", "/api/kanban/board")
        self.assertEqual(200, status)
        self.assertEqual([{"stage": "matching", "cards": [{"study_id": "s1"}]}], data["columns"])

    def test_campaigns_list_route(self) -> None:
        status, data, _ = self.request("GET", "/api/campaigns")
        self.assertEqual(200, status)
        self.assertEqual([{"campaign_id": "CAMP-1", "kind": "prospecting"}], data)

    def test_campaigns_prospecting_route(self) -> None:
        status, data, _ = self.request(
            "POST", "/api/campaigns/prospecting", {"name": "AI Leaders", "criteria": {"entity": "people", "text": "a"}}
        )
        self.assertEqual(201, status)
        self.assertEqual("AI Leaders", data["name"])
        self.assertEqual(AUTH_CTX.email, data["actor"])
        self.assertEqual(3, data["target_count"])

    def test_campaigns_cross_sell_route(self) -> None:
        status, data, _ = self.request("POST", "/api/campaigns/cross-sell", {"study_id": "s1"})
        self.assertEqual(201, status)
        self.assertEqual("s1", data["nudging"]["study_id"])
        self.assertEqual(AUTH_CTX.email, data["event"]["actor"])

    def test_campaigns_mark_sent_route(self) -> None:
        status, data, _ = self.request("POST", "/api/campaigns/CAMP-2/mark-sent")
        self.assertEqual(200, status)
        self.assertEqual("CAMP-2", data["campaign_id"])
        self.assertEqual("sent", data["status"])
        self.assertEqual(AUTH_CTX.email, data["sent_by"])

    def test_campaigns_mark_sent_route_requires_auth(self) -> None:
        server_module.APP.dependency_overrides.pop(get_current_user, None)
        status, _, _ = self.request("POST", "/api/campaigns/CAMP-2/mark-sent")
        self.assertEqual(401, status)

    def test_nudges_accept_route(self) -> None:
        status, data, _ = self.request("POST", "/api/nudges/NUD-1/accept", {"study_id": "s1"})
        self.assertEqual(200, status)
        self.assertEqual("NUD-1", data["nudge_id"])
        self.assertEqual("accepted", data["status"])
        self.assertEqual(AUTH_CTX.email, data["decided_by"])

    def test_nudges_reject_route(self) -> None:
        status, data, _ = self.request("POST", "/api/nudges/NUD-1/reject", {"study_id": "s1", "reason": "stale"})
        self.assertEqual(200, status)
        self.assertEqual("NUD-1", data["nudge_id"])
        self.assertEqual("rejected", data["status"])
        self.assertEqual(AUTH_CTX.email, data["decided_by"])
        self.assertEqual("stale", data["decision_reason"])

    def test_nudges_accept_route_requires_auth(self) -> None:
        server_module.APP.dependency_overrides.pop(get_current_user, None)
        status, _, _ = self.request("POST", "/api/nudges/NUD-1/accept", {"study_id": "s1"})
        self.assertEqual(401, status)

    def test_account_360_route_aggregates_and_404s_for_unknown_company(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_root = Path(tmp) / "network"
            data_root.mkdir(parents=True)
            (data_root / "companies.jsonl").write_text(
                json.dumps(
                    {
                        "company_id": "COMP-1",
                        "canonical_name": "EDF",
                        "normalized_name": "edf",
                        "status": "active",
                        "workspace_id": "default",
                        "last_updated": "2026-08-01",
                        "stale_after_months": 6,
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            index_path = Path(tmp) / "index.sqlite"
            network_index.rebuild(data_root, index_path)
            with patch.object(server_module, "NETWORK_INDEX_PATH", index_path):
                status, data, _ = self.request("GET", "/api/accounts/COMP-1/360")
                self.assertEqual(200, status)
                self.assertEqual(data["company"]["company_id"], "COMP-1")
                self.assertEqual(data["people"], [])

                status, _, _ = self.request("GET", "/api/accounts/UNKNOWN/360")
                self.assertEqual(404, status)

    def test_network_duplicates_route(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_root = Path(tmp) / "network"
            data_root.mkdir(parents=True)
            (data_root / "people.jsonl").write_text(
                "".join(
                    json.dumps(item) + "\n"
                    for item in [
                        {
                            "person_id": "PERS-1",
                            "display_name": "Jean Dupont",
                            "normalized_name": "jean dupont",
                            "seed_company_id": "COMP-1",
                            "identity_confidence": "high",
                            "role_hypotheses": [],
                            "status": "active",
                            "last_updated": "2026-08-01",
                            "stale_after_months": 6,
                        },
                        {
                            "person_id": "PERS-2",
                            "display_name": "Jean Dupont",
                            "normalized_name": "jean dupont",
                            "seed_company_id": "COMP-2",
                            "identity_confidence": "high",
                            "role_hypotheses": [],
                            "status": "active",
                            "last_updated": "2026-08-01",
                            "stale_after_months": 6,
                        },
                    ]
                ),
                encoding="utf-8",
            )
            (data_root / "companies.jsonl").write_text("", encoding="utf-8")
            index_path = Path(tmp) / "index.sqlite"
            network_index.rebuild(data_root, index_path)
            with patch.object(server_module, "NETWORK_INDEX_PATH", index_path):
                status, data, _ = self.request("GET", "/api/network/duplicates")
                self.assertEqual(200, status)
                self.assertEqual(len(data), 1)
                self.assertEqual(data[0]["normalized_name"], "jean dupont")

    def test_reassign_company_route_requires_admin(self) -> None:
        non_admin = RequestContext(user_id="u2", email="plain@b.com", is_admin=False, role="standard_user", workspace_id="ws1")
        server_module.APP.dependency_overrides[get_current_user] = lambda: non_admin
        status, _, _ = self.request("POST", "/admin/network/companies/C1/reassign", payload={"workspace_id": "ws-new"})
        self.assertEqual(403, status)

    def test_reassign_company_route_updates_company_for_admin(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_root = Path(tmp) / "network"
            data_root.mkdir(parents=True)
            (data_root / "companies.jsonl").write_text(
                json.dumps({"company_id": "C1", "canonical_name": "Acme", "workspace_id": "ws-old"}) + "\n",
                encoding="utf-8",
            )
            index_path = data_root / "network_index.sqlite"
            with patch.object(server_module, "NETWORK_INDEX_PATH", index_path):
                status, data, _ = self.request(
                    "POST", "/admin/network/companies/C1/reassign", payload={"workspace_id": "ws-new"}
                )
                self.assertEqual(200, status)
                self.assertEqual(data["company"]["workspace_id"], "ws-new")
                self.assertTrue(data["index_rebuild_required"])

                status, _, _ = self.request(
                    "POST", "/admin/network/companies/UNKNOWN/reassign", payload={"workspace_id": "ws-new"}
                )
                self.assertEqual(400, status)

    def test_network_rebuild_index_route_requires_admin(self) -> None:
        non_admin = RequestContext(user_id="u2", email="plain@b.com", is_admin=False, role="standard_user", workspace_id="ws1")
        server_module.APP.dependency_overrides[get_current_user] = lambda: non_admin
        status, _, _ = self.request("POST", "/admin/network/rebuild-index")
        self.assertEqual(403, status)

    def test_network_rebuild_index_route_builds_index_for_admin(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_root = Path(tmp) / "network"
            data_root.mkdir(parents=True)
            (data_root / "people.jsonl").write_text(
                json.dumps(
                    {
                        "person_id": "PERS-1",
                        "display_name": "Alice Martin",
                        "normalized_name": "alice martin",
                        "seed_company_id": "COMP-1",
                        "identity_confidence": "high",
                        "role_hypotheses": ["economic_sponsor"],
                        "status": "active",
                        "last_updated": "2026-08-01",
                        "stale_after_months": 6,
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (data_root / "companies.jsonl").write_text(
                json.dumps(
                    {
                        "company_id": "COMP-1",
                        "canonical_name": "EDF",
                        "normalized_name": "edf",
                        "status": "active",
                        "icb_mapping": {"sector": {"code": "651010"}},
                        "last_updated": "2026-08-01",
                        "stale_after_months": 6,
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            index_path = data_root / "index.sqlite"
            with patch.object(server_module, "NETWORK_INDEX_PATH", index_path):
                status, data, _ = self.request("POST", "/admin/network/rebuild-index")
            self.assertEqual(200, status)
            self.assertEqual(data["people"], 1)
            self.assertEqual(data["companies"], 1)
            self.assertEqual(data["relationships"], 0)

    def test_post_domain_routes(self) -> None:
        cases = [
            ("/api/skills/demo/invoke", {"input": "x"}, "prepared"),
            ("/api/catalog/harvest", {"company": "Acme", "persist": False}, "staged"),
            ("/api/catalog/discover", {"company": "Acme", "persist": True}, "discovered"),
            ("/api/nudging/generate", {"study_id": "s1"}, None),
            ("/api/value-chain/study", {"study_id": "s1"}, None),
            ("/api/value-chain/prepare", {"study_id": "s1", "use_case_id": "UC1"}, "prepared"),
            ("/api/uc-graph/company", {"study_id": "s1"}, None),
            ("/api/uc-graph/sector", {"sector_code": "301010"}, None),
            ("/api/heritage/company", {"study_id": "s1"}, None),
            ("/api/heritage/sector", {"sector_code": "301010"}, None),
            ("/api/reach/preview", {"study_id": "s1"}, None),
            ("/api/reach/prepare", {"study_id": "s1"}, "prepared"),
            ("/api/workflows/plan", {"kind": "qualification", "study_id": "s1"}, None),
            ("/api/qualification/actions", {"study_id": "s1", "step_id": "matching", "action": "cancel"}, None),
        ]
        for path, payload, expected_status in cases:
            status, data, _ = self.request("POST", path, payload)
            self.assertIn(status, {200, 201}, path)
            if expected_status:
                self.assertEqual(expected_status, data["status"], path)
        status, _, _ = self.request("POST", "/missing", {})
        self.assertEqual(404, status)

    def test_qualification_action_actor_comes_from_session_not_payload(self) -> None:
        status, data, _ = self.request(
            "POST",
            "/api/qualification/actions",
            {"study_id": "s1", "step_id": "matching", "action": "cancel", "actor": "spoofed@evil.com"},
        )
        self.assertEqual(201, status)
        self.assertEqual(AUTH_CTX.email, data["entry"]["actor"])

    def test_force_action_requires_product_owner_or_admin(self) -> None:
        non_owner = RequestContext(user_id="u2", email="plain@b.com", is_admin=False, role="standard_user", workspace_id="ws1")
        server_module.APP.dependency_overrides[get_current_user] = lambda: non_owner
        status, data, _ = self.request(
            "POST",
            "/api/qualification/actions",
            {"study_id": "s1", "step_id": "matching", "action": "force", "reason": "x"},
        )
        self.assertEqual(403, status)

    def test_unauthenticated_request_to_business_route_is_401(self) -> None:
        server_module.APP.dependency_overrides.pop(get_current_user, None)
        status, _, _ = self.request("GET", "/api/skills")
        self.assertEqual(401, status)

    def test_demand_intake_route_creates_profile(self) -> None:
        status, data, _ = self.request(
            "POST",
            "/api/demand/intake",
            {"company": "Acme Corp", "problem_statement": "We cannot see AI adoption ROI."},
        )
        self.assertEqual(201, status)
        self.assertEqual("s-new", data["study_id"])
        self.assertTrue(data["created_study"])

    def test_demand_intake_route_requires_auth(self) -> None:
        server_module.APP.dependency_overrides.pop(get_current_user, None)
        status, _, _ = self.request(
            "POST",
            "/api/demand/intake",
            {"company": "Acme Corp", "problem_statement": "x"},
        )
        self.assertEqual(401, status)

    def test_blocker_actions_route_returns_list_and_requires_auth(self) -> None:
        status, data, _ = self.request("GET", "/api/blocker-actions")
        self.assertEqual(200, status)
        self.assertIsInstance(data, list)
        server_module.APP.dependency_overrides.pop(get_current_user, None)
        status, _, _ = self.request("GET", "/api/blocker-actions")
        self.assertEqual(401, status)

    def test_blocker_actions_route_passes_filters_through(self) -> None:
        status, data, _ = self.request(
            "GET",
            "/api/blocker-actions?study_id=s1&action=force&step_id=reach&since=2026-01-01&until=2026-12-31",
        )
        self.assertEqual(200, status)
        self.assertEqual("s1", data[0]["study_id"])
        self.assertEqual("force", data[0]["action"])
        self.assertEqual("reach", data[0]["step_id"])
        self.assertEqual("2026-01-01", data[0]["since"])
        self.assertEqual("2026-12-31", data[0]["until"])

    def test_blocker_actions_route_resolves_company_id_to_study_id(self) -> None:
        status, data, _ = self.request("GET", "/api/blocker-actions?company_id=c1")
        self.assertEqual(200, status)
        self.assertEqual("s1", data[0]["study_id"])

    def test_blocker_actions_route_returns_empty_for_unknown_company_id(self) -> None:
        status, data, _ = self.request("GET", "/api/blocker-actions?company_id=unknown")
        self.assertEqual(200, status)
        self.assertEqual([], data)

    def test_health_route_is_open_without_authentication(self) -> None:
        server_module.APP.dependency_overrides.pop(get_current_user, None)
        status, health, _ = self.request("GET", "/api/health")
        self.assertEqual(200, status)
        self.assertEqual("0.7", health["version"])

    def test_invalid_json_and_persist_type_return_bad_request(self) -> None:
        status, data, _ = self.request("POST", "/api/nudging/generate", raw=b"not-json", headers={"Content-Type": "application/json"})
        self.assertEqual(400, status)
        self.assertIn("invalid JSON", data["error"])
        status, data, _ = self.request("POST", "/api/catalog/harvest", {"persist": "yes"})
        self.assertEqual(400, status)
        self.assertIn("persist must be a boolean", data["error"])
        status, data, _ = self.request("POST", "/api/catalog/discover", {"persist": 1})
        self.assertEqual(400, status)
        self.assertIn("persist must be a boolean", data["error"])

    def test_get_route_unexpected_exception_returns_clean_500(self) -> None:
        with patch.object(server_module, "logging") as mock_logging:
            with patch.object(server_module.DEMAND, "snapshot", side_effect=ValueError("boom")):
                status, data, content_type = self.request("GET", "/api/demand")
        self.assertEqual(500, status)
        self.assertIn("application/json", content_type)
        self.assertEqual("error", data["status"])
        self.assertNotIn("boom", data["error"])
        self.assertEqual("internal server error", data["error"])
        mock_logging.getLogger.return_value.exception.assert_called()

    def test_get_route_control_plane_error_returns_400(self) -> None:
        with patch.object(
            server_module.QUALIFICATION,
            "list_studies",
            side_effect=server_module.ControlPlaneError("bad qualification data"),
        ):
            status, data, _ = self.request("GET", "/api/qualification")
        self.assertEqual(400, status)
        self.assertEqual("error", data["status"])
        self.assertIn("bad qualification data", data["error"])

    def test_network_create_person_and_company_routes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_root = Path(tmp)
            index_path = data_root / "network" / "network_index.sqlite"
            with patch.object(server_module, "NETWORK_DATA_ROOT", data_root), patch.object(
                server_module, "NETWORK_INDEX_PATH", index_path
            ):
                status, company, _ = self.request(
                    "POST", "/api/network/companies", {"canonical_name": "Acme Corp"}
                )
                self.assertEqual(201, status)
                self.assertEqual(company["canonical_name"], "Acme Corp")

                status, person, _ = self.request(
                    "POST",
                    "/api/network/people",
                    {"display_name": "Jane Doe", "seed_company_id": company["company_id"]},
                )
                self.assertEqual(201, status)
                self.assertEqual(person["display_name"], "Jane Doe")
                self.assertEqual(person["seed_company_id"], company["company_id"])

    def test_network_create_person_is_immediately_searchable(self) -> None:
        # M1 regression: creating a person via the API must not require a
        # separate POST /admin/network/rebuild-index call before the record
        # shows up in GET /api/network/people search results.
        with tempfile.TemporaryDirectory() as tmp:
            data_root = Path(tmp)
            index_path = data_root / "network" / "network_index.sqlite"
            with patch.object(server_module, "NETWORK_DATA_ROOT", data_root), patch.object(
                server_module, "NETWORK_INDEX_PATH", index_path
            ):
                status, company, _ = self.request(
                    "POST", "/api/network/companies", {"canonical_name": "Beta Industries"}
                )
                self.assertEqual(201, status)

                status, person, _ = self.request(
                    "POST",
                    "/api/network/people",
                    {"display_name": "Zoe Lambert", "seed_company_id": company["company_id"]},
                )
                self.assertEqual(201, status)

                # No admin rebuild call in between -- search must already see it.
                status, people, _ = self.request("GET", "/api/network/people?text=Zoe")
                self.assertEqual(200, status)
                self.assertEqual([p["person_id"] for p in people], [person["person_id"]])

    def test_network_create_company_is_immediately_searchable(self) -> None:
        # M1 regression: same as above, for companies.
        with tempfile.TemporaryDirectory() as tmp:
            data_root = Path(tmp)
            index_path = data_root / "network" / "network_index.sqlite"
            with patch.object(server_module, "NETWORK_DATA_ROOT", data_root), patch.object(
                server_module, "NETWORK_INDEX_PATH", index_path
            ):
                status, company, _ = self.request(
                    "POST", "/api/network/companies", {"canonical_name": "Gamma Robotics"}
                )
                self.assertEqual(201, status)

                # No admin rebuild call in between -- search must already see it.
                status, companies, _ = self.request("GET", "/api/network/companies?text=Gamma")
                self.assertEqual(200, status)
                self.assertEqual([c["company_id"] for c in companies], [company["company_id"]])

    def test_network_create_person_unknown_company_is_400(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(server_module, "NETWORK_DATA_ROOT", Path(tmp)):
                status, data, _ = self.request(
                    "POST", "/api/network/people", {"display_name": "Jane Doe", "seed_company_id": "COMP-NOPE"}
                )
                self.assertEqual(400, status)
                self.assertEqual("error", data["status"])

    def test_catalog_promote_and_update_offer_routes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "catalog_sources").mkdir(parents=True)
            import yaml as _yaml

            (root / "catalog_sources" / "shelves.yaml").write_text(
                _yaml.safe_dump({"shelves": [{"shelf_id": "shelf-1"}]}), encoding="utf-8"
            )
            (root / "product_catalog").mkdir(parents=True)
            (root / "product_catalog" / "index.yaml").write_text(
                _yaml.safe_dump({"schema_version": "0.2", "offers": []}), encoding="utf-8"
            )
            with patch.object(server_module, "CONTROL", server_module.RepoControlPlane(root)):
                from app.catalog import CatalogHarvester

                harvest = CatalogHarvester(root).stage(
                    {
                        "company": "Widgetron Inc",
                        "shelf_id": "shelf-1",
                        "items": [{"name": "Widgetron", "source_url": "https://widgetron.example/"}],
                    }
                )
                candidate_id = f"{harvest['harvest']['harvest_id']}:CAND-001"

                status, offer, _ = self.request(
                    "POST",
                    f"/api/catalog/candidates/{candidate_id}/promote",
                    {"offer_id": "OFFER-WD-01"},
                )
                self.assertEqual(201, status)
                self.assertEqual(offer["offer_id"], "OFFER-WD-01")

                status, updated, _ = self.request(
                    "PATCH",
                    "/api/catalog/offers/OFFER-WD-01",
                    {"updates": {"positioning": {"one_liner": "revised"}}},
                )
                self.assertEqual(200, status)
                self.assertEqual(updated["positioning"]["one_liner"], "revised")

    def test_catalog_candidates_route_lists_staged_candidates(self) -> None:
        import tempfile
        import yaml as _yaml

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "catalog_sources").mkdir(parents=True)
            (root / "catalog_sources" / "shelves.yaml").write_text(
                _yaml.safe_dump({"shelves": [{"shelf_id": "shelf-1"}]}), encoding="utf-8"
            )
            (root / "product_catalog").mkdir(parents=True)
            (root / "product_catalog" / "index.yaml").write_text(
                _yaml.safe_dump({"schema_version": "0.2", "offers": []}), encoding="utf-8"
            )
            with patch.object(server_module, "CONTROL", server_module.RepoControlPlane(root)):
                status, empty, _ = self.request("GET", "/api/catalog/candidates")
                self.assertEqual(200, status)
                self.assertEqual(empty, [])

                from app.catalog import CatalogHarvester

                CatalogHarvester(root).stage(
                    {
                        "company": "Widgetron Inc",
                        "shelf_id": "shelf-1",
                        "items": [{"name": "Widgetron", "source_url": "https://widgetron.example/"}],
                    }
                )
                status, candidates, _ = self.request("GET", "/api/catalog/candidates")
                self.assertEqual(200, status)
                self.assertEqual(len(candidates), 1)
                self.assertEqual(candidates[0]["name"], "Widgetron")

                status, filtered, _ = self.request("GET", "/api/catalog/candidates?text=widget")
                self.assertEqual(200, status)
                self.assertEqual(len(filtered), 1)

                status, none_matched, _ = self.request("GET", "/api/catalog/candidates?text=nomatch")
                self.assertEqual(200, status)
                self.assertEqual(none_matched, [])

                status, by_shelf, _ = self.request("GET", "/api/catalog/candidates?shelf_id=shelf-1")
                self.assertEqual(200, status)
                self.assertEqual(len(by_shelf), 1)

                candidate_id = candidates[0]["id"]
                status, detail, _ = self.request(
                    "GET", f"/api/catalog/candidates/{candidate_id}"
                )
                self.assertEqual(200, status)
                self.assertEqual(detail["id"], candidate_id)
                self.assertEqual(detail["name"], "Widgetron")
                self.assertIn("raw_claims", detail)

                status, missing, _ = self.request("GET", "/api/catalog/candidates/bogus:CAND-999")
                self.assertEqual(400, status)

    def test_catalog_update_offer_requires_product_owner_or_admin(self) -> None:
        non_owner = RequestContext(user_id="u2", email="plain@b.com", is_admin=False, role="standard_user", workspace_id="ws1")
        server_module.APP.dependency_overrides[get_current_user] = lambda: non_owner
        status, _, _ = self.request(
            "PATCH", "/api/catalog/offers/OFFER-WD-01", {"updates": {"positioning": {}}}
        )
        self.assertEqual(403, status)

    def test_json_body_must_be_object(self) -> None:
        raw = json.dumps([1, 2]).encode("utf-8")
        response = self.client.post("/api/nudging/generate", content=raw, headers={"Content-Type": "application/json"})
        data = response.json()
        self.assertEqual(400, response.status_code)
        self.assertIn("must be an object", data["error"])


if __name__ == "__main__":
    unittest.main()
