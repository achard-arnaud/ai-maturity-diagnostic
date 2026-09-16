import tempfile
import threading
import unittest
from pathlib import Path

from app.execution_policy import BudgetEnvelope, BudgetExceeded, BudgetLedger, RetryPolicy, Usage, cache_key


class ExecutionPolicyTests(unittest.TestCase):
    def envelope(self) -> BudgetEnvelope:
        return BudgetEnvelope(10, 1000, 500, 5.0, 100.0)

    def test_budget_checkpoint_and_hard_stop(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ledger = BudgetLedger(Path(tmp), "ws", self.envelope())
            status = ledger.consume(Usage(calls=8, input_tokens=100))
            self.assertEqual(status.mode, "checkpoint_required")
            with self.assertRaises(BudgetExceeded):
                ledger.consume(Usage(calls=3))
            self.assertEqual(ledger.status().used.calls, 8)

    def test_concurrent_usage_is_not_lost(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ledger = BudgetLedger(Path(tmp), "ws", self.envelope())
            threads = [threading.Thread(target=ledger.consume, args=(Usage(calls=1),)) for _ in range(10)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
            self.assertEqual(ledger.status().used.calls, 10)

    def test_retry_429_uses_retry_after(self) -> None:
        decision = RetryPolicy().decide(attempt=1, status_code=429, retry_after_seconds=17)
        self.assertTrue(decision.retry)
        self.assertEqual(decision.delay_seconds, 17)

    def test_timeout_backoff_is_bounded_and_deterministic_with_sample(self) -> None:
        decision = RetryPolicy(base_delay_seconds=2, max_delay_seconds=3).decide(
            attempt=3, timed_out=True, random_value=0.5
        )
        self.assertTrue(decision.retry)
        self.assertEqual(decision.delay_seconds, 3)

    def test_non_retryable_and_attempt_limit_stop(self) -> None:
        self.assertFalse(RetryPolicy().decide(attempt=1, status_code=400).retry)
        self.assertFalse(RetryPolicy(max_attempts=2).decide(attempt=2, status_code=503).retry)

    def test_cache_key_covers_model_prompt_policy_and_payload(self) -> None:
        base = cache_key(provider="p", model="m", prompt_version="1", policy_version="1", payload={"x": 1})
        changed = cache_key(provider="p", model="m2", prompt_version="1", policy_version="1", payload={"x": 1})
        self.assertNotEqual(base, changed)
        repeated = cache_key(provider="p", model="m", prompt_version="1", policy_version="1", payload={"x": 1})
        self.assertEqual(base, repeated)


if __name__ == "__main__":
    unittest.main()
