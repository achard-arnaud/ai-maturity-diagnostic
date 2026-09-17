from __future__ import annotations

import copy
import unittest

from app.insights_metrics import CohortPolicy
from app.insights_projection import build_projection, reconcile_projection


def event(event_id: str, event_type: str, data: dict | None = None) -> dict:
    return {"event_id": event_id, "event_hash": f"hash-{event_id}", "event_type": event_type, "workspace_id": "ws-a", "occurred_at": f"2026-08-{int(event_id):02d}T10:00:00Z", "data": {"source": "outbound", **(data or {})}}


class InsightsProjectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = CohortPolicy("august-outbound", "ws-a", "2026-08-01T00:00:00Z", "2026-09-01T00:00:00Z", (("source", "outbound"),))
        self.events = [
            event("1", "journey.started"),
            event("2", "journey.started"),
            event("3", "journey.completed"),
            event("4", "quality.checked", {"passed": True}),
            event("5", "quality.checked", {"passed": False}),
            event("6", "execution.completed", {"cost_units": 2.5}),
        ]

    def test_projection_demonstrates_cohort_cost_quality_and_funnel(self) -> None:
        projection = build_projection(reversed(self.events), self.policy)
        metrics = {item["metric_id"]: item for item in projection["metrics"]}
        self.assertEqual(0.5, metrics["funnel_completion_rate"]["value"])
        self.assertEqual(0.5, metrics["quality_pass_rate"]["value"])
        self.assertEqual(2.5, metrics["execution_cost"]["value"])
        self.assertFalse(projection["authoritative"])

    def test_replay_is_order_independent_and_reconciles(self) -> None:
        first = build_projection(self.events, self.policy)
        second = build_projection(reversed(self.events), self.policy)
        self.assertEqual(first, second)
        self.assertTrue(reconcile_projection(first, self.events, self.policy))
        changed = copy.deepcopy(first); changed["metrics"][0]["value"] = 99
        self.assertFalse(reconcile_projection(changed, self.events, self.policy))


if __name__ == "__main__":
    unittest.main()
