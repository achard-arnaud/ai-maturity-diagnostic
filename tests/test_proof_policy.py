from __future__ import annotations

import unittest

from app.proof_policy import ProofPolicyError, can_support_client_claim, design_proof, record_proof_outcome


def _design() -> dict:
    return design_proof(proof_id="proof-1", opportunity_id="opp-1", success_metrics=[{"metric_id": "cycle-time", "target": 20, "unit": "%"}], falsifier="No measurable cycle-time improvement after the agreed test period.")


class ProofPolicyTests(unittest.TestCase):
    def test_proof_requires_metrics_and_falsifier_before_running(self) -> None:
        with self.assertRaisesRegex(ProofPolicyError, "success metric"):
            design_proof(proof_id="p", opportunity_id="o", success_metrics=[], falsifier="fails")
        with self.assertRaisesRegex(ProofPolicyError, "falsifier"):
            design_proof(proof_id="p", opportunity_id="o", success_metrics=[{"metric_id": "m", "target": 1, "unit": "x"}], falsifier="")

    def test_met_evidence_backed_outcome_can_support_a_claim(self) -> None:
        outcome = record_proof_outcome(_design(), actuals={"cycle-time": 25}, evidence_refs=["measurement-1"], recorded_at="2026-09-17T00:00:00+00:00")
        self.assertEqual("met", outcome["status"])
        self.assertTrue(can_support_client_claim(outcome))

    def test_missing_metric_is_inconclusive_not_a_claim(self) -> None:
        outcome = record_proof_outcome(_design(), actuals={}, evidence_refs=["measurement-1"], recorded_at="2026-09-17T00:00:00+00:00")
        self.assertEqual("inconclusive", outcome["status"])
        self.assertFalse(can_support_client_claim(outcome))

    def test_favourable_metric_without_evidence_is_not_a_claim(self) -> None:
        outcome = record_proof_outcome(_design(), actuals={"cycle-time": 25}, evidence_refs=[], recorded_at="2026-09-17T00:00:00+00:00")
        self.assertFalse(can_support_client_claim(outcome))


if __name__ == "__main__":
    unittest.main()
