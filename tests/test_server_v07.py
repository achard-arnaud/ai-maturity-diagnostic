from __future__ import annotations

import json
import os
import unittest
from unittest.mock import patch

from starlette.testclient import TestClient

from app import server as server_module
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


class FakeQualification:
    def list_studies(self): return [{"study_id": "s1"}]


class FakeNudging:
    def list_inventories(self): return [{"study_id": "s1"}]
    def generate_request(self, payload): return {"nudges": [], "payload": payload}


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


class FakeBlockerActions:
    def record(self, *, study_id, step_id, action, actor, reason=None, target_step_id=None):
        return {"study_id": study_id, "step_id": step_id, "action": action, "actor": actor, "reason": reason, "target_step_id": target_step_id, "timestamp": "2026-01-01T00:00:00+00:00"}

    def list_actions(self, study_id):
        return [{"study_id": study_id, "action": "cancel"}]


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
        with patch.object(server_module.DEMAND, "snapshot", side_effect=ValueError("boom")):
            status, data, content_type = self.request("GET", "/api/demand")
        self.assertEqual(500, status)
        self.assertIn("application/json", content_type)
        self.assertEqual("error", data["status"])
        self.assertIn("boom", data["error"])

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

    def test_json_body_must_be_object(self) -> None:
        raw = json.dumps([1, 2]).encode("utf-8")
        response = self.client.post("/api/nudging/generate", content=raw, headers={"Content-Type": "application/json"})
        data = response.json()
        self.assertEqual(400, response.status_code)
        self.assertIn("must be an object", data["error"])


if __name__ == "__main__":
    unittest.main()
