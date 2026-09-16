from __future__ import annotations

import dataclasses
import unittest
from datetime import datetime, timedelta, timezone

from app.signal_screening import ResearchPriorityScore, compute_research_priority_score

FORBIDDEN_FIT_WORDS = ("fit", "offer", "recommend", "product", "catalog")


def _signal(**overrides) -> dict:
    base = {
        "signal_id": "sig_1",
        "workspace_id": "ws-a",
        "source": {"kind": "public", "ref": "https://example.com/1"},
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "status": "new",
        "company_entity_id": None,
        "dedup_key": "sig_key",
        "freshness": {"stale_after_days": 30},
        "provenance": {"source_refs": ["https://example.com/1"], "epistemic_status": "fact", "evidence_grade": "P1"},
    }
    base.update(overrides)
    return base


class HardExclusionTests(unittest.TestCase):
    def test_dismissed_signal_is_excluded_regardless_of_evidence(self) -> None:
        signal = _signal(status="dismissed", provenance={"source_refs": ["x"], "epistemic_status": "fact", "evidence_grade": "P1"})
        result = compute_research_priority_score(signal)
        self.assertTrue(result.excluded)
        self.assertEqual(0.0, result.score)
        self.assertIn("dismissed", result.exclusion_reason)

    def test_expired_signal_is_excluded_even_with_top_evidence_grade(self) -> None:
        old_observed = (datetime.now(timezone.utc) - timedelta(days=100)).isoformat()
        signal = _signal(observed_at=old_observed, freshness={"stale_after_days": 30}, provenance={"source_refs": ["x"], "epistemic_status": "fact", "evidence_grade": "P1"})
        result = compute_research_priority_score(signal)
        self.assertTrue(result.excluded)
        self.assertEqual(0.0, result.score)

    def test_exclusion_is_absolute_not_overridable_by_score(self) -> None:
        # A hard exclusion always wins even for the theoretically
        # highest-scoring signal (manual source, P1 evidence).
        signal = _signal(status="expired", source={"kind": "manual", "ref": "operator:x"}, provenance={"source_refs": ["x"], "epistemic_status": "fact", "evidence_grade": "P1"})
        result = compute_research_priority_score(signal)
        self.assertTrue(result.excluded)


class ScoreExplicabilityTests(unittest.TestCase):
    def test_score_carries_a_non_empty_factor_breakdown(self) -> None:
        result = compute_research_priority_score(_signal())
        self.assertGreater(len(result.factors), 0)
        self.assertEqual(result.score, round(sum(f.contribution for f in result.factors), 4))

    def test_explanation_is_serializable_and_named(self) -> None:
        result = compute_research_priority_score(_signal())
        explanation = result.explanation()
        names = {item["name"] for item in explanation}
        self.assertIn("evidence_grade", names)
        self.assertIn("source_kind", names)

    def test_higher_evidence_grade_scores_higher_all_else_equal(self) -> None:
        p1 = compute_research_priority_score(_signal(provenance={"source_refs": ["x"], "epistemic_status": "fact", "evidence_grade": "P1"}))
        n0 = compute_research_priority_score(_signal(provenance={"source_refs": ["x"], "epistemic_status": "unknown", "evidence_grade": "N0"}))
        self.assertGreater(p1.score, n0.score)

    def test_manual_source_scores_higher_than_import_all_else_equal(self) -> None:
        manual = compute_research_priority_score(_signal(source={"kind": "manual", "ref": "operator:x"}))
        imported = compute_research_priority_score(_signal(source={"kind": "import", "ref": "batch#0"}))
        self.assertGreater(manual.score, imported.score)


class NeverAFitScoreTests(unittest.TestCase):
    """Gold-set style structural guard: whatever this module ever returns
    must never resemble a product-fit or offer score, per Epic 00
    Principle #2 and this Sprint's own stop condition.
    """

    def test_result_type_has_no_fit_or_offer_shaped_field(self) -> None:
        field_names = {f.name for f in dataclasses.fields(ResearchPriorityScore)}
        for forbidden in FORBIDDEN_FIT_WORDS:
            for name in field_names:
                self.assertNotIn(forbidden, name.lower(), f"field {name!r} looks fit/offer-shaped")

    def test_factor_names_never_reference_product_or_fit(self) -> None:
        result = compute_research_priority_score(_signal())
        for factor in result.factors:
            for forbidden in FORBIDDEN_FIT_WORDS:
                self.assertNotIn(forbidden, factor.name.lower())

    def test_score_is_bounded_to_zero_one(self) -> None:
        result = compute_research_priority_score(_signal(provenance={"source_refs": ["x"], "epistemic_status": "fact", "evidence_grade": "P1"}, source={"kind": "manual", "ref": "operator:x"}))
        self.assertGreaterEqual(result.score, 0.0)
        self.assertLessEqual(result.score, 1.0)


if __name__ == "__main__":
    unittest.main()
