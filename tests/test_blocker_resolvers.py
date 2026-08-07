from __future__ import annotations

import unittest

from app.blockers import attach_resolution, blocker, human_review_blocker


class BlockerResolverTests(unittest.TestCase):
    def test_skill_blocker_exposes_action_and_postcondition(self) -> None:
        item = blocker(
            category="fit_gate",
            key="study:G1",
            message="Gate is open.",
            required_state="Evidence-backed PASS or FAIL",
            owner_skill="opportunity-fit-matching",
            cta_label="Resolve gate",
            cta_input="Resolve G1 from evidence.",
            context_paths=["studies/acme/06_product_fit_matrix.yaml"],
            postcondition="Gate is resolved",
        )
        self.assertTrue(item["blocker_id"].startswith("BLK-"))
        self.assertEqual("opportunity-fit-matching", item["owner_skill"])
        self.assertEqual("Resolve gate", item["cta_label"])
        self.assertTrue(item["prepare_only_safe"])
        step = attach_resolution({"id": "matching", "status": "blocked"}, item)
        self.assertEqual("Resolve gate", step["resolver"]["cta_label"])
        self.assertEqual("Gate is resolved", step["resolver"]["postcondition"])

    def test_human_review_is_explicit_and_not_fake_executable(self) -> None:
        item = human_review_blocker(
            key="offer:review",
            message="Owner review required.",
            required_state="Owner accepts or rejects the unresolved unknowns",
            cta_label="Review offer",
            postcondition="Owner decision recorded",
        )
        self.assertIsNone(item["owner_skill"])
        self.assertTrue(item["human_action"])
        self.assertFalse(item["prepare_only_safe"])

    def test_blocker_requires_real_resolver(self) -> None:
        with self.assertRaises(ValueError):
            blocker(
                category="demand",
                key="missing",
                message="Missing.",
                required_state="Present",
                cta_label="Resolve",
                postcondition="Present",
            )


if __name__ == "__main__":
    unittest.main()
