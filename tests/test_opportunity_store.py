from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.opportunity_store import OpportunityNotFound, build_pipeline_board, get_opportunity, list_opportunities, put_opportunity


def _opportunity(identifier: str, status: str = "draft", workspace_id: str = "ws-a") -> dict:
    return {"opportunity_id": identifier, "workspace_id": workspace_id, "status": status}


class OpportunityStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_workspace_isolation_and_not_found(self) -> None:
        put_opportunity(self.root, "ws-a", _opportunity("opp-1"))
        self.assertEqual("opp-1", get_opportunity(self.root, "ws-a", "opp-1")["opportunity_id"])
        with self.assertRaises(OpportunityNotFound):
            get_opportunity(self.root, "ws-b", "opp-1")

    def test_filter_pagination_and_stable_board(self) -> None:
        put_opportunity(self.root, "ws-a", _opportunity("opp-b", "discovery"))
        put_opportunity(self.root, "ws-a", _opportunity("opp-a", "discovery"))
        put_opportunity(self.root, "ws-a", _opportunity("opp-c", "proof"))
        page = list_opportunities(self.root, "ws-a", stage="discovery", limit=1)
        self.assertEqual(["opp-a"], [record["opportunity_id"] for record in page.items])
        self.assertEqual("opp-a", page.next_cursor)
        board = build_pipeline_board(self.root, "ws-a")
        self.assertEqual(["opp-a", "opp-b"], [record["opportunity_id"] for record in board["discovery"]])
        self.assertEqual([], board["proposal"])

    def test_write_cannot_cross_workspace(self) -> None:
        with self.assertRaisesRegex(ValueError, "workspace"):
            put_opportunity(self.root, "ws-a", _opportunity("opp-1", workspace_id="ws-b"))


if __name__ == "__main__":
    unittest.main()
