"""Epic 13 S01: explicit metric semantics and cohort policies.

Metrics are definitions for rebuildable event projections.  They never become
authoritative business records and every result must name its cohort window.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping


class MetricPolicyError(ValueError):
    pass


@dataclass(frozen=True)
class MetricDefinition:
    metric_id: str
    label: str
    unit: str
    event_types: tuple[str, ...]
    aggregation: str
    value_field: str | None = None
    description: str = ""


@dataclass(frozen=True)
class CohortPolicy:
    cohort_id: str
    workspace_id: str
    start_at: str
    end_at: str
    dimensions: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        start = parse_instant(self.start_at)
        end = parse_instant(self.end_at)
        if end <= start:
            raise MetricPolicyError("cohort end_at must be after start_at")
        if not self.cohort_id.strip() or not self.workspace_id.strip():
            raise MetricPolicyError("cohort_id and workspace_id are required")

    def matches(self, event: Mapping[str, Any]) -> bool:
        if event.get("workspace_id") != self.workspace_id:
            return False
        occurred = parse_instant(str(event.get("occurred_at", "")))
        if not (parse_instant(self.start_at) <= occurred < parse_instant(self.end_at)):
            return False
        data = event.get("data") or {}
        return all(str(data.get(key)) == value for key, value in self.dimensions)


METRIC_CATALOG: tuple[MetricDefinition, ...] = (
    MetricDefinition("journey_started", "Parcours démarrés", "count", ("journey.started",), "count"),
    MetricDefinition("journey_completed", "Parcours terminés", "count", ("journey.completed",), "count"),
    MetricDefinition("quality_pass_rate", "Taux qualité", "ratio", ("quality.checked",), "boolean_rate", "passed"),
    MetricDefinition("execution_cost", "Coût d'exécution", "cost_units", ("execution.completed",), "sum", "cost_units"),
)


def parse_instant(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise MetricPolicyError(f"invalid ISO instant: {value}") from exc
    if parsed.tzinfo is None:
        raise MetricPolicyError("metric instants must include a timezone")
    return parsed.astimezone(timezone.utc)


def metric_catalog() -> list[dict[str, Any]]:
    return [asdict(definition) for definition in METRIC_CATALOG]


def select_cohort(events: Iterable[Mapping[str, Any]], policy: CohortPolicy) -> list[Mapping[str, Any]]:
    return sorted((event for event in events if policy.matches(event)), key=lambda item: (item["occurred_at"], item.get("event_id", "")))
