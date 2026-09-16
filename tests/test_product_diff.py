from __future__ import annotations

import unittest

from app.product_diff import diff_snapshot_content


def _content(**kwargs) -> dict:
    base = {"name": "Acme", "description": "Core", "exclusions": ["no on-prem"], "hard_gates": ["SOC2"], "capabilities": ["SSO"]}
    base.update(kwargs)
    return base


class ProductDiffTests(unittest.TestCase):
    def test_identical_content_has_no_diff(self) -> None:
        self.assertEqual({}, diff_snapshot_content(_content(), _content()))

    def test_scalar_field_change_is_reported(self) -> None:
        diff = diff_snapshot_content(_content(), _content(description="Updated"))
        self.assertEqual({"old": "Core", "new": "Updated"}, diff["description"])
        self.assertNotIn("name", diff)

    def test_list_additions_and_removals_are_reported(self) -> None:
        diff = diff_snapshot_content(
            _content(hard_gates=["SOC2"]),
            _content(hard_gates=["SOC2", "ISO27001"]),
        )
        self.assertEqual(["ISO27001"], diff["hard_gates"]["added"])
        self.assertEqual([], diff["hard_gates"]["removed"])

    def test_list_removal_is_reported(self) -> None:
        diff = diff_snapshot_content(
            _content(exclusions=["no on-prem", "no SSO"]),
            _content(exclusions=["no on-prem"]),
        )
        self.assertEqual([], diff["exclusions"]["added"])
        self.assertEqual(["no SSO"], diff["exclusions"]["removed"])

    def test_list_reordering_is_not_a_diff(self) -> None:
        diff = diff_snapshot_content(
            _content(capabilities=["SSO", "SCIM"]),
            _content(capabilities=["SCIM", "SSO"]),
        )
        self.assertNotIn("capabilities", diff)

    def test_unchanged_fields_are_absent_from_diff(self) -> None:
        diff = diff_snapshot_content(_content(), _content(description="Changed"))
        self.assertEqual({"description"}, set(diff.keys()))


if __name__ == "__main__":
    unittest.main()
