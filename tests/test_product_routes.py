from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from starlette.testclient import TestClient

from app.authruntime.app import create_app
from app.authruntime.config import AuthConfig
from app.authruntime.db import ControlStore
from app.product_diff import diff_snapshot_content
from app.product_policy import compute_content_hash
from app.product_routes import create_v1_product_router
from app.product_snapshot_store import put_snapshot
from app.product_store import put_product


def _content(**kwargs) -> dict:
    base = {"name": "Acme", "description": "Core", "exclusions": [], "hard_gates": [], "capabilities": []}
    base.update(kwargs)
    return base


def _shared_snapshot(snapshot_id: str, product_id: str, **content_kwargs) -> dict:
    content = _content(**content_kwargs)
    return {
        "snapshot_id": snapshot_id,
        "product_id": product_id,
        "product_version_id": f"{snapshot_id}-v",
        "owner_scope": {"kind": "shared", "workspace_id": None},
        "content": content,
        "content_hash": compute_content_hash(content),
        "published_at": "2026-01-01T00:00:00+00:00",
        "evidence_ids": [],
        "supersedes_snapshot_id": None,
    }


def _workspace_product(product_id: str, workspace_id: str) -> dict:
    return {
        "product_id": product_id,
        "owner_scope": {"kind": "workspace", "workspace_id": workspace_id},
        "name": "WS Product",
        "status": "active",
        "created_at": "2026-01-01T00:00:00+00:00",
        "overlay_of_product_id": None,
    }


class ProductRoutesTests(unittest.TestCase):
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

        put_product(self.root, {
            "product_id": "p-shared", "owner_scope": {"kind": "shared", "workspace_id": None},
            "name": "Shared Product", "status": "active",
            "created_at": "2026-01-01T00:00:00+00:00", "overlay_of_product_id": None,
        })
        put_product(self.root, _workspace_product("p-a", "ws-a"))
        put_snapshot(self.root, _shared_snapshot("snap1", "p-shared", description="v1"))
        put_snapshot(self.root, _shared_snapshot("snap2", "p-shared", description="v2"))

        app = create_app(control_store=self.store, oidc_client=None, config=self.config)
        app.include_router(create_v1_product_router(self.root))
        self.client = TestClient(app)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _cookie(self, token: str) -> dict:
        return {"aimd_session": token}

    def test_unauthenticated_is_401(self) -> None:
        response = self.client.get("/api/v1/workspaces/ws-a/products")
        self.assertEqual(401, response.status_code)

    def test_list_shows_shared_and_own_workspace_products_only(self) -> None:
        response = self.client.get("/api/v1/workspaces/ws-a/products", cookies=self._cookie(self.alice_token))
        ids = {p["product_id"] for p in response.json()["items"]}
        self.assertEqual({"p-shared", "p-a"}, ids)

    def test_other_workspace_product_is_404_for_a_different_workspace(self) -> None:
        response = self.client.get("/api/v1/workspaces/ws-b/products/p-a", cookies=self._cookie(self.bob_token))
        self.assertEqual(404, response.status_code)

    def test_shared_product_deep_link_is_stable_across_requests(self) -> None:
        first = self.client.get("/api/v1/workspaces/ws-a/products/p-shared", cookies=self._cookie(self.alice_token))
        second = self.client.get("/api/v1/workspaces/ws-a/products/p-shared", cookies=self._cookie(self.alice_token))
        self.assertEqual(200, first.status_code)
        self.assertEqual(first.json(), second.json())

    def test_snapshot_deep_link_is_stable_across_requests(self) -> None:
        first = self.client.get(
            "/api/v1/workspaces/ws-a/products/p-shared/snapshots/snap1", cookies=self._cookie(self.alice_token)
        )
        second = self.client.get(
            "/api/v1/workspaces/ws-a/products/p-shared/snapshots/snap1", cookies=self._cookie(self.alice_token)
        )
        self.assertEqual(200, first.status_code)
        self.assertEqual(first.json(), second.json())
        self.assertEqual("v1", first.json()["content"]["description"])

    def test_unknown_snapshot_is_404(self) -> None:
        response = self.client.get(
            "/api/v1/workspaces/ws-a/products/p-shared/snapshots/nope", cookies=self._cookie(self.alice_token)
        )
        self.assertEqual(404, response.status_code)

    def test_diff_route_matches_pure_function(self) -> None:
        response = self.client.get(
            "/api/v1/workspaces/ws-a/products/p-shared/diff",
            params={"from_snapshot_id": "snap1", "to_snapshot_id": "snap2"},
            cookies=self._cookie(self.alice_token),
        )
        self.assertEqual(200, response.status_code)
        expected = diff_snapshot_content(_content(description="v1"), _content(description="v2"))
        self.assertEqual(expected, response.json()["diff"])


if __name__ == "__main__":
    unittest.main()
