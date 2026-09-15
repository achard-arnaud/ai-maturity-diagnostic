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

    def test_search_users_no_filters_returns_everyone(self) -> None:
        self.store.get_or_create_user("alice@example.com", "Alice")
        self.store.get_or_create_user("bob@example.com", "Bob")
        results = self.store.search_users()
        emails = {u["email"] for u in results}
        self.assertEqual(emails, {"alice@example.com", "bob@example.com"})

    def test_search_users_text_filter_matches_email_substring(self) -> None:
        self.store.get_or_create_user("alice@example.com", "Alice")
        self.store.get_or_create_user("bob@example.com", "Bob")
        results = self.store.search_users(text="ali")
        emails = {u["email"] for u in results}
        self.assertEqual(emails, {"alice@example.com"})

    def test_search_users_role_filter_admin(self) -> None:
        admin = self.store.get_or_create_user("admin@example.com", "Admin")
        self.store.set_admin(admin["id"], True)
        self.store.get_or_create_user("plain@example.com", "Plain")
        results = self.store.search_users(role="admin")
        emails = {u["email"] for u in results}
        self.assertEqual(emails, {"admin@example.com"})

    def test_search_users_role_filter_product_owner(self) -> None:
        ws = self.store.create_workspace("ws-po", "Workspace PO")
        po = self.store.get_or_create_user("po@example.com", "PO")
        self.store.set_membership(po["id"], ws["id"], "product_owner")
        self.store.get_or_create_user("standard@example.com", "Standard")
        results = self.store.search_users(role="product_owner")
        emails = {u["email"] for u in results}
        self.assertEqual(emails, {"po@example.com"})

    def test_search_users_role_filter_standard_user(self) -> None:
        ws = self.store.create_workspace("ws-std", "Workspace Std")
        std = self.store.get_or_create_user("std@example.com", "Std")
        self.store.set_membership(std["id"], ws["id"], "standard_user")
        self.store.get_or_create_user("other@example.com", "Other")
        results = self.store.search_users(role="standard_user")
        emails = {u["email"] for u in results}
        self.assertEqual(emails, {"std@example.com"})

    def test_search_users_workspace_id_filter(self) -> None:
        ws_a = self.store.create_workspace("ws-search-a", "Workspace Search A")
        ws_b = self.store.create_workspace("ws-search-b", "Workspace Search B")
        user_a = self.store.get_or_create_user("a@example.com", "A")
        user_b = self.store.get_or_create_user("b@example.com", "B")
        self.store.set_membership(user_a["id"], ws_a["id"], "standard_user")
        self.store.set_membership(user_b["id"], ws_b["id"], "standard_user")
        results = self.store.search_users(workspace_id="ws-search-a")
        emails = {u["email"] for u in results}
        self.assertEqual(emails, {"a@example.com"})

    def test_search_users_combined_filters(self) -> None:
        ws = self.store.create_workspace("ws-combo", "Workspace Combo")
        match = self.store.get_or_create_user("match@example.com", "Match")
        self.store.set_membership(match["id"], ws["id"], "product_owner")
        no_role_match = self.store.get_or_create_user("matchtoo@example.com", "MatchToo")
        self.store.set_membership(no_role_match["id"], ws["id"], "standard_user")
        other_ws = self.store.create_workspace("ws-combo-other", "Other Combo")
        wrong_ws = self.store.get_or_create_user("matchwrongws@example.com", "WrongWs")
        self.store.set_membership(wrong_ws["id"], other_ws["id"], "product_owner")

        results = self.store.search_users(text="match", role="product_owner", workspace_id="ws-combo")
        emails = {u["email"] for u in results}
        self.assertEqual(emails, {"match@example.com"})

    def test_override_recorded_and_listed_by_workspace(self) -> None:
        self.store.create_workspace("ws-c", "Workspace C")
        override_id = self.store.record_override("ws-c", "study-1:demand", "po@example.com", "Deal is time-boxed by exec sponsor")
        self.assertIsInstance(override_id, int)
        rows = self.store.list_overrides("ws-c")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["reason"], "Deal is time-boxed by exec sponsor")
        self.assertEqual(self.store.list_overrides("ws-does-not-exist"), [])


    def test_list_overrides_across_workspaces_for_admin(self) -> None:
        self.store.create_workspace("ws-inbox-a", "Workspace Inbox A")
        self.store.create_workspace("ws-inbox-b", "Workspace Inbox B")
        self.store.record_override("ws-inbox-a", "study-a:demand", "po-a@example.com", "reason a")
        self.store.record_override("ws-inbox-b", "study-b:matching", "po-b@example.com", "reason b")

        all_rows = self.store.list_overrides()
        blocker_ids = {row["blocker_id"] for row in all_rows}
        self.assertIn("study-a:demand", blocker_ids)
        self.assertIn("study-b:matching", blocker_ids)

    def test_list_overrides_filters_by_workspace_id(self) -> None:
        self.store.create_workspace("ws-inbox-c", "Workspace Inbox C")
        self.store.create_workspace("ws-inbox-d", "Workspace Inbox D")
        self.store.record_override("ws-inbox-c", "study-c:demand", "po-c@example.com", "reason c")
        self.store.record_override("ws-inbox-d", "study-d:demand", "po-d@example.com", "reason d")

        rows = self.store.list_overrides(workspace_id="ws-inbox-c")
        self.assertEqual([row["workspace_id"] for row in rows], ["ws-inbox-c"])

    def test_list_overrides_resolved_filter_has_no_open_closed_concept(self) -> None:
        """Documented finding: the overrides table has no resolved/open
        column, so `resolved=False` cannot return a genuine open queue --
        it returns [] (nothing is trackable as unresolved), and
        `resolved=True`/None both return every recorded override."""
        self.store.create_workspace("ws-inbox-e", "Workspace Inbox E")
        self.store.record_override("ws-inbox-e", "study-e:demand", "po-e@example.com", "reason e")

        self.assertEqual(self.store.list_overrides(workspace_id="ws-inbox-e", resolved=False), [])
        rows_true = self.store.list_overrides(workspace_id="ws-inbox-e", resolved=True)
        rows_none = self.store.list_overrides(workspace_id="ws-inbox-e", resolved=None)
        self.assertEqual(len(rows_true), 1)
        self.assertEqual(len(rows_none), 1)


if __name__ == "__main__":
    unittest.main()
