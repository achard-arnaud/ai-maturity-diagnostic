from __future__ import annotations

import unittest

from app.engagement_ingestion import correlate_touchpoint, ingest_batch, ingest_engagement_event


def _record(source_ref: str, engagement_event_id: str = "ee1", kind: str = "replied") -> dict:
    return {
        "engagement_event_id": engagement_event_id, "conversation_id": "c1", "kind": kind,
        "channel": "email", "occurred_at": "2026-01-04T00:00:00Z", "source_ref": source_ref,
    }


class IngestEngagementEventTests(unittest.TestCase):
    def test_first_ingest_creates_event(self) -> None:
        result = ingest_engagement_event(existing_events=[], **_record("msg-1"))
        self.assertTrue(result.created)
        self.assertEqual("msg-1", result.event["source_ref"])

    def test_reingesting_same_source_ref_is_a_noop(self) -> None:
        first = ingest_engagement_event(existing_events=[], **_record("msg-1"))
        second = ingest_engagement_event(existing_events=[first.event], **_record("msg-1"))
        self.assertFalse(second.created)
        self.assertEqual(first.event, second.event)

    def test_different_source_ref_creates_a_new_event(self) -> None:
        first = ingest_engagement_event(existing_events=[], **_record("msg-1"))
        second = ingest_engagement_event(existing_events=[first.event], **_record("msg-2", engagement_event_id="ee2"))
        self.assertTrue(second.created)


class IngestBatchTests(unittest.TestCase):
    def test_batch_with_duplicate_source_ref_yields_one_creation(self) -> None:
        records = [_record("msg-1"), _record("msg-1", engagement_event_id="ee-dup")]
        results = ingest_batch(records, existing_events=[])
        self.assertEqual([True, False], [r.created for r in results])

    def test_batch_against_prior_existing_events_is_idempotent(self) -> None:
        existing = [ingest_engagement_event(existing_events=[], **_record("msg-1")).event]
        results = ingest_batch([_record("msg-1")], existing_events=existing)
        self.assertEqual([False], [r.created for r in results])

    def test_batch_distinct_records_all_created(self) -> None:
        records = [_record("msg-1"), _record("msg-2", engagement_event_id="ee2")]
        results = ingest_batch(records, existing_events=[])
        self.assertEqual([True, True], [r.created for r in results])

    def test_full_reimport_of_the_same_file_creates_nothing_new(self) -> None:
        # Gold case: 'events idempotents' -- re-running an entire import
        # file after it already landed produces zero new events.
        records = [_record("msg-1"), _record("msg-2", engagement_event_id="ee2")]
        first_pass = ingest_batch(records, existing_events=[])
        stored = [r.event for r in first_pass]
        second_pass = ingest_batch(records, existing_events=stored)
        self.assertEqual([False, False], [r.created for r in second_pass])


def _touchpoint(touchpoint_id: str, channel: str, sent_at: str | None, status: str = "sent") -> dict:
    return {"touchpoint_id": touchpoint_id, "channel": channel, "status": status, "sent_at": sent_at}


class CorrelateTouchpointTests(unittest.TestCase):
    def test_correlates_to_most_recently_sent_matching_channel(self) -> None:
        candidates = [
            _touchpoint("tp1", "email", "2026-01-01T00:00:00Z"),
            _touchpoint("tp2", "email", "2026-01-03T00:00:00Z"),
        ]
        result = correlate_touchpoint(channel="email", occurred_at="2026-01-04T00:00:00Z", candidate_touchpoints=candidates)
        self.assertEqual("tp2", result)

    def test_ignores_touchpoints_on_a_different_channel(self) -> None:
        candidates = [_touchpoint("tp1", "phone", "2026-01-03T00:00:00Z")]
        result = correlate_touchpoint(channel="email", occurred_at="2026-01-04T00:00:00Z", candidate_touchpoints=candidates)
        self.assertIsNone(result)

    def test_ignores_touchpoints_not_yet_sent(self) -> None:
        candidates = [_touchpoint("tp1", "email", None, status="prepared")]
        result = correlate_touchpoint(channel="email", occurred_at="2026-01-04T00:00:00Z", candidate_touchpoints=candidates)
        self.assertIsNone(result)

    def test_ignores_touchpoints_sent_after_the_event(self) -> None:
        candidates = [_touchpoint("tp1", "email", "2026-01-05T00:00:00Z")]
        result = correlate_touchpoint(channel="email", occurred_at="2026-01-04T00:00:00Z", candidate_touchpoints=candidates)
        self.assertIsNone(result)

    def test_no_candidates_returns_none_never_a_guess(self) -> None:
        result = correlate_touchpoint(channel="email", occurred_at="2026-01-04T00:00:00Z", candidate_touchpoints=[])
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
