from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from app import harvest_orchestration, harvest_runner
from app.acquisition_policy import SearchRequest
from app.execution_policy import BudgetEnvelope, RetryPolicy
from app.harvest_orchestration import recommended_sources_for_space, run_harvest
from scripts.social_search import Result


def make_request(**overrides):
    defaults = dict(
        workspace_id="acme-ws",
        query="AI adoption",
        sources=("hackernews",),
        space="discover",
        requested_by="u1",
    )
    defaults.update(overrides)
    return SearchRequest(**defaults)


def NOOP_SLEEP(_seconds: float) -> None:
    return None


class RecommendedSourcesTests(unittest.TestCase):
    def test_known_spaces_return_expected_sources(self) -> None:
        self.assertEqual(("hackernews", "arxiv", "github", "web", "x"), recommended_sources_for_space("discover"))
        self.assertEqual(("youtube", "reddit", "perplexity"), recommended_sources_for_space("research"))
        self.assertEqual(("linkedin",), recommended_sources_for_space("targets"))

    def test_unknown_space_raises(self) -> None:
        with self.assertRaises(ValueError):
            recommended_sources_for_space("pipeline")


class RunHarvestTests(unittest.TestCase):
    def test_workspace_id_mismatch_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            request = make_request(workspace_id="acme-ws")
            with self.assertRaises(ValueError):
                run_harvest(Path(tmp), "other-ws", "actor1", request)

    def test_happy_path_completes_and_persists_a_run(self) -> None:
        fake = mock.Mock(
            return_value=[Result("hackernews", "Post A", "https://news.ycombinator.com/item?id=1", "s")]
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with mock.patch.dict(harvest_runner.SEARCHERS, {"hackernews": fake}):
                result = run_harvest(root, "acme-ws", "actor1", make_request())
            self.assertEqual("completed", result.status)
            self.assertEqual(1, len(result.candidates))
            self.assertTrue(result.run_id.startswith("run_"))
            self.assertIsInstance(result.correlation_id, str)

            from app.run_manager import RunManager

            run, _ = RunManager(root=root, workspace_id="acme-ws", actor_id="actor1").get(result.run_id)
            self.assertEqual("completed", run["status"])
            self.assertEqual(1, len(run["output_refs"]))

    def test_budget_exceeded_blocks_the_run_and_stops_further_sources(self) -> None:
        first = mock.Mock(return_value=[])
        second = mock.Mock(return_value=[])
        request = make_request(sources=("hackernews", "arxiv"))
        envelope = BudgetEnvelope(
            max_calls=1, max_input_tokens=0, max_output_tokens=0, max_cost_units=0.0, max_wall_seconds=600.0
        )
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.dict(harvest_runner.SEARCHERS, {"hackernews": first, "arxiv": second}):
                result = run_harvest(Path(tmp), "acme-ws", "actor1", request, envelope=envelope)
        self.assertEqual("blocked", result.status)
        first.assert_called_once()
        second.assert_not_called()

    def test_all_sources_failing_marks_the_run_failed(self) -> None:
        def boom(*args, **kwargs):
            raise RuntimeError("boom")

        request = make_request(sources=("hackernews",))
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.dict(harvest_runner.SEARCHERS, {"hackernews": boom}):
                result = run_harvest(Path(tmp), "acme-ws", "actor1", request, retry_policy=RetryPolicy(max_attempts=1))
        self.assertEqual("failed", result.status)
        self.assertEqual((), result.candidates)

    def test_partial_failure_across_sources_still_completes(self) -> None:
        ok_fn = mock.Mock(
            return_value=[Result("hackernews", "Post A", "https://news.ycombinator.com/item?id=1", "s")]
        )

        def boom(*args, **kwargs):
            raise RuntimeError("boom")

        request = make_request(sources=("hackernews", "arxiv"))
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.dict(harvest_runner.SEARCHERS, {"hackernews": ok_fn, "arxiv": boom}):
                result = run_harvest(
                    Path(tmp), "acme-ws", "actor1", request, retry_policy=RetryPolicy(max_attempts=1)
                )
        self.assertEqual("completed", result.status)
        self.assertEqual(1, len(result.candidates))

    def test_timeout_is_retried_up_to_the_policy_cap(self) -> None:
        request = make_request(sources=("hackernews",))
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.object(harvest_orchestration, "run_source") as run_source_mock:
                run_source_mock.side_effect = [
                    harvest_orchestration.SourceRunResult("hackernews", "timeout", (), 10, "slow"),
                    harvest_orchestration.SourceRunResult("hackernews", "timeout", (), 10, "slow"),
                    harvest_orchestration.SourceRunResult(
                        "hackernews",
                        "ok",
                        (
                            mock.Mock(candidate_id="cand-1"),
                        ),
                        10,
                        None,
                    ),
                ]
                result = run_harvest(
                    Path(tmp),
                    "acme-ws",
                    "actor1",
                    request,
                    retry_policy=RetryPolicy(max_attempts=5, base_delay_seconds=0.0, jitter_ratio=0.0),
                    sleep_fn=NOOP_SLEEP,
                )
        self.assertEqual("completed", result.status)
        self.assertEqual(3, run_source_mock.call_count)
        self.assertEqual(1, len(result.candidates))

    def test_error_status_is_not_retried(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.object(harvest_orchestration, "run_source") as run_source_mock:
                run_source_mock.return_value = harvest_orchestration.SourceRunResult(
                    "hackernews", "error", (), 10, "boom"
                )
                run_harvest(
                    Path(tmp),
                    "acme-ws",
                    "actor1",
                    make_request(),
                    retry_policy=RetryPolicy(max_attempts=5, base_delay_seconds=0.0),
                    sleep_fn=NOOP_SLEEP,
                )
        self.assertEqual(1, run_source_mock.call_count)


if __name__ == "__main__":
    unittest.main()
