from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.engagement_store import (
    ConversationNotFound,
    get_conversation,
    list_conversations,
    list_events_for_conversation,
    list_objections_for_event,
    put_conversation,
    put_engagement_event,
    put_objection,
)


def _conversation(conversation_id: str, status: str = "open") -> dict:
    return {
        "conversation_id": conversation_id, "workspace_id": "ws-a", "target_plan_id": "tp1",
        "stakeholder_role_id": "sr1", "sequence_id": "seq1", "status": status,
        "created_at": "2026-01-01T00:00:00Z",
    }


def _event(engagement_event_id: str, conversation_id: str, occurred_at: str = "2026-01-01T00:00:00Z") -> dict:
    return {
        "engagement_event_id": engagement_event_id, "conversation_id": conversation_id,
        "touchpoint_id": None, "kind": "replied", "channel": "email", "occurred_at": occurred_at,
        "source_ref": f"src-{engagement_event_id}", "raw_ref": None,
    }


def _objection(objection_id: str, engagement_event_id: str) -> dict:
    return {
        "objection_id": objection_id, "engagement_event_id": engagement_event_id, "category": "price",
        "confidence": 0.5, "status": "draft", "raised_at": "2026-01-01T00:00:00Z",
        "reviewed_by": None, "reviewed_at": None,
    }


class EngagementStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_put_and_get_conversation(self) -> None:
        put_conversation(self.root, "ws-a", _conversation("c1"))
        record = get_conversation(self.root, "ws-a", "c1")
        self.assertEqual("c1", record["conversation_id"])

    def test_get_missing_conversation_raises(self) -> None:
        with self.assertRaises(ConversationNotFound):
            get_conversation(self.root, "ws-a", "missing")

    def test_list_conversations_filters_by_status(self) -> None:
        put_conversation(self.root, "ws-a", _conversation("c1", status="open"))
        put_conversation(self.root, "ws-a", _conversation("c2", status="closed"))
        page = list_conversations(self.root, "ws-a", status="open")
        self.assertEqual(["c1"], [c["conversation_id"] for c in page.items])

    def test_list_conversations_workspace_isolated(self) -> None:
        put_conversation(self.root, "ws-a", _conversation("c1"))
        page = list_conversations(self.root, "ws-b")
        self.assertEqual([], page.items)

    def test_events_ordered_by_occurred_at(self) -> None:
        put_engagement_event(self.root, "ws-a", _event("ee2", "c1", occurred_at="2026-01-02T00:00:00Z"))
        put_engagement_event(self.root, "ws-a", _event("ee1", "c1", occurred_at="2026-01-01T00:00:00Z"))
        events = list_events_for_conversation(self.root, "ws-a", "c1")
        self.assertEqual(["ee1", "ee2"], [e["engagement_event_id"] for e in events])

    def test_objections_scoped_to_event(self) -> None:
        put_objection(self.root, "ws-a", _objection("o1", "ee1"))
        put_objection(self.root, "ws-a", _objection("o2", "ee2"))
        objections = list_objections_for_event(self.root, "ws-a", "ee1")
        self.assertEqual(["o1"], [o["objection_id"] for o in objections])


if __name__ == "__main__":
    unittest.main()
