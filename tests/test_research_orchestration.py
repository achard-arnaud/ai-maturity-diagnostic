from __future__ import annotations

import unittest

from app.research_orchestration import BudgetError, PassBudget, PassStep, run_pass


def _step(name: str, cost: float, calls: list[str]):
    def _run(context) -> tuple[str, float]:
        calls.append(name)
        return f"result-{name}", cost

    return PassStep(name=name, run=_run)


class RunPassTests(unittest.TestCase):
    def test_all_steps_complete_within_budget(self) -> None:
        calls: list[str] = []
        steps = [_step("a", 1.0, calls), _step("b", 1.0, calls)]
        result = run_pass(steps, PassBudget(max_steps=10, max_cost=100))
        self.assertEqual("completed", result.status)
        self.assertEqual(["a", "b"], calls)
        self.assertEqual({"a": "result-a", "b": "result-b"}, result.results)
        self.assertIsNone(result.checkpoint)

    def test_max_steps_checkpoints_a_heavy_run(self) -> None:
        calls: list[str] = []
        steps = [_step("a", 1.0, calls), _step("b", 1.0, calls), _step("c", 1.0, calls)]
        result = run_pass(steps, PassBudget(max_steps=2, max_cost=100))
        self.assertEqual("checkpointed", result.status)
        self.assertEqual(["a", "b"], calls)
        self.assertEqual(2, result.checkpoint["next_index"])

    def test_max_cost_checkpoints_once_spent(self) -> None:
        calls: list[str] = []
        steps = [_step("a", 5.0, calls), _step("b", 5.0, calls), _step("c", 5.0, calls)]
        result = run_pass(steps, PassBudget(max_steps=10, max_cost=8.0))
        self.assertEqual("checkpointed", result.status)
        self.assertEqual(["a", "b"], calls)
        self.assertEqual(10.0, result.cost_spent)
        self.assertEqual(2, result.checkpoint["next_index"])

    def test_resume_from_checkpoint_never_reruns_completed_steps(self) -> None:
        calls: list[str] = []
        steps = [_step("a", 1.0, calls), _step("b", 1.0, calls), _step("c", 1.0, calls)]
        first = run_pass(steps, PassBudget(max_steps=1, max_cost=100))
        self.assertEqual(["a"], calls)

        second = run_pass(steps, PassBudget(max_steps=1, max_cost=100), checkpoint=first.checkpoint)
        self.assertEqual(["a", "b"], calls)
        self.assertEqual("checkpointed", second.status)

        third = run_pass(steps, PassBudget(max_steps=10, max_cost=100), checkpoint=second.checkpoint)
        self.assertEqual(["a", "b", "c"], calls)
        self.assertEqual("completed", third.status)
        self.assertEqual(
            {"a": "result-a", "b": "result-b", "c": "result-c"}, third.results
        )

    def test_completed_results_are_never_lost_across_checkpoints(self) -> None:
        calls: list[str] = []
        steps = [_step("a", 1.0, calls), _step("b", 1.0, calls)]
        first = run_pass(steps, PassBudget(max_steps=1, max_cost=100))
        second = run_pass(steps, PassBudget(max_steps=1, max_cost=100), checkpoint=first.checkpoint)
        self.assertIn("a", second.results)
        self.assertIn("b", second.results)

    def test_invalid_budget_rejected(self) -> None:
        with self.assertRaises(BudgetError):
            run_pass([], PassBudget(max_steps=0, max_cost=1))

    def test_context_is_passed_through_with_accumulated_results(self) -> None:
        seen_contexts = []

        def _run(context):
            seen_contexts.append(dict(context))
            return "ok", 1.0

        steps = [
            PassStep(name="a", run=_run),
            PassStep(name="b", run=_run),
        ]
        run_pass(steps, PassBudget(max_steps=10, max_cost=100), context={"case_id": "rc1"})
        self.assertEqual("rc1", seen_contexts[0]["case_id"])
        self.assertEqual({}, seen_contexts[0]["results"])
        self.assertEqual({"a": "ok"}, seen_contexts[1]["results"])


if __name__ == "__main__":
    unittest.main()
