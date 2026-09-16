"""Epic 11 S04: proof design and outcome discipline."""

from __future__ import annotations


class ProofPolicyError(ValueError):
    pass


def design_proof(*, proof_id: str, opportunity_id: str, success_metrics: list[dict], falsifier: str) -> dict:
    """Create the immutable design inputs required before a proof can run."""
    if not success_metrics:
        raise ProofPolicyError("a proof requires at least one success metric")
    if not falsifier.strip():
        raise ProofPolicyError("a proof requires a falsifier before it can run")
    for metric in success_metrics:
        if not metric.get("metric_id") or "target" not in metric or not metric.get("unit"):
            raise ProofPolicyError("every success metric requires id, target and unit")
    return {"proof_id": proof_id, "opportunity_id": opportunity_id, "success_metrics": [dict(metric) for metric in success_metrics], "falsifier": falsifier}


def record_proof_outcome(design: dict, *, actuals: dict[str, float], evidence_refs: list[str], recorded_at: str) -> dict:
    """Evaluate a designed proof; a missing observation is inconclusive, never met."""
    metrics = []
    for metric in design["success_metrics"]:
        metric_id = metric["metric_id"]
        if metric_id not in actuals:
            status = "inconclusive"
            metrics.append({**metric, "actual": 0.0})
            continue
        metrics.append({**metric, "actual": actuals[metric_id]})
    if len(actuals) != len(metrics):
        status = "inconclusive"
    elif all(metric["actual"] >= metric["target"] for metric in metrics):
        status = "met"
    else:
        status = "not_met"
    return {"proof_id": design["proof_id"], "success_metrics": metrics, "falsifier": design["falsifier"], "status": status, "evidence_refs": list(evidence_refs), "recorded_at": recorded_at}


def can_support_client_claim(outcome: dict) -> bool:
    """Only evidence-backed outcomes that met their predeclared metrics qualify."""
    return outcome["status"] == "met" and bool(outcome["evidence_refs"])
