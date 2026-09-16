from __future__ import annotations

import unittest

from app.reach_scheduler import (
    ReachSchedulerError,
    count_sent_today,
    evaluate_schedule,
    is_degraded_mode_active,
    is_within_time_window,
)


class TimeWindowTests(unittest.TestCase):
    def test_within_email_window(self) -> None:
        self.assertTrue(is_within_time_window("email", hour=10))

    def test_before_email_window(self) -> None:
        self.assertFalse(is_within_time_window("email", hour=6))

    def test_after_email_window(self) -> None:
        self.assertFalse(is_within_time_window("email", hour=20))

    def test_unknown_channel_rejected(self) -> None:
        with self.assertRaises(ReachSchedulerError):
            is_within_time_window("carrier_pigeon", hour=10)


class CountSentTodayTests(unittest.TestCase):
    def test_counts_only_matching_channel_and_day(self) -> None:
        events = [
            {"channel": "email", "sent_at": "2026-01-01T10:00:00Z"},
            {"channel": "email", "sent_at": "2026-01-02T10:00:00Z"},
            {"channel": "phone", "sent_at": "2026-01-01T10:00:00Z"},
        ]
        self.assertEqual(1, count_sent_today("email", events, today="2026-01-01"))


class EvaluateScheduleTests(unittest.TestCase):
    def test_allowed_within_window_and_under_quota(self) -> None:
        decision = evaluate_schedule(
            "email", hour=10, today="2026-01-01", sent_events=[], daily_quota=5
        )
        self.assertTrue(decision.allowed)
        self.assertFalse(decision.degraded)

    def test_degraded_when_outside_time_window(self) -> None:
        decision = evaluate_schedule(
            "email", hour=22, today="2026-01-01", sent_events=[], daily_quota=5
        )
        self.assertFalse(decision.allowed)
        self.assertTrue(decision.degraded)
        self.assertEqual("outside_time_window", decision.reason)

    def test_degraded_when_quota_exhausted(self) -> None:
        events = [{"channel": "email", "sent_at": "2026-01-01T08:00:00Z"} for _ in range(3)]
        decision = evaluate_schedule(
            "email", hour=10, today="2026-01-01", sent_events=events, daily_quota=3
        )
        self.assertFalse(decision.allowed)
        self.assertTrue(decision.degraded)
        self.assertEqual("quota_exhausted", decision.reason)

    def test_never_forces_a_send_through_closed_window_even_with_quota_room(self) -> None:
        decision = evaluate_schedule(
            "phone", hour=23, today="2026-01-01", sent_events=[], daily_quota=100
        )
        self.assertFalse(decision.allowed)
        self.assertTrue(decision.degraded)


class DegradedModeTests(unittest.TestCase):
    def test_degraded_mode_active_when_any_decision_degraded(self) -> None:
        decisions = [
            evaluate_schedule("email", hour=10, today="2026-01-01", sent_events=[], daily_quota=5),
            evaluate_schedule("email", hour=22, today="2026-01-01", sent_events=[], daily_quota=5),
        ]
        self.assertTrue(is_degraded_mode_active(decisions))

    def test_degraded_mode_inactive_when_all_allowed(self) -> None:
        decisions = [
            evaluate_schedule("email", hour=10, today="2026-01-01", sent_events=[], daily_quota=5),
            evaluate_schedule("manual", hour=10, today="2026-01-01", sent_events=[], daily_quota=5),
        ]
        self.assertFalse(is_degraded_mode_active(decisions))


if __name__ == "__main__":
    unittest.main()
