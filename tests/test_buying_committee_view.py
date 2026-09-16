from __future__ import annotations

import unittest

from app.buying_committee_view import build_committee_graph


def _stakeholder(sid: str, role: str = "sponsor") -> dict:
    return {"stakeholder_role_id": sid, "role": role, "person_entity_id": f"entity_{sid}", "status": "active"}


class BuildCommitteeGraphTests(unittest.TestCase):
    def test_nodes_include_every_stakeholder(self) -> None:
        stakeholders = [_stakeholder("sr1"), _stakeholder("sr2", "champion")]
        graph = build_committee_graph(stakeholders, {})
        self.assertEqual(2, len(graph["nodes"]))

    def test_node_fields_come_only_from_input(self) -> None:
        stakeholders = [_stakeholder("sr1")]
        graph = build_committee_graph(stakeholders, {})
        node = graph["nodes"][0]
        self.assertEqual({"id", "role", "person_entity_id", "status"}, set(node.keys()))

    def test_no_edge_without_warm_path(self) -> None:
        stakeholders = [_stakeholder("sr1")]
        influences = {"sr1": {"warm_path": None, "confidence": "unknown"}}
        graph = build_committee_graph(stakeholders, influences)
        self.assertEqual([], graph["edges"])

    def test_edge_created_when_warm_path_present(self) -> None:
        stakeholders = [_stakeholder("sr1")]
        influences = {"sr1": {"warm_path": "mutual contact Bob", "confidence": "high"}}
        graph = build_committee_graph(stakeholders, influences)
        self.assertEqual(1, len(graph["edges"]))
        self.assertEqual("sr1", graph["edges"][0]["to"])
        self.assertEqual("high", graph["edges"][0]["confidence"])


class DeterminismTests(unittest.TestCase):
    """Stop condition: 'projection sans new truth' -- same underlying
    data, regardless of input order, always produces byte-identical
    output."""

    def test_node_order_is_independent_of_input_order(self) -> None:
        forward = [_stakeholder("sr1"), _stakeholder("sr2"), _stakeholder("sr3")]
        reversed_input = list(reversed(forward))
        graph_a = build_committee_graph(forward, {})
        graph_b = build_committee_graph(reversed_input, {})
        self.assertEqual(graph_a, graph_b)

    def test_edge_order_is_independent_of_input_order(self) -> None:
        stakeholders = [_stakeholder("sr1"), _stakeholder("sr2")]
        influences = {
            "sr1": {"warm_path": "path A", "confidence": "high"},
            "sr2": {"warm_path": "path B", "confidence": "medium"},
        }
        graph_a = build_committee_graph(stakeholders, influences)
        graph_b = build_committee_graph(list(reversed(stakeholders)), influences)
        self.assertEqual(graph_a, graph_b)

    def test_repeated_calls_are_identical(self) -> None:
        stakeholders = [_stakeholder("sr1")]
        influences = {"sr1": {"warm_path": "path A", "confidence": "high"}}
        self.assertEqual(
            build_committee_graph(stakeholders, influences),
            build_committee_graph(stakeholders, influences),
        )


if __name__ == "__main__":
    unittest.main()
