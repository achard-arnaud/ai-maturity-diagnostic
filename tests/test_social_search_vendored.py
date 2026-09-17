"""Contract tests for scripts/social_search/, vendored verbatim from
achard-arnaud/search-social-networks (see scripts/social_search/NOTICE.md
and docs/ADR-011-evidence-acquisition-search.md). These are adapted from
that repository's own tests/test_search_social_networks.py -- covering
the reusable library behaviors this repo depends on, not the upstream
CLI/doctor entrypoint, which was not vendored (ADR-011 S1: EXTRACT_PATTERN,
not import).

If a future re-vendor of scripts/social_search/ ever breaks one of these,
that is a real regression in behavior this repo's harvest wrapper relies
on -- not a false positive to silence.
"""

from __future__ import annotations

import unittest
from unittest import mock

from scripts.social_search import SEARCHERS, SELECTED_SOURCES, Result, dedupe
from scripts.social_search import linkedin, youtube


class VendoredSourceRegistryTests(unittest.TestCase):
    def test_selected_sources_match_registered_searchers(self) -> None:
        self.assertEqual(set(SELECTED_SOURCES), set(SEARCHERS))

    def test_every_searcher_has_the_uniform_call_shape(self) -> None:
        # f(query, days, limit, enrich, allow_commercial=False) -> list[Result]
        import inspect

        for name, fn in SEARCHERS.items():
            params = list(inspect.signature(fn).parameters)
            self.assertEqual(params[:4], ["query", "days", "limit", "enrich"], name)


class DedupeTests(unittest.TestCase):
    def test_dedupe_prefers_higher_score_and_preserves_enrichment(self) -> None:
        low = Result("web", "a", "https://example.com/x?utm_source=a", score=0.4, metadata={"top_comments": [1]})
        high = Result("web", "b", "https://example.com/x", score=0.9)
        out = dedupe([low, high], 10)
        self.assertEqual(1, len(out))
        self.assertEqual("b", out[0].title)
        # merge_meta must carry the lower-scored hit's enrichment forward.
        self.assertEqual([1], out[0].metadata["top_comments"])


class LinkedInEpistemicDisciplineTests(unittest.TestCase):
    """Guards the exact caveats app/acquisition_policy.py's grading ceiling
    (ADR-011 S4) relies on already being present at the source."""

    def test_public_lane_flags_are_never_claims_of_authenticated_access(self) -> None:
        with mock.patch.object(
            linkedin,
            "web_index",
            return_value=[Result("linkedin", "hit", "https://linkedin.com/posts/a", score=0.5)],
        ):
            results = linkedin._search_linkedin_public("acme", 30, 5)
        self.assertTrue(results)
        for result in results:
            self.assertFalse(result.metadata["authenticated_linkedin_access"])
            self.assertFalse(result.metadata["live_role_validation"])
            self.assertFalse(result.metadata["canonical_identity_resolution"])

    def test_public_lane_always_runs_even_when_commercial_path_is_allowed(self) -> None:
        public = [Result("linkedin", "public", "https://linkedin.com/posts/a", score=0.5)]
        with mock.patch.object(linkedin, "_search_linkedin_public", return_value=public) as pub, mock.patch.object(
            linkedin, "_search_linkedin_sc", return_value=[]
        ) as sc, mock.patch.dict("os.environ", {"SCRAPECREATORS_API_KEY": "key"}):
            out = linkedin.search_linkedin("acme", 30, 5, True, allow_commercial=True)
        pub.assert_called_once()
        sc.assert_called_once()
        self.assertEqual(1, len(out))

    def test_commercial_lane_never_runs_without_explicit_allow_commercial(self) -> None:
        public = [Result("linkedin", "public", "https://linkedin.com/posts/a", score=0.5)]
        with mock.patch.object(linkedin, "_search_linkedin_public", return_value=public), mock.patch.object(
            linkedin, "_search_linkedin_sc"
        ) as sc, mock.patch.dict("os.environ", {"SCRAPECREATORS_API_KEY": "key"}):
            linkedin.search_linkedin("acme", 30, 5, True, allow_commercial=False)
        sc.assert_not_called()


class YoutubeCascadeTests(unittest.TestCase):
    def test_transcript_cascade_tries_public_before_commercial(self) -> None:
        with mock.patch.object(youtube, "_youtube_transcript_ytdlp", return_value="public transcript") as ytdlp, \
             mock.patch.object(youtube, "_youtube_transcript_direct") as direct, \
             mock.patch.object(youtube, "_youtube_transcript_sc") as sc:
            text, method = youtube._youtube_transcript("https://youtube.com/watch?v=vid123", allow_commercial=True)
        ytdlp.assert_called_once()
        direct.assert_not_called()
        sc.assert_not_called()
        self.assertEqual("public transcript", text)
        self.assertEqual("yt-dlp", method)


if __name__ == "__main__":
    unittest.main()
