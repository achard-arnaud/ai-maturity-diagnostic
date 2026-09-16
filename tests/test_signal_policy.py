from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from jsonschema import Draft202012Validator

from app.signal_policy import (
    SignalPolicyError,
    assert_no_demand_fields,
    can_transition,
    compute_dedup_key,
    is_expired,
    load_signal_schema,
)


def _signal(**overrides) -> dict:
    base = {
        "signal_id": "sig_1",
        "workspace_id": "ws-a",
        "source": {"kind": "public", "ref": "https://example.com/news/1"},
        "observed_at": "2026-06-01T00:00:00+00:00",
        "status": "new",
        "company_entity_id": None,
        "dedup_key": compute_dedup_key("public", "https://example.com/news/1", "content"),
        "freshness": {"stale_after_days": 30},
        "provenance": {"source_refs": ["https://example.com/news/1"], "epistemic_status": "fact", "evidence_grade": "P1"},
    }
    base.update(overrides)
    return base


class SignalSchemaTests(unittest.TestCase):
    def test_schema_is_valid_json_schema(self) -> None:
        Draft202012Validator.check_schema(load_signal_schema())

    def test_well_formed_signal_validates(self) -> None:
        Draft202012Validator(load_signal_schema()).validate(_signal())

    def test_demand_only_field_fails_schema_validation(self) -> None:
        # additionalProperties: false means a demand-only field is
        # rejected by the schema itself, not just the policy guard below.
        signal = _signal()
        signal["budget"] = {"known": True, "amount": 100000}
        with self.assertRaises(Exception):
            Draft202012Validator(load_signal_schema()).validate(signal)


class DemandContaminationGuardTests(unittest.TestCase):
    def test_clean_signal_passes(self) -> None:
        assert_no_demand_fields(_signal())

    def test_sponsor_field_is_rejected(self) -> None:
        with self.assertRaises(SignalPolicyError):
            assert_no_demand_fields(_signal(sponsor="CTO"))

    def test_multiple_demand_fields_are_all_reported(self) -> None:
        with self.assertRaisesRegex(SignalPolicyError, "budget.*urgency|urgency.*budget"):
            assert_no_demand_fields(_signal(budget={}, urgency="high"))


class DedupKeyTests(unittest.TestCase):
    def test_same_inputs_produce_same_key(self) -> None:
        key_1 = compute_dedup_key("public", "https://example.com/1", "same content")
        key_2 = compute_dedup_key("public", "https://example.com/1", "same content")
        self.assertEqual(key_1, key_2)

    def test_different_source_kind_produces_different_key(self) -> None:
        # Two adapters (public vs manual) observing the same ref+content
        # are still deduped together by content, not artificially split --
        # unless the ref itself differs.
        key_public = compute_dedup_key("public", "ref-1", "content")
        key_manual = compute_dedup_key("manual", "ref-1", "content")
        self.assertNotEqual(key_public, key_manual)

    def test_empty_ref_is_rejected(self) -> None:
        with self.assertRaises(SignalPolicyError):
            compute_dedup_key("public", "", "content")


class ExpiryTests(unittest.TestCase):
    def test_fresh_signal_is_not_expired(self) -> None:
        signal = _signal(observed_at="2026-06-01T00:00:00+00:00", freshness={"stale_after_days": 30})
        self.assertFalse(is_expired(signal, as_of=datetime(2026, 6, 15, tzinfo=timezone.utc)))

    def test_signal_past_freshness_window_is_expired(self) -> None:
        signal = _signal(observed_at="2026-06-01T00:00:00+00:00", freshness={"stale_after_days": 30})
        self.assertTrue(is_expired(signal, as_of=datetime(2026, 8, 1, tzinfo=timezone.utc)))

    def test_boundary_exactly_at_window_is_not_yet_expired(self) -> None:
        observed = datetime(2026, 6, 1, tzinfo=timezone.utc)
        signal = _signal(observed_at=observed.isoformat(), freshness={"stale_after_days": 30})
        self.assertFalse(is_expired(signal, as_of=observed + timedelta(days=30)))

    def test_one_second_past_window_is_expired(self) -> None:
        observed = datetime(2026, 6, 1, tzinfo=timezone.utc)
        signal = _signal(observed_at=observed.isoformat(), freshness={"stale_after_days": 30})
        self.assertTrue(is_expired(signal, as_of=observed + timedelta(days=30, seconds=1)))

    def test_naive_observed_at_is_treated_as_utc(self) -> None:
        signal = _signal(observed_at="2026-06-01T00:00:00", freshness={"stale_after_days": 30})
        self.assertFalse(is_expired(signal, as_of=datetime(2026, 6, 15, tzinfo=timezone.utc)))


class LifecycleTransitionTests(unittest.TestCase):
    def test_new_to_reviewed_is_legal(self) -> None:
        self.assertTrue(can_transition("new", "reviewed"))

    def test_reviewed_to_linked_is_legal(self) -> None:
        self.assertTrue(can_transition("reviewed", "linked"))

    def test_reviewed_to_dismissed_is_legal(self) -> None:
        self.assertTrue(can_transition("reviewed", "dismissed"))

    def test_new_to_linked_directly_is_illegal(self) -> None:
        # Must pass through "reviewed" -- no shortcut from new straight to linked.
        self.assertFalse(can_transition("new", "linked"))

    def test_any_non_terminal_status_can_expire(self) -> None:
        for status in ("new", "reviewed", "linked"):
            self.assertTrue(can_transition(status, "expired"))

    def test_dismissed_and_expired_are_terminal(self) -> None:
        self.assertFalse(can_transition("dismissed", "reviewed"))
        self.assertFalse(can_transition("expired", "reviewed"))

    def test_unknown_status_raises(self) -> None:
        with self.assertRaises(SignalPolicyError):
            can_transition("new", "bogus")


if __name__ == "__main__":
    unittest.main()
