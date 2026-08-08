from __future__ import annotations

import http.client
import json
import os
import threading
import unittest
from unittest.mock import patch

from app import server as server_module


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


class ServerV07Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.patches = patch.multiple(
            server_module,
            CONTROL=FakeControl(), HARVESTER=FakeHarvester(), DEMAND=FakeDemand(),
            QUALIFICATION=FakeQualification(), NUDGING=FakeNudging(), VALUE_CHAIN=FakeValueChain(),
            UC_GRAPH=FakeGraph(), REACH=FakeReach(), FOLLOWUP=FakeFollowUp(),
            HERITAGE=FakeHeritage(), WORKFLOWS=FakeWorkflows(),
        )
        self.patches.start()
        self.env = patch.dict(os.environ, {"AI_DIAGNOSTIC_HTTP_LOG": "0"}, clear=False)
        self.env.start()
        self.httpd = server_module.ThreadingHTTPServer(("127.0.0.1", 0), server_module.Handler)
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        self.port = self.httpd.server_address[1]

    def tearDown(self) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()
        self.thread.join(timeout=2)
        self.env.stop()
        self.patches.stop()

    def request(self, method: str, path: str, payload=None, raw: bytes | None = None, headers=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=3)
        body = raw
        request_headers = dict(headers or {})
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
            request_headers.setdefault("Content-Type", "application/json")
        conn.request(method, path, body=body, headers=request_headers)
        response = conn.getresponse()
        data = response.read()
        content_type = response.getheader("Content-Type") or ""
        conn.close()
        parsed = json.loads(data.decode("utf-8")) if "application/json" in content_type and data else data
        return response.status, parsed, content_type

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
        ]
        for path, payload, expected_status in cases:
            status, data, _ = self.request("POST", path, payload)
            self.assertIn(status, {200, 201}, path)
            if expected_status:
                self.assertEqual(expected_status, data["status"], path)
        status, _, _ = self.request("POST", "/missing", {})
        self.assertEqual(404, status)

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

    def test_json_body_must_be_object(self) -> None:
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=3)
        raw = json.dumps([1, 2]).encode("utf-8")
        conn.request("POST", "/api/nudging/generate", body=raw, headers={"Content-Type": "application/json"})
        response = conn.getresponse()
        data = json.loads(response.read().decode("utf-8"))
        conn.close()
        self.assertEqual(400, response.status)
        self.assertIn("must be an object", data["error"])


if __name__ == "__main__":
    unittest.main()
