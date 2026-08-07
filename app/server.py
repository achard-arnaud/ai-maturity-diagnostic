from __future__ import annotations

import json
import mimetypes
import os
import subprocess
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from app.catalog import CatalogHarvester
from app.core import ControlPlaneError, RepoControlPlane
from app.demand import DemandCatalog
from app.nudging import UseCaseNudger
from app.qualification import QualificationCockpit
from app.workflows import WorkflowPlanner

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "app" / "frontend"
CONTROL = RepoControlPlane(ROOT)
HARVESTER = CatalogHarvester(ROOT)
DEMAND = DemandCatalog(ROOT)
QUALIFICATION = QualificationCockpit(ROOT)
NUDGING = UseCaseNudger(ROOT)
WORKFLOWS = WorkflowPlanner(ROOT)


class Handler(BaseHTTPRequestHandler):
    server_version = "AIMaturityDiagnostic/0.6"

    def _json(self, status: int, payload: Any) -> None:
        raw = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length < 0 or length > 1_000_000:
            raise ControlPlaneError("request body too large")
        raw = self.rfile.read(length) if length else b"{}"
        try:
            data = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ControlPlaneError("invalid JSON body") from exc
        if not isinstance(data, dict):
            raise ControlPlaneError("JSON body must be an object")
        return data

    def _static(self, name: str) -> None:
        target = (FRONTEND / name).resolve()
        try:
            target.relative_to(FRONTEND.resolve())
        except ValueError:
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        if not target.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        raw = target.read_bytes()
        content_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        if content_type.startswith("text/") or content_type == "application/javascript":
            content_type += "; charset=utf-8"
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/api/health":
            self._json(
                HTTPStatus.OK,
                {
                    "status": "ok",
                    "version": "0.6",
                    "executor_configured": bool(os.getenv("AI_DIAGNOSTIC_SKILL_EXECUTOR", "").strip()),
                },
            )
            return
        routes = {
            "/api/skills": CONTROL.list_skills,
            "/api/offers": CONTROL.list_offers,
            "/api/shelves": CONTROL.list_shelves,
            "/api/backlog": CONTROL.backlog,
            "/api/demand": DEMAND.snapshot,
            "/api/demand/inventories": DEMAND.inventories,
            "/api/qualification": QUALIFICATION.list_studies,
            "/api/nudging/inventories": NUDGING.list_inventories,
        }
        if path in routes:
            self._json(HTTPStatus.OK, routes[path]())
            return
        if path == "/":
            self._static("index.html")
            return
        if path in {"/app.js", "/styles.css"}:
            self._static(path[1:])
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        try:
            payload = self._body()
            if path.startswith("/api/skills/") and path.endswith("/invoke"):
                skill_id = path[len("/api/skills/") : -len("/invoke")].strip("/")
                self._json(HTTPStatus.OK, CONTROL.invoke(skill_id, payload))
                return
            if path == "/api/catalog/harvest":
                persist = payload.get("persist", True)
                if not isinstance(persist, bool):
                    raise ControlPlaneError("persist must be a boolean")
                self._json(HTTPStatus.CREATED, HARVESTER.stage(payload, persist=persist))
                return
            if path == "/api/catalog/discover":
                persist = payload.get("persist", True)
                if not isinstance(persist, bool):
                    raise ControlPlaneError("persist must be a boolean")
                self._json(HTTPStatus.CREATED, HARVESTER.discover_public(payload, persist=persist))
                return
            if path == "/api/nudging/generate":
                self._json(HTTPStatus.OK, NUDGING.generate_request(payload))
                return
            if path == "/api/workflows/plan":
                self._json(HTTPStatus.OK, WORKFLOWS.plan(payload))
                return
            self.send_error(HTTPStatus.NOT_FOUND)
        except ControlPlaneError as exc:
            self._json(HTTPStatus.BAD_REQUEST, {"status": "error", "error": str(exc)})
        except subprocess.TimeoutExpired:
            self._json(HTTPStatus.GATEWAY_TIMEOUT, {"status": "error", "error": "skill executor timed out"})

    def log_message(self, fmt: str, *args: object) -> None:
        if os.getenv("AI_DIAGNOSTIC_HTTP_LOG", "1") != "0":
            super().log_message(fmt, *args)


def main() -> None:
    host = os.getenv("AI_DIAGNOSTIC_HOST", "127.0.0.1")
    port = int(os.getenv("AI_DIAGNOSTIC_PORT", "8080"))
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"AI diagnostic control plane: http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
