from __future__ import annotations

import unittest

from jsonschema import Draft202012Validator

from app.signal_ingestion import SignalIngestionError, ingest_import, ingest_manual, ingest_public
from app.signal_policy import load_signal_schema


class PublicAdapterTests(unittest.TestCase):
    def test_produces_a_schema_valid_signal(self) -> None:
        signal = ingest_public(
            "ws-a", url="https://example.com/news/1", content="Acme raises Series B", fetched_at="2026-06-01T00:00:00+00:00"
        )
        Draft202012Validator(load_signal_schema()).validate(signal)
        self.assertEqual("new", signal["status"])
        self.assertEqual("public", signal["source"]["kind"])

    def test_missing_url_fails(self) -> None:
        with self.assertRaises(SignalIngestionError):
            ingest_public("ws-a", url="", content="text", fetched_at="2026-06-01T00:00:00+00:00")

    def test_missing_content_fails(self) -> None:
        with self.assertRaises(SignalIngestionError):
            ingest_public("ws-a", url="https://example.com/1", content="", fetched_at="2026-06-01T00:00:00+00:00")

    def test_no_live_fetch_is_performed(self) -> None:
        # "core sans integration": passing an unreachable/fake URL must
        # never raise a network error -- the adapter only ever consumes
        # already-provided content.
        signal = ingest_public(
            "ws-a", url="https://this-domain-does-not-exist.invalid/x", content="pre-fetched text", fetched_at="2026-06-01T00:00:00+00:00"
        )
        self.assertEqual("https://this-domain-does-not-exist.invalid/x", signal["source"]["ref"])


class ManualAdapterTests(unittest.TestCase):
    def test_produces_a_schema_valid_signal(self) -> None:
        signal = ingest_manual("ws-a", operator="alice@example.com", note="Mentioned budget freeze on a call", observed_at="2026-06-01T00:00:00+00:00")
        Draft202012Validator(load_signal_schema()).validate(signal)
        self.assertEqual("manual", signal["source"]["kind"])

    def test_missing_operator_fails(self) -> None:
        with self.assertRaises(SignalIngestionError):
            ingest_manual("ws-a", operator="", note="text", observed_at="2026-06-01T00:00:00+00:00")

    def test_two_operators_same_event_do_not_collide_on_dedup(self) -> None:
        first = ingest_manual("ws-a", operator="alice@example.com", note="same event", observed_at="2026-06-01T00:00:00+00:00")
        second = ingest_manual("ws-a", operator="bob@example.com", note="same event", observed_at="2026-06-01T00:00:00+00:00")
        self.assertNotEqual(first["dedup_key"], second["dedup_key"])


class ImportAdapterTests(unittest.TestCase):
    def test_produces_schema_valid_signals(self) -> None:
        rows = [
            {"content": "Signal A", "observed_at": "2026-06-01T00:00:00+00:00"},
            {"content": "Signal B", "observed_at": "2026-06-02T00:00:00+00:00"},
        ]
        signals = ingest_import("ws-a", batch_ref="batch-2026-06", rows=rows)
        self.assertEqual(2, len(signals))
        validator = Draft202012Validator(load_signal_schema())
        for signal in signals:
            validator.validate(signal)

    def test_empty_batch_fails(self) -> None:
        with self.assertRaises(SignalIngestionError):
            ingest_import("ws-a", batch_ref="batch-1", rows=[])

    def test_missing_batch_ref_fails(self) -> None:
        with self.assertRaises(SignalIngestionError):
            ingest_import("ws-a", batch_ref="", rows=[{"content": "x", "observed_at": "2026-06-01T00:00:00+00:00"}])

    def test_row_missing_content_fails_the_whole_batch(self) -> None:
        rows = [
            {"content": "Signal A", "observed_at": "2026-06-01T00:00:00+00:00"},
            {"content": "", "observed_at": "2026-06-02T00:00:00+00:00"},
        ]
        with self.assertRaises(SignalIngestionError):
            ingest_import("ws-a", batch_ref="batch-2026-06", rows=rows)

    def test_row_missing_observed_at_fails_the_whole_batch(self) -> None:
        rows = [{"content": "Signal A", "observed_at": ""}]
        with self.assertRaises(SignalIngestionError):
            ingest_import("ws-a", batch_ref="batch-2026-06", rows=rows)

    def test_rows_within_a_batch_have_distinct_source_refs(self) -> None:
        rows = [
            {"content": "Signal A", "observed_at": "2026-06-01T00:00:00+00:00"},
            {"content": "Signal A", "observed_at": "2026-06-01T00:00:00+00:00"},
        ]
        signals = ingest_import("ws-a", batch_ref="batch-2026-06", rows=rows)
        self.assertNotEqual(signals[0]["source"]["ref"], signals[1]["source"]["ref"])


if __name__ == "__main__":
    unittest.main()
