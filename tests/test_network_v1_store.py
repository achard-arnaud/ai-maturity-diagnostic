from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.network_v1_store import EntityNotFound, get_entity, list_entities, put_entity


def _person(entity_id: str) -> dict:
    return {
        "entity_id": entity_id,
        "legacy_ids": [f"PERS-{entity_id}"],
        "display_name": f"Person {entity_id}",
        "workspace_id": "ws-a",
        "valid_from": "2026-01-01",
        "valid_to": None,
        "status": "active",
        "merged_into_entity_id": None,
        "provenance": {"source_refs": [], "epistemic_status": "inference", "evidence_grade": "U1"},
        "last_updated": "2026-01-01",
        "stale_after_months": 6,
    }


class NetworkV1StoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_put_then_get_round_trips(self) -> None:
        put_entity(self.root, "ws-a", "person", _person("e1"))
        record = get_entity(self.root, "ws-a", "person", "e1")
        self.assertEqual("Person e1", record["display_name"])

    def test_get_missing_entity_raises(self) -> None:
        with self.assertRaises(EntityNotFound):
            get_entity(self.root, "ws-a", "person", "nope")

    def test_put_is_upsert_keyed_on_entity_id(self) -> None:
        put_entity(self.root, "ws-a", "person", _person("e1"))
        updated = _person("e1")
        updated["display_name"] = "Renamed"
        put_entity(self.root, "ws-a", "person", updated)
        record = get_entity(self.root, "ws-a", "person", "e1")
        self.assertEqual("Renamed", record["display_name"])
        page = list_entities(self.root, "ws-a", "person")
        self.assertEqual(1, len(page.items))

    def test_workspaces_are_isolated(self) -> None:
        put_entity(self.root, "ws-a", "person", _person("e1"))
        with self.assertRaises(EntityNotFound):
            get_entity(self.root, "ws-b", "person", "e1")

    def test_pagination_returns_cursor_when_more_remain(self) -> None:
        for i in range(5):
            put_entity(self.root, "ws-a", "person", _person(f"e{i}"))
        page = list_entities(self.root, "ws-a", "person", limit=2)
        self.assertEqual(2, len(page.items))
        self.assertIsNotNone(page.next_cursor)
        next_page = list_entities(self.root, "ws-a", "person", limit=2, cursor=page.next_cursor)
        self.assertEqual(2, len(next_page.items))
        self.assertNotEqual(page.items, next_page.items)

    def test_last_page_has_no_next_cursor(self) -> None:
        for i in range(3):
            put_entity(self.root, "ws-a", "person", _person(f"e{i}"))
        page = list_entities(self.root, "ws-a", "person", limit=10)
        self.assertEqual(3, len(page.items))
        self.assertIsNone(page.next_cursor)


if __name__ == "__main__":
    unittest.main()
