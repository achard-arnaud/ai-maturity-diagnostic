from __future__ import annotations

import unittest

from app.learning_experiments import ExperimentPlan, evaluate_experiment


class LearningExperimentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.plan = ExperimentPlan("exp-1", "lp-1", "quality_pass_rate", "increase", 100, 0.02, 0.05, "baseline/v1", "canary/v2")

    def measurement(self, value: float, sample_size: int = 100) -> dict:
        return {"metric_id": "quality_pass_rate", "value": value, "sample_size": sample_size}

    def test_measured_improvement_promotes_canary(self) -> None:
        result = evaluate_experiment(self.plan, baseline=self.measurement(0.80), canary=self.measurement(0.86), nrt_drift=0.01)
        self.assertEqual("promote", result["decision"])
        self.assertFalse(result["rollback_required"])
        self.assertEqual("lp-1", result["experiment"]["proposal_id"])

    def test_regression_or_nrt_drift_requires_rollback(self) -> None:
        regression = evaluate_experiment(self.plan, baseline=self.measurement(0.80), canary=self.measurement(0.75), nrt_drift=0.01)
        drift = evaluate_experiment(self.plan, baseline=self.measurement(0.80), canary=self.measurement(0.86), nrt_drift=0.20)
        self.assertEqual("metric_regression", regression["reason"])
        self.assertEqual("nrt_drift", drift["reason"])
        self.assertTrue(regression["rollback_required"] and drift["rollback_required"])

    def test_insufficient_samples_cannot_promote(self) -> None:
        result = evaluate_experiment(self.plan, baseline=self.measurement(0.80, 99), canary=self.measurement(0.99), nrt_drift=0.0)
        self.assertEqual("continue", result["decision"])


if __name__ == "__main__":
    unittest.main()
