from __future__ import annotations

import unittest

from app.insights_metrics import CohortPolicy, METRIC_CATALOG, MetricPolicyError, metric_catalog, select_cohort


class InsightsMetricTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = CohortPolicy(
            "august-fr-outbound",
            "ws-a",
            "2026-08-01T00:00:00Z",
            "2026-09-01T00:00:00Z",
            (("source", "outbound"), ("region", "fr")),
        )

    def test_catalog_definitions_are_unique_and_unambiguous(self) -> None:
        ids = [metric.metric_id for metric in METRIC_CATALOG]
        self.assertEqual(len(ids), len(set(ids)))
        for metric in metric_catalog():
            self.assertIn(metric["aggregation"], {"count", "sum", "boolean_rate"})
            self.assertTrue(metric["event_types"])
            if metric["aggregation"] != "count":
                self.assertTrue(metric["value_field"])

    def test_cohort_is_workspace_time_and_dimension_scoped(self) -> None:
        matching = {"event_id": "2", "workspace_id": "ws-a", "occurred_at": "2026-08-03T00:00:00Z", "data": {"source": "outbound", "region": "fr"}}
        events = [
            matching,
            {**matching, "event_id": "1", "workspace_id": "ws-b"},
            {**matching, "event_id": "3", "occurred_at": "2026-09-01T00:00:00Z"},
            {**matching, "event_id": "4", "data": {"source": "inbound", "region": "fr"}},
        ]
        self.assertEqual([matching], select_cohort(reversed(events), self.policy))

    def test_invalid_or_timezone_free_windows_are_rejected(self) -> None:
        with self.assertRaises(MetricPolicyError):
            CohortPolicy("c", "ws-a", "2026-08-01", "2026-09-01")
        with self.assertRaises(MetricPolicyError):
            CohortPolicy("c", "ws-a", "2026-09-01T00:00:00Z", "2026-08-01T00:00:00Z")


if __name__ == "__main__":
    unittest.main()
