"""Epic 13 S02: deterministic funnel, quality and cost projections."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Iterable, Mapping

from app.insights_metrics import CohortPolicy, METRIC_CATALOG, select_cohort


@dataclass(frozen=True)
class MetricValue:
    metric_id: str
    value: float
    unit: str
    numerator: float | None = None
    denominator: float | None = None


def _digest(events: list[Mapping[str, Any]]) -> str:
    payload = [{key: event.get(key) for key in ("event_id", "event_hash", "occurred_at")} for event in events]
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def build_projection(events: Iterable[Mapping[str, Any]], policy: CohortPolicy) -> dict[str, Any]:
    selected = select_cohort(events, policy)
    values: list[MetricValue] = []
    for definition in METRIC_CATALOG:
        relevant = [event for event in selected if event.get("event_type") in definition.event_types]
        if definition.aggregation == "count":
            metric = MetricValue(definition.metric_id, float(len(relevant)), definition.unit)
        elif definition.aggregation == "sum":
            total = sum(float((event.get("data") or {}).get(definition.value_field or "", 0)) for event in relevant)
            metric = MetricValue(definition.metric_id, total, definition.unit)
        else:
            passed = sum(1 for event in relevant if (event.get("data") or {}).get(definition.value_field or "") is True)
            total = len(relevant)
            metric = MetricValue(definition.metric_id, passed / total if total else 0.0, definition.unit, float(passed), float(total))
        values.append(metric)

    by_id = {item.metric_id: item for item in values}
    started = by_id["journey_started"].value
    completed = by_id["journey_completed"].value
    values.append(MetricValue("funnel_completion_rate", completed / started if started else 0.0, "ratio", completed, started))
    return {
        "schema_version": "1.0",
        "projection_kind": "event_projection",
        "authoritative": False,
        "cohort": asdict(policy),
        "source_event_count": len(selected),
        "source_digest": _digest(selected),
        "metrics": [asdict(item) for item in values],
    }


def reconcile_projection(projection: Mapping[str, Any], events: Iterable[Mapping[str, Any]], policy: CohortPolicy) -> bool:
    rebuilt = build_projection(events, policy)
    return projection == rebuilt
