from __future__ import annotations

import itertools
import unittest

from app.fit_gates import (
    GateResult,
    can_compute_score,
    evaluate_hard_gates,
    failed_gate_reasons,
    resolve_gate_blocker,
)


def _snapshot(hard_gates: list[str]) -> dict:
    return {"content": {"hard_gates": hard_gates}}


class EvaluateHardGatesTests(unittest.TestCase):
    def test_all_gates_get_a_result(self) -> None:
        snapshot = _snapshot(["SOC2", "GDPR"])
        results = evaluate_hard_gates(snapshot, [{"gate_id": "SOC2", "passed": True}, {"gate_id": "GDPR", "passed": True}])
        self.assertEqual(2, len(results))
        self.assertTrue(all(r.passed for r in results))

    def test_missing_check_defaults_to_not_passed(self) -> None:
        snapshot = _snapshot(["SOC2"])
        results = evaluate_hard_gates(snapshot, [])
        self.assertFalse(results[0].passed)
        self.assertEqual("not yet evaluated", results[0].reason)

    def test_failed_gate_carries_its_reason(self) -> None:
        snapshot = _snapshot(["SOC2"])
        results = evaluate_hard_gates(snapshot, [{"gate_id": "SOC2", "passed": False, "reason": "no certification on file"}])
        self.assertEqual("no certification on file", results[0].reason)


class ExhaustiveGateMatrixTests(unittest.TestCase):
    """Stop condition: 'aucun score bypass' -- every combination of
    gate pass/fail states and blocker counts is checked; scoring is
    allowed in exactly one case: every gate passed AND zero open
    blockers."""

    def test_exhaustive_matrix_over_three_gates_and_blocker_counts(self) -> None:
        gate_names = ["g1", "g2", "g3"]
        for passed_flags in itertools.product([True, False], repeat=3):
            gates = [GateResult(gate_id=n, name=n, passed=p) for n, p in zip(gate_names, passed_flags)]
            for open_blockers in (0, 1, 2):
                allowed = can_compute_score(gates, open_blocker_count=open_blockers)
                expected = all(passed_flags) and open_blockers == 0
                self.assertEqual(
                    expected, allowed,
                    f"gates={passed_flags} blockers={open_blockers} expected {expected} got {allowed}",
                )

    def test_single_failed_gate_blocks_regardless_of_others(self) -> None:
        gates = [
            GateResult("g1", "g1", True),
            GateResult("g2", "g2", False),
            GateResult("g3", "g3", True),
        ]
        self.assertFalse(can_compute_score(gates, open_blocker_count=0))

    def test_open_blocker_blocks_even_with_all_gates_passed(self) -> None:
        gates = [GateResult("g1", "g1", True)]
        self.assertFalse(can_compute_score(gates, open_blocker_count=1))

    def test_no_gates_and_no_blockers_allows_scoring(self) -> None:
        self.assertTrue(can_compute_score([], open_blocker_count=0))


class FailedGateReasonsTests(unittest.TestCase):
    def test_only_failed_gates_are_listed(self) -> None:
        gates = [GateResult("g1", "g1", True), GateResult("g2", "g2", False, reason="missing evidence")]
        reasons = failed_gate_reasons(gates)
        self.assertEqual(["g2: missing evidence"], reasons)


class ResolverContractTests(unittest.TestCase):
    def test_passed_gate_has_no_resolver(self) -> None:
        self.assertIsNone(resolve_gate_blocker(GateResult("g1", "g1", True)))

    def test_failed_gate_produces_full_resolver_contract(self) -> None:
        contract = resolve_gate_blocker(GateResult("g1", "SOC2", False, reason="no cert"))
        self.assertIn("SOC2", contract.why_blocked)
        self.assertTrue(contract.required_state_or_evidence)
        self.assertEqual("fit_reviewer", contract.owner_capability)
        self.assertTrue(contract.cta)
        self.assertTrue(contract.postcondition)
        self.assertTrue(contract.cost_estimate)


if __name__ == "__main__":
    unittest.main()
