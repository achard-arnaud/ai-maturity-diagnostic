from __future__ import annotations

import unittest

from app.fit_scoring import (
    FitScoringError,
    compute_coverage,
    compute_explainable_score,
    validate_alternatives,
    validate_counter_evidence,
)


def _check(dimension: str, covered: bool) -> dict:
    return {"dimension": dimension, "covered": covered, "rationale": "reviewed"}


class CoverageTests(unittest.TestCase):
    def test_no_checks_is_zero_coverage(self) -> None:
        result = compute_coverage([])
        self.assertEqual(0.0, result.coverage_ratio)

    def test_all_covered_is_full_coverage(self) -> None:
        result = compute_coverage([_check("problem", True), _check("impact", True)])
        self.assertEqual(1.0, result.coverage_ratio)
        self.assertEqual((), result.gaps)

    def test_partial_coverage_lists_gaps(self) -> None:
        result = compute_coverage([_check("problem", True), _check("impact", False)])
        self.assertEqual(0.5, result.coverage_ratio)
        self.assertEqual(("impact",), result.gaps)
        self.assertEqual(("problem",), result.covered)


class ExplainableScoreTests(unittest.TestCase):
    def test_score_carries_a_factor_per_dimension(self) -> None:
        checks = [_check("problem", True), _check("impact", False)]
        result = compute_explainable_score(checks)
        self.assertEqual(2, len(result.factors))

    def test_explanation_is_human_readable_gold_case(self) -> None:
        checks = [_check("problem", True), _check("impact", False)]
        result = compute_explainable_score(checks)
        self.assertIn("problem", result.explanation)
        self.assertIn("covered", result.explanation)
        self.assertIn("impact", result.explanation)
        self.assertIn("gap", result.explanation)

    def test_uncovered_dimension_contributes_zero(self) -> None:
        result = compute_explainable_score([_check("problem", False)])
        self.assertEqual(0.0, result.factors[0].contribution)

    def test_covered_dimension_contributes_its_weight(self) -> None:
        result = compute_explainable_score([_check("problem", True)], weights={"problem": 0.3})
        self.assertEqual(0.3, result.factors[0].contribution)

    def test_calibration_more_coverage_never_lowers_the_score(self) -> None:
        # Gold-set calibration case: adding a covered dimension can only
        # raise (or leave unchanged) the total score, never lower it.
        base = compute_explainable_score([_check("problem", True)])
        more_covered = compute_explainable_score([_check("problem", True), _check("impact", True)])
        self.assertGreaterEqual(more_covered.value, base.value)

    def test_no_dimensions_has_a_readable_fallback_explanation(self) -> None:
        result = compute_explainable_score([])
        self.assertEqual("no dimensions evaluated", result.explanation)
        self.assertEqual(0.0, result.value)


class AlternativesAndCounterEvidenceTests(unittest.TestCase):
    def test_valid_alternatives_pass(self) -> None:
        validate_alternatives([{"description": "Use a lighter-weight tool", "rationale": "lower cost"}])

    def test_alternative_missing_description_is_rejected(self) -> None:
        with self.assertRaises(FitScoringError):
            validate_alternatives([{"description": "", "rationale": "lower cost"}])

    def test_alternative_missing_rationale_is_rejected(self) -> None:
        with self.assertRaises(FitScoringError):
            validate_alternatives([{"description": "Use a lighter tool", "rationale": ""}])

    def test_valid_counter_evidence_passes(self) -> None:
        validate_counter_evidence([{"statement": "Customer already has a competing tool in production"}])

    def test_empty_counter_evidence_statement_is_rejected(self) -> None:
        with self.assertRaises(FitScoringError):
            validate_counter_evidence([{"statement": "  "}])


if __name__ == "__main__":
    unittest.main()
