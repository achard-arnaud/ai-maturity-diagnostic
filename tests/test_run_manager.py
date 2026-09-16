import tempfile
import unittest
from pathlib import Path

from app.run_manager import InvalidResumeToken, RunManager, RunStateError


class RunManagerTests(unittest.TestCase):
    def manager(self, root: str) -> RunManager:
        return RunManager(Path(root), "ws-1", "actor-1")

    def test_checkpoint_and_resume_increment_attempt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            manager = self.manager(tmp)
            prepared = manager.prepare("research", input_ref="study:1")
            started = manager.start(prepared.run["run_id"])
            self.assertEqual(started["attempt"], 1)
            checkpointed = manager.checkpoint(started["run_id"], {"cursor": 4})
            resumed = manager.resume(started["run_id"], prepared.resume_token)
            self.assertEqual(resumed["status"], "started")
            self.assertEqual(resumed["attempt"], 2)
            self.assertEqual(checkpointed["checkpoint"], {"cursor": 4})

    def test_failed_retryable_run_can_resume(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            manager = self.manager(tmp)
            prepared = manager.prepare("research")
            manager.start(prepared.run["run_id"])
            failed = manager.fail(prepared.run["run_id"], "RATE_LIMIT", "later", retryable=True)
            self.assertTrue(failed["error"]["retryable"])
            self.assertEqual(manager.resume(prepared.run["run_id"], prepared.resume_token)["status"], "started")

    def test_cancel_is_terminal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            manager = self.manager(tmp)
            prepared = manager.prepare("research")
            manager.cancel(prepared.run["run_id"], "operator")
            with self.assertRaises(RunStateError):
                manager.start(prepared.run["run_id"])

    def test_invalid_resume_token_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            manager = self.manager(tmp)
            prepared = manager.prepare("research")
            manager.start(prepared.run["run_id"])
            manager.checkpoint(prepared.run["run_id"], {"cursor": 1})
            with self.assertRaises(InvalidResumeToken):
                manager.resume(prepared.run["run_id"], "wrong")

    def test_non_retryable_failure_cannot_resume(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            manager = self.manager(tmp)
            prepared = manager.prepare("research")
            manager.start(prepared.run["run_id"])
            manager.fail(prepared.run["run_id"], "INVALID", "bad input", retryable=False)
            with self.assertRaises(RunStateError):
                manager.resume(prepared.run["run_id"], prepared.resume_token)

    def test_prepare_idempotency_does_not_duplicate_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            manager = self.manager(tmp)
            first = manager.prepare("research", idempotency_key="request-1")
            second = manager.prepare("research", idempotency_key="request-1")
            self.assertEqual(first.run["run_id"], second.run["run_id"])
            self.assertEqual(len(list((Path(tmp) / "runtime/runs").glob("*.yaml"))), 1)


if __name__ == "__main__":
    unittest.main()
