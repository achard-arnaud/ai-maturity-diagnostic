from __future__ import annotations

import unittest

from app.fit_policy import compute_input_lock_hash, create_input_lock, is_input_lock_current


class InputLockHashTests(unittest.TestCase):
    def test_same_inputs_produce_the_same_hash(self) -> None:
        a = compute_input_lock_hash("d1", 3, "snap1")
        b = compute_input_lock_hash("d1", 3, "snap1")
        self.assertEqual(a, b)

    def test_different_demand_version_changes_the_hash(self) -> None:
        a = compute_input_lock_hash("d1", 3, "snap1")
        b = compute_input_lock_hash("d1", 4, "snap1")
        self.assertNotEqual(a, b)

    def test_different_snapshot_changes_the_hash(self) -> None:
        a = compute_input_lock_hash("d1", 3, "snap1")
        b = compute_input_lock_hash("d1", 3, "snap2")
        self.assertNotEqual(a, b)

    def test_different_demand_id_changes_the_hash(self) -> None:
        a = compute_input_lock_hash("d1", 3, "snap1")
        b = compute_input_lock_hash("d2", 3, "snap1")
        self.assertNotEqual(a, b)


class InputLockReproducibilityTests(unittest.TestCase):
    def test_two_assessments_over_the_same_inputs_share_the_same_base(self) -> None:
        lock_a = create_input_lock("d1", 3, "snap1")
        lock_b = create_input_lock("d1", 3, "snap1")
        self.assertEqual(lock_a.input_hash, lock_b.input_hash)
        self.assertEqual(lock_a, lock_b)

    def test_lock_is_current_when_nothing_has_moved(self) -> None:
        lock = create_input_lock("d1", 3, "snap1")
        self.assertTrue(is_input_lock_current(lock, current_demand_version=3, current_snapshot_id="snap1"))

    def test_lock_is_not_current_after_demand_edit(self) -> None:
        lock = create_input_lock("d1", 3, "snap1")
        self.assertFalse(is_input_lock_current(lock, current_demand_version=4, current_snapshot_id="snap1"))

    def test_lock_is_not_current_after_new_snapshot_published(self) -> None:
        lock = create_input_lock("d1", 3, "snap1")
        self.assertFalse(is_input_lock_current(lock, current_demand_version=3, current_snapshot_id="snap2"))


if __name__ == "__main__":
    unittest.main()
