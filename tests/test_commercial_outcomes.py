from __future__ import annotations

import unittest

from app.commercial_outcomes import CommercialOutcomeError, create_expansion, create_learning_event, record_loss
from app.opportunity_policy import required_exit_criteria, transition_opportunity
from app.proof_policy import can_support_client_claim, design_proof, record_proof_outcome

TIME = "2026-09-17T00:00:00+00:00"


class CommercialOutcomeTests(unittest.TestCase):
    def test_loss_requires_reason_and_emits_learning(self) -> None:
        with self.assertRaisesRegex(CommercialOutcomeError, "loss reason"):
            record_loss(opportunity_id="opp-1", reason="", decided_at=TIME)
        loss = record_loss(opportunity_id="opp-1", reason="No procurement approval", decided_at=TIME)
        learning = create_learning_event(event_id="learn-1", workspace_id="ws-a", opportunity_id=loss["opportunity_id"], outcome="lost", signal=loss["reason"], created_at=TIME)
        self.assertEqual("lost", learning["outcome"])

    def test_only_won_deal_can_expand(self) -> None:
        deal = {"deal_id": "deal-1", "workspace_id": "ws-a", "status": "won"}
        self.assertEqual("identified", create_expansion(expansion_id="exp-1", deal=deal, created_at=TIME)["status"])
        deal["status"] = "lost"
        with self.assertRaisesRegex(CommercialOutcomeError, "won"):
            create_expansion(expansion_id="exp-1", deal=deal, created_at=TIME)

    def test_end_to_end_opportunity_can_close_won_after_proof(self) -> None:
        opportunity = {"status": "draft"}
        opportunity = transition_opportunity(opportunity, next_stage="discovery", completed_criteria=required_exit_criteria("discovery"))
        opportunity = transition_opportunity(opportunity, next_stage="proof", completed_criteria=required_exit_criteria("proof"))
        proof = design_proof(proof_id="proof-1", opportunity_id="opp-1", success_metrics=[{"metric_id": "m", "target": 1, "unit": "x"}], falsifier="No benefit")
        outcome = record_proof_outcome(proof, actuals={"m": 1}, evidence_refs=["measurement-1"], recorded_at=TIME)
        self.assertTrue(can_support_client_claim(outcome))
        opportunity = transition_opportunity(opportunity, next_stage="proposal", completed_criteria=required_exit_criteria("proposal"))
        opportunity = transition_opportunity(opportunity, next_stage="closed_won", completed_criteria=required_exit_criteria("closed_won"))
        self.assertEqual("closed_won", opportunity["status"])


if __name__ == "__main__":
    unittest.main()
