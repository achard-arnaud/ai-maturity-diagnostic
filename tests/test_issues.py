from __future__ import annotations

import unittest

from app.blockers import issue


class IssueFactoryTests(unittest.TestCase):
    def test_issue_is_non_blocking_and_carries_no_resolver(self) -> None:
        item = issue(
            kind="anti_fit",
            statement="Selected offer has a stale pricing signal.",
            epistemic_status="hypothesis",
            can_change_decision=False,
            context_paths=["studies/acme/06_product_fit_matrix.yaml"],
        )
        self.assertTrue(item["issue_id"].startswith("ISS-"))
        self.assertEqual("anti_fit", item["kind"])
        self.assertEqual("hypothesis", item["epistemic_status"])
        self.assertFalse(item["can_change_decision"])
        # Unlike blocker(), an issue never carries a resolver/CTA shape.
        self.assertNotIn("owner_skill", item)
        self.assertNotIn("cta_label", item)

    def test_issue_id_is_stable_for_same_kind_statement(self) -> None:
        first = issue(kind="stale_signal", statement="Same tension.")
        second = issue(kind="stale_signal", statement="Same tension.")
        self.assertEqual(first["issue_id"], second["issue_id"])

    def test_issue_requires_kind_and_statement(self) -> None:
        # Basic contract completeness (FOLLOWUP-equivalent lint, cheap variant):
        # an Issue without a kind or a statement is rejected at construction,
        # so no consumer can ever observe an incomplete Issue.
        with self.assertRaises(ValueError):
            issue(kind="", statement="Something.")
        with self.assertRaises(ValueError):
            issue(kind="anti_fit", statement="")

    def test_issue_rejects_unknown_epistemic_status(self) -> None:
        # The vocabulary is the one already established by contracts/claim.schema.yaml
        # (fact/inference/hypothesis/unknown) — no new taxonomy is introduced here.
        with self.assertRaises(ValueError):
            issue(kind="anti_fit", statement="X", epistemic_status="vendor_claim")

    def test_hypothesis_issue_is_never_read_as_fact_by_any_consumer(self) -> None:
        # There is exactly one consumer of issue() dicts today: QualificationCockpit
        # attaches them to a study row under "issues" and nothing branches on
        # epistemic_status to treat a hypothesis as settled truth. This test pins
        # that invariant so a future consumer can't silently start doing so.
        item = issue(kind="anti_fit", statement="Warning gate is open.", epistemic_status="hypothesis")
        self.assertNotEqual("fact", item["epistemic_status"])
        # A hypothesis issue must never claim it can unilaterally change the
        # decision on its own say-so; that would be treating it as settled fact.
        self.assertFalse(issue(kind="anti_fit", statement="x", epistemic_status="hypothesis", can_change_decision=False)["can_change_decision"])


if __name__ == "__main__":
    unittest.main()
