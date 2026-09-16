from __future__ import annotations

import unittest
from datetime import date

from app.network_temporal import CurrentnessConflict, evaluate_currentness


def _relationship(**overrides) -> dict:
    base = {
        "current_status": "current",
        "valid_from": "2026-01-01",
        "valid_to": None,
    }
    base.update(overrides)
    return base


class CurrentnessPolicyTests(unittest.TestCase):
    def test_current_status_within_open_interval_is_current(self) -> None:
        result = evaluate_currentness(_relationship(), as_of=date(2026, 6, 1))
        self.assertTrue(result.is_current)

    def test_invalidated_status_is_never_current_even_with_open_interval(self) -> None:
        result = evaluate_currentness(_relationship(current_status="invalidated"), as_of=date(2026, 6, 1))
        self.assertFalse(result.is_current)
        self.assertIn("invalidated", result.reason)

    def test_expired_valid_to_overrides_current_status(self) -> None:
        # This is the core rule this Sprint adds: current_status alone is not enough.
        record = _relationship(current_status="current", valid_to="2026-03-01")
        result = evaluate_currentness(record, as_of=date(2026, 6, 1))
        self.assertFalse(result.is_current)
        self.assertIn("valid_to", result.reason)

    def test_future_valid_from_is_not_current_yet(self) -> None:
        record = _relationship(valid_from="2026-12-01")
        result = evaluate_currentness(record, as_of=date(2026, 6, 1))
        self.assertFalse(result.is_current)
        self.assertIn("future", result.reason)

    def test_former_status_without_valid_to_raises_conflict(self) -> None:
        record = _relationship(current_status="former", valid_to=None)
        with self.assertRaises(CurrentnessConflict):
            evaluate_currentness(record, as_of=date(2026, 6, 1))

    def test_former_status_with_valid_to_in_past_is_not_current(self) -> None:
        record = _relationship(current_status="former", valid_to="2026-03-01")
        result = evaluate_currentness(record, as_of=date(2026, 6, 1))
        self.assertFalse(result.is_current)

    def test_unverified_status_within_interval_counts_as_current(self) -> None:
        result = evaluate_currentness(_relationship(current_status="unverified"), as_of=date(2026, 6, 1))
        self.assertTrue(result.is_current)

    def test_valid_to_is_inclusive_of_its_own_date(self) -> None:
        # valid_to is the last day the relationship is still valid.
        record = _relationship(valid_to="2026-06-01")
        result = evaluate_currentness(record, as_of=date(2026, 6, 1))
        self.assertTrue(result.is_current)

    def test_day_after_valid_to_is_not_current(self) -> None:
        record = _relationship(valid_to="2026-06-01")
        result = evaluate_currentness(record, as_of=date(2026, 6, 2))
        self.assertFalse(result.is_current)


if __name__ == "__main__":
    unittest.main()
