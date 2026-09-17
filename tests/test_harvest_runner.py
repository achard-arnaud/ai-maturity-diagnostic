from __future__ import annotations

import time
import unittest
from unittest import mock

from app import harvest_runner
from app.acquisition_policy import SearchRequest
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


class RunSourceTests(unittest.TestCase):
    def test_unknown_source_raises(self) -> None:
        with self.assertRaises(ValueError):
            harvest_runner.run_source("myspace", make_request(sources=("hackernews",)))

    def test_ok_status_maps_every_result_to_a_candidate(self) -> None:
        fake = mock.Mock(
            return_value=[
                Result("hackernews", "Post A", "https://news.ycombinator.com/item?id=1", "snippet a"),
                Result("hackernews", "Post B", "https://news.ycombinator.com/item?id=2", "snippet b"),
            ]
        )
        with mock.patch.dict(harvest_runner.SEARCHERS, {"hackernews": fake}):
            result = harvest_runner.run_source("hackernews", make_request())
        self.assertEqual("ok", result.status)
        self.assertEqual(2, len(result.candidates))
        self.assertIsNone(result.error)
        fake.assert_called_once_with("AI adoption", 30, 10, True, False)

    def test_empty_results_yield_empty_status_not_error(self) -> None:
        fake = mock.Mock(return_value=[])
        with mock.patch.dict(harvest_runner.SEARCHERS, {"hackernews": fake}):
            result = harvest_runner.run_source("hackernews", make_request())
        self.assertEqual("empty", result.status)
        self.assertEqual((), result.candidates)

    def test_exception_is_isolated_as_error_status_not_raised(self) -> None:
        def boom(*args, **kwargs):
            raise RuntimeError("network exploded")

        with mock.patch.dict(harvest_runner.SEARCHERS, {"hackernews": boom}):
            result = harvest_runner.run_source("hackernews", make_request())
        self.assertEqual("error", result.status)
        self.assertIn("network exploded", result.error)
        self.assertEqual((), result.candidates)

    def test_slow_source_is_reported_as_timeout_not_hung_forever(self) -> None:
        def slow(*args, **kwargs):
            time.sleep(5)
            return []

        with mock.patch.dict(harvest_runner.SEARCHERS, {"hackernews": slow}):
            result = harvest_runner.run_source("hackernews", make_request(), timeout_seconds=0.05)
        self.assertEqual("timeout", result.status)
        self.assertIn("0.05", result.error)

    def test_entity_refs_and_space_are_threaded_onto_every_candidate(self) -> None:
        fake = mock.Mock(
            return_value=[Result("hackernews", "Post A", "https://news.ycombinator.com/item?id=1", "snippet")]
        )
        with mock.patch.dict(harvest_runner.SEARCHERS, {"hackernews": fake}):
            result = harvest_runner.run_source(
                "hackernews", make_request(), entity_refs=("company_acme",)
            )
        self.assertEqual(("company_acme",), result.candidates[0].entity_refs)
        self.assertEqual("discover", result.candidates[0].space)

    def test_source_specific_metadata_survives_onto_the_candidate(self) -> None:
        fake = mock.Mock(
            return_value=[
                Result(
                    "linkedin",
                    "A post",
                    "https://linkedin.com/posts/a",
                    "snippet",
                    metadata={"live_role_validation": False, "content_type": "post"},
                )
            ]
        )
        with mock.patch.dict(harvest_runner.SEARCHERS, {"linkedin": fake}):
            result = harvest_runner.run_source(
                "linkedin", make_request(sources=("linkedin",), space="targets")
            )
        self.assertEqual("ok", result.status)
        self.assertEqual(False, result.candidates[0].metadata["live_role_validation"])
        self.assertEqual("post", result.candidates[0].metadata["content_type"])

    def test_plain_yyyy_mm_dd_date_is_normalized_to_date_time(self) -> None:
        fake = mock.Mock(
            return_value=[Result("hackernews", "Post A", "https://news.ycombinator.com/item?id=1", "s", date="2026-08-01")]
        )
        with mock.patch.dict(harvest_runner.SEARCHERS, {"hackernews": fake}):
            result = harvest_runner.run_source("hackernews", make_request())
        self.assertEqual("2026-08-01T00:00:00+00:00", result.candidates[0].dated_at)

    def test_missing_date_stays_none(self) -> None:
        fake = mock.Mock(
            return_value=[Result("hackernews", "Post A", "https://news.ycombinator.com/item?id=1", "s", date=None)]
        )
        with mock.patch.dict(harvest_runner.SEARCHERS, {"hackernews": fake}):
            result = harvest_runner.run_source("hackernews", make_request())
        self.assertIsNone(result.candidates[0].dated_at)


class RunSourcesTests(unittest.TestCase):
    def test_one_source_failing_does_not_block_the_others(self) -> None:
        ok_fn = mock.Mock(
            return_value=[Result("hackernews", "Post A", "https://news.ycombinator.com/item?id=1", "s")]
        )

        def boom(*args, **kwargs):
            raise RuntimeError("boom")

        request = make_request(sources=("hackernews", "arxiv"))
        with mock.patch.dict(harvest_runner.SEARCHERS, {"hackernews": ok_fn, "arxiv": boom}):
            results = harvest_runner.run_sources(request)
        by_source = {r.source: r for r in results}
        self.assertEqual("ok", by_source["hackernews"].status)
        self.assertEqual("error", by_source["arxiv"].status)

    def test_results_are_returned_in_request_source_order(self) -> None:
        empty = mock.Mock(return_value=[])
        request = make_request(sources=("arxiv", "hackernews"))
        with mock.patch.dict(harvest_runner.SEARCHERS, {"arxiv": empty, "hackernews": empty}):
            results = harvest_runner.run_sources(request)
        self.assertEqual(["arxiv", "hackernews"], [r.source for r in results])


if __name__ == "__main__":
    unittest.main()
