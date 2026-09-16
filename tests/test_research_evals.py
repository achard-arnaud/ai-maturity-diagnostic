from __future__ import annotations

import unittest

from app.research_evals import (
    EvalThresholds,
    check_contamination,
    compute_coverage,
    compute_factuality,
    run_evals,
)


def _case(research_case_id: str) -> dict:
    return {"research_case_id": research_case_id}


def _claim(claim_id: str, research_case_id: str, claim_type: str = "fact", **kwargs) -> dict:
    base = {
        "claim_id": claim_id,
        "research_case_id": research_case_id,
        "claim_type": claim_type,
        "statement": "the company raised a Series B in 2025",
        "status": "active",
        "evidence_ids": ["e1"],
        "derived_from_claim_ids": [],
    }
    base.update(kwargs)
    return base


def _evidence(evidence_id: str = "e1", grade: str = "P1") -> dict:
    return {"evidence_id": evidence_id, "evidence_grade": grade}


class ContaminationTests(unittest.TestCase):
    def test_clean_statement_passes(self) -> None:
        claims = [_claim("c1", "rc1")]
        self.assertEqual([], check_contamination(claims))

    def test_statement_mentioning_product_is_flagged(self) -> None:
        claims = [_claim("c1", "rc1", statement="this account might fit our product catalog")]
        self.assertEqual(["c1"], check_contamination(claims))

    def test_case_insensitive_match(self) -> None:
        claims = [_claim("c1", "rc1", statement="Discussed PRICING options")]
        self.assertEqual(["c1"], check_contamination(claims))


class CoverageTests(unittest.TestCase):
    def test_no_cases_is_zero_coverage(self) -> None:
        self.assertEqual(0.0, compute_coverage([], {}))

    def test_all_cases_complete_is_full_coverage(self) -> None:
        cases = [_case("rc1"), _case("rc2")]
        claims_by_case = {
            "rc1": [_claim("c1", "rc1")],
            "rc2": [_claim("c2", "rc2")],
        }
        self.assertEqual(1.0, compute_coverage(cases, claims_by_case))

    def test_half_complete_is_half_coverage(self) -> None:
        cases = [_case("rc1"), _case("rc2")]
        claims_by_case = {"rc1": [_claim("c1", "rc1")]}
        self.assertEqual(0.5, compute_coverage(cases, claims_by_case))


class FactualityTests(unittest.TestCase):
    def test_no_fact_claims_is_zero_factuality(self) -> None:
        claims = [_claim("c1", "rc1", claim_type="hypothesis", hypothesis_owner="a", hypothesis_due_at="2026-01-01")]
        self.assertEqual(0.0, compute_factuality(claims, evidence_by_id={}, claims_by_id={}))

    def test_valid_fact_claim_is_full_factuality(self) -> None:
        claims = [_claim("c1", "rc1")]
        evidence_by_id = {"e1": _evidence()}
        self.assertEqual(1.0, compute_factuality(claims, evidence_by_id=evidence_by_id, claims_by_id={}))

    def test_invalid_fact_claim_lowers_factuality(self) -> None:
        claims = [_claim("c1", "rc1", evidence_ids=["missing"])]
        self.assertEqual(0.0, compute_factuality(claims, evidence_by_id={}, claims_by_id={}))


class RunEvalsGoldSetThresholdTests(unittest.TestCase):
    def test_clean_gold_set_passes_default_thresholds(self) -> None:
        cases = [_case("rc1")]
        claims = [_claim("c1", "rc1")]
        evidence_by_id = {"e1": _evidence()}
        report = run_evals(cases, claims, evidence_by_id=evidence_by_id)
        self.assertTrue(report.passed)
        self.assertEqual((), report.failures)

    def test_contaminated_gold_set_fails_regardless_of_other_metrics(self) -> None:
        cases = [_case("rc1")]
        claims = [_claim("c1", "rc1", statement="great fit for our product catalog")]
        evidence_by_id = {"e1": _evidence()}
        report = run_evals(cases, claims, evidence_by_id=evidence_by_id)
        self.assertFalse(report.passed)
        self.assertIn("c1", report.contaminated_claim_ids)

    def test_low_coverage_fails(self) -> None:
        cases = [_case("rc1"), _case("rc2"), _case("rc3")]
        claims = [_claim("c1", "rc1")]
        evidence_by_id = {"e1": _evidence()}
        report = run_evals(cases, claims, evidence_by_id=evidence_by_id)
        self.assertFalse(report.passed)
        self.assertTrue(any("coverage" in f for f in report.failures))

    def test_low_factuality_fails(self) -> None:
        cases = [_case("rc1")]
        claims = [_claim("c1", "rc1", evidence_ids=["missing"])]
        evidence_by_id = {}
        report = run_evals(cases, claims, evidence_by_id=evidence_by_id)
        self.assertFalse(report.passed)
        self.assertTrue(any("factuality" in f for f in report.failures))

    def test_custom_thresholds_are_respected(self) -> None:
        cases = [_case("rc1"), _case("rc2")]
        claims = [_claim("c1", "rc1")]
        evidence_by_id = {"e1": _evidence()}
        lenient = EvalThresholds(max_contamination=0, min_coverage=0.4, min_factuality=0.5)
        report = run_evals(cases, claims, evidence_by_id=evidence_by_id, thresholds=lenient)
        self.assertTrue(report.passed)


if __name__ == "__main__":
    unittest.main()
