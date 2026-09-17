from __future__ import annotations

import unittest

from jsonschema import Draft202012Validator

from app.acquisition_policy import (
    AcquisitionPolicyError,
    EvidenceCandidate,
    SearchRequest,
    assert_no_demand_or_fit_fields,
    build_evidence_candidate,
    candidate_to_signal,
)
from app.signal_policy import assert_no_demand_fields, load_signal_schema


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


def make_candidate(**overrides):
    defaults = dict(
        candidate_id="cand-1",
        workspace_id="acme-ws",
        space="discover",
        source_name="hackernews",
        locator="https://news.ycombinator.com/item?id=1",
        title="Some company ships an AI feature",
        snippet="a snippet",
    )
    defaults.update(overrides)
    return build_evidence_candidate(**defaults)


class SearchRequestTests(unittest.TestCase):
    def test_valid_request_constructs(self) -> None:
        request = make_request()
        self.assertEqual(request.workspace_id, "acme-ws")
        self.assertEqual(request.sources, ("hackernews",))

    def test_missing_workspace_id_is_rejected(self) -> None:
        with self.assertRaises(AcquisitionPolicyError):
            make_request(workspace_id="  ")

    def test_missing_query_is_rejected(self) -> None:
        with self.assertRaises(AcquisitionPolicyError):
            make_request(query="")

    def test_missing_requested_by_is_rejected(self) -> None:
        with self.assertRaises(AcquisitionPolicyError):
            make_request(requested_by="")

    def test_unknown_space_is_rejected(self) -> None:
        with self.assertRaises(AcquisitionPolicyError):
            make_request(space="pipeline")

    def test_empty_sources_is_rejected(self) -> None:
        # Program invariant: never fan out to every source by default.
        with self.assertRaises(AcquisitionPolicyError):
            make_request(sources=())

    def test_unknown_source_is_rejected(self) -> None:
        with self.assertRaises(AcquisitionPolicyError):
            make_request(sources=("myspace",))

    def test_linkedin_outside_targets_space_is_rejected(self) -> None:
        with self.assertRaises(AcquisitionPolicyError):
            make_request(sources=("linkedin",), space="discover")
        with self.assertRaises(AcquisitionPolicyError):
            make_request(sources=("linkedin",), space="research")

    def test_linkedin_inside_targets_space_is_accepted(self) -> None:
        request = make_request(sources=("linkedin",), space="targets")
        self.assertEqual(request.sources, ("linkedin",))

    def test_non_linkedin_source_inside_targets_space_is_rejected(self) -> None:
        with self.assertRaises(AcquisitionPolicyError):
            make_request(sources=("hackernews",), space="targets")

    def test_non_positive_days_or_limit_is_rejected(self) -> None:
        with self.assertRaises(AcquisitionPolicyError):
            make_request(days=0)
        with self.assertRaises(AcquisitionPolicyError):
            make_request(limit=0)


class AssertNoDemandOrFitFieldsTests(unittest.TestCase):
    def test_clean_payload_passes(self) -> None:
        assert_no_demand_or_fit_fields({"foo": "bar"})

    def test_demand_only_field_is_rejected(self) -> None:
        with self.assertRaises(AcquisitionPolicyError):
            assert_no_demand_or_fit_fields({"sponsor": "someone"})

    def test_fit_or_target_only_field_is_rejected(self) -> None:
        with self.assertRaises(AcquisitionPolicyError):
            assert_no_demand_or_fit_fields({"verdict": "pursue"})
        with self.assertRaises(AcquisitionPolicyError):
            assert_no_demand_or_fit_fields({"score": 87})
        with self.assertRaises(AcquisitionPolicyError):
            assert_no_demand_or_fit_fields({"target_plan_id": "tp-1"})


class BuildEvidenceCandidateTests(unittest.TestCase):
    def test_valid_candidate_is_built(self) -> None:
        candidate = make_candidate()
        self.assertIsInstance(candidate, EvidenceCandidate)
        self.assertEqual(candidate.evidence_grade, "U1")
        self.assertEqual(candidate.epistemic_status, "hypothesis")
        self.assertTrue(candidate.dedup_key.startswith("sig_"))

    def test_missing_locator_is_rejected(self) -> None:
        # Epic 14 S01 test: "missing provenance rejected".
        with self.assertRaises(AcquisitionPolicyError):
            make_candidate(locator="")
        with self.assertRaises(AcquisitionPolicyError):
            make_candidate(locator="   ")

    def test_missing_title_and_snippet_is_rejected(self) -> None:
        with self.assertRaises(AcquisitionPolicyError):
            make_candidate(title="", snippet="")

    def test_unknown_source_is_rejected(self) -> None:
        with self.assertRaises(AcquisitionPolicyError):
            make_candidate(source_name="myspace")

    def test_unknown_space_is_rejected(self) -> None:
        with self.assertRaises(AcquisitionPolicyError):
            make_candidate(space="pipeline")

    def test_grade_above_uncorroborated_ceiling_is_rejected(self) -> None:
        # ADR-011 S4: a freshly harvested candidate can never be graded
        # P1/P2/W1 without prior corroboration this module cannot see.
        for grade in ("P1", "P2", "W1"):
            with self.assertRaises(AcquisitionPolicyError):
                make_candidate(evidence_grade=grade)

    def test_epistemic_status_above_ceiling_is_rejected(self) -> None:
        with self.assertRaises(AcquisitionPolicyError):
            make_candidate(epistemic_status="fact")

    def test_demand_or_fit_field_in_metadata_is_rejected(self) -> None:
        # Epic 14 S01 test: "search result cannot create Demand/Fit/Target
        # readiness" -- even smuggled through free-form metadata.
        with self.assertRaises(AcquisitionPolicyError):
            make_candidate(metadata={"sponsor": "someone"})
        with self.assertRaises(AcquisitionPolicyError):
            make_candidate(metadata={"verdict": "pursue"})

    def test_excerpt_is_truncated_to_schema_max_length(self) -> None:
        candidate = make_candidate(title="x" * 2000, snippet="")
        self.assertLessEqual(len(candidate.excerpt), 1000)

    def test_dedup_key_is_deterministic_for_same_inputs(self) -> None:
        first = make_candidate()
        second = make_candidate(candidate_id="cand-2")
        self.assertEqual(first.dedup_key, second.dedup_key)

    def test_dedup_key_differs_for_different_locator(self) -> None:
        first = make_candidate()
        second = make_candidate(locator="https://news.ycombinator.com/item?id=2")
        self.assertNotEqual(first.dedup_key, second.dedup_key)

    def test_source_specific_metadata_is_preserved(self) -> None:
        # ADR-011 S4/harvest note: epistemic caveat flags like
        # live_role_validation must survive onto the candidate verbatim.
        candidate = make_candidate(
            source_name="linkedin",
            space="targets",
            metadata={"live_role_validation": False, "canonical_identity_resolution": False},
        )
        self.assertEqual(candidate.metadata["live_role_validation"], False)
        self.assertEqual(candidate.metadata["canonical_identity_resolution"], False)

    def test_default_observed_at_is_set_when_omitted(self) -> None:
        candidate = make_candidate()
        self.assertIsNotNone(candidate.observed_at)

    def test_source_kind_is_always_public_regardless_of_acquisition_source(self) -> None:
        # contracts/evidence_v1.schema.yaml + signal_v1.schema.yaml's
        # source.kind enum is {public, manual, import} -- never the
        # specific search-social-networks channel name.
        candidate = make_candidate(source_name="linkedin", space="targets")
        self.assertEqual("public", candidate.source_kind)
        self.assertEqual("linkedin", candidate.acquisition_source)


class CandidateToSignalTests(unittest.TestCase):
    def test_produces_a_schema_shaped_signal_dict(self) -> None:
        candidate = make_candidate()
        signal = candidate_to_signal(candidate)
        self.assertEqual(signal["workspace_id"], candidate.workspace_id)
        self.assertEqual(signal["source"], {"kind": "public", "ref": candidate.locator})
        self.assertEqual(signal["status"], "new")
        self.assertIsNone(signal["company_entity_id"])
        self.assertEqual(signal["dedup_key"], candidate.dedup_key)
        self.assertEqual(signal["provenance"]["evidence_grade"], candidate.evidence_grade)
        self.assertEqual(signal["provenance"]["epistemic_status"], candidate.epistemic_status)
        # Must pass the same defense-in-depth guard every other signal does.
        assert_no_demand_fields(signal)
        Draft202012Validator(load_signal_schema()).validate(signal)

    def test_signal_id_is_unique_per_call(self) -> None:
        candidate = make_candidate()
        first = candidate_to_signal(candidate)
        second = candidate_to_signal(candidate)
        self.assertNotEqual(first["signal_id"], second["signal_id"])


if __name__ == "__main__":
    unittest.main()
