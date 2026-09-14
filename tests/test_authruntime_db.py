from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.authruntime.db import DEFAULT_WORKSPACE_ID, ControlStore


class ControlStoreSchemaTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.store = ControlStore(Path(self._tmp.name) / "control.sqlite3")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_init_creates_default_workspace(self) -> None:
        workspaces = self.store.list_workspaces()
        ids = {w["id"] for w in workspaces}
        self.assertIn(DEFAULT_WORKSPACE_ID, ids)

    def test_init_is_idempotent(self) -> None:
        self.store.init_schema()
        self.store.init_schema()
        ids = [w["id"] for w in self.store.list_workspaces()]
        self.assertEqual(ids.count(DEFAULT_WORKSPACE_ID), 1)

    def test_get_or_create_user_dedupes_by_email(self) -> None:
        first = self.store.get_or_create_user("alice@example.com", "Alice")
        second = self.store.get_or_create_user("alice@example.com", "Alice Again")
        self.assertEqual(first["id"], second["id"])

    def test_membership_is_exactly_one_workspace_per_user(self) -> None:
        user = self.store.get_or_create_user("bob@example.com", "Bob")
        ws_a = self.store.create_workspace("ws-a", "Workspace A")
        ws_b = self.store.create_workspace("ws-b", "Workspace B")
        self.store.set_membership(user["id"], ws_a["id"], "product_owner")
        self.store.set_membership(user["id"], ws_b["id"], "standard_user")
        membership = self.store.get_membership(user["id"])
        self.assertEqual(membership["workspace_id"], "ws-b")
        self.assertEqual(membership["role"], "standard_user")

    def test_membership_rejects_invalid_role(self) -> None:
        user = self.store.get_or_create_user("carol@example.com", "Carol")
        with self.assertRaises(ValueError):
            self.store.set_membership(user["id"], DEFAULT_WORKSPACE_ID, "admin")

    def test_session_lifecycle(self) -> None:
        user = self.store.get_or_create_user("dave@example.com", "Dave")
        token = self.store.create_session(user["id"], ttl_hours=1)
        row = self.store.get_session_user(token)
        self.assertIsNotNone(row)
        self.assertEqual(row["email"], "dave@example.com")

        self.store.revoke_session(token)
        self.assertIsNone(self.store.get_session_user(token))

    def test_expired_session_is_rejected(self) -> None:
        user = self.store.get_or_create_user("erin@example.com", "Erin")
        token = self.store.create_session(user["id"], ttl_hours=-1)
        self.assertIsNone(self.store.get_session_user(token))

    def test_unknown_session_token_is_rejected(self) -> None:
        self.assertIsNone(self.store.get_session_user("does-not-exist"))

    def test_audit_events_are_append_only_ordered(self) -> None:
        self.store.record_audit("admin@example.com", "create_workspace", "ws-a", None)
        self.store.record_audit("admin@example.com", "set_membership", "u1->ws-a:product_owner", None)
        events = self.store.list_audit()
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0]["action"], "set_membership")  # most recent first

    def test_override_recorded_and_listed_by_workspace(self) -> None:
        self.store.create_workspace("ws-c", "Workspace C")
        override_id = self.store.record_override("ws-c", "study-1:demand", "po@example.com", "Deal is time-boxed by exec sponsor")
        self.assertIsInstance(override_id, int)
        rows = self.store.list_overrides("ws-c")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["reason"], "Deal is time-boxed by exec sponsor")
        self.assertEqual(self.store.list_overrides("ws-does-not-exist"), [])


if __name__ == "__main__":
    unittest.main()
