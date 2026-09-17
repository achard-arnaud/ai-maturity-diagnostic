from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.learning_proposals import LearningProposalError, LearningProposalStore


class LearningProposalTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.store = LearningProposalStore(self.root, "ws-a")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def create(self, origin: str = "retrospective") -> dict:
        return self.store.create(origin=origin, target_kind="prompt", target_ref="prompts/research.md", hypothesis="Fewer unsupported claims", evidence_refs=["evt-2", "evt-1"], actor_id="alice", proposal_id=f"lp_{origin}")

    def test_origins_are_explicit_and_do_not_mutate_target(self) -> None:
        target = self.root / "prompts" / "research.md"
        target.parent.mkdir(); target.write_text("baseline", encoding="utf-8")
        for origin in ("retrospective", "red_team", "dreaming"):
            proposal = self.create(origin)
            self.store.transition(proposal["proposal_id"], to_status="in_review", actor_id="bob", rationale="review")
            self.store.transition(proposal["proposal_id"], to_status="accepted", actor_id="bob", rationale="test it")
        self.assertEqual("baseline", target.read_text(encoding="utf-8"))
        self.assertEqual(3, len(self.store.list()))

    def test_accept_reject_and_measured_lifecycles_are_audited(self) -> None:
        accepted = self.create()
        self.store.transition(accepted["proposal_id"], to_status="in_review", actor_id="bob", rationale="ready")
        self.store.transition(accepted["proposal_id"], to_status="accepted", actor_id="bob", rationale="bounded trial")
        self.store.transition(accepted["proposal_id"], to_status="testing", actor_id="bob", rationale="start", experiment_id="exp-1")
        measured = self.store.transition(accepted["proposal_id"], to_status="measured", actor_id="bob", rationale="quality improved", result_ref="results/exp-1.json")
        rejected = self.store.create(origin="red_team", target_kind="rule", target_ref="rules/gate", hypothesis="remove gate", evidence_refs=["evt-x"], actor_id="alice", proposal_id="lp_rejected")
        self.store.transition(rejected["proposal_id"], to_status="in_review", actor_id="bob", rationale="review")
        self.store.transition(rejected["proposal_id"], to_status="rejected", actor_id="bob", rationale="unsafe")
        self.assertEqual("results/exp-1.json", measured["result_ref"])
        event_types = [event["event_type"] for event in self.store.events.replay()]
        self.assertIn("learning.proposal.accepted", event_types)
        self.assertIn("learning.proposal.rejected", event_types)
        self.assertIn("learning.proposal.measured", event_types)

    def test_invalid_transition_or_origin_is_rejected(self) -> None:
        with self.assertRaises(LearningProposalError):
            self.create("automatic")
        proposal = self.create()
        with self.assertRaises(LearningProposalError):
            self.store.transition(proposal["proposal_id"], to_status="accepted", actor_id="bob", rationale="skip review")


if __name__ == "__main__":
    unittest.main()
