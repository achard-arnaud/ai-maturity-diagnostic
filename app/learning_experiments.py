"""Epic 13 S04: bounded baseline/canary experiments and NRT drift gates."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping


class ExperimentError(ValueError):
    pass


@dataclass(frozen=True)
class ExperimentPlan:
    experiment_id: str
    proposal_id: str
    primary_metric_id: str
    direction: str
    minimum_sample_size: int
    maximum_regression: float
    drift_threshold: float
    baseline_ref: str
    canary_ref: str

    def __post_init__(self) -> None:
        if self.direction not in {"increase", "decrease"}:
            raise ExperimentError("direction must be increase or decrease")
        if self.minimum_sample_size <= 0 or self.maximum_regression < 0 or self.drift_threshold < 0:
            raise ExperimentError("experiment thresholds must be non-negative and sample size positive")
        if not all((self.experiment_id, self.proposal_id, self.primary_metric_id, self.baseline_ref, self.canary_ref)):
            raise ExperimentError("experiment identifiers and refs are required")


def evaluate_experiment(plan: ExperimentPlan, *, baseline: Mapping[str, Any], canary: Mapping[str, Any], nrt_drift: float) -> dict[str, Any]:
    for label, measurement in (("baseline", baseline), ("canary", canary)):
        if measurement.get("metric_id") != plan.primary_metric_id:
            raise ExperimentError(f"{label} metric does not match plan")
        if int(measurement.get("sample_size", 0)) < plan.minimum_sample_size:
            return {"schema_version": "1.0", "experiment": asdict(plan), "decision": "continue", "reason": f"{label}_sample_too_small", "rollback_required": False, "nrt_drift": nrt_drift}

    baseline_value = float(baseline["value"])
    canary_value = float(canary["value"])
    improvement = canary_value - baseline_value if plan.direction == "increase" else baseline_value - canary_value
    drift_failed = nrt_drift > plan.drift_threshold
    regression_failed = improvement < -plan.maximum_regression
    if drift_failed or regression_failed:
        decision = "rollback"
        reason = "nrt_drift" if drift_failed else "metric_regression"
    else:
        decision = "promote" if improvement > 0 else "continue"
        reason = "measured_improvement" if improvement > 0 else "no_measured_improvement"
    return {
        "schema_version": "1.0",
        "experiment": asdict(plan),
        "baseline": dict(baseline),
        "canary": dict(canary),
        "improvement": improvement,
        "nrt_drift": nrt_drift,
        "decision": decision,
        "reason": reason,
        "rollback_required": decision == "rollback",
    }
