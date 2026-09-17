# Epic 13 S01 stop condition

The metric catalog fixes each metric's event source, unit, aggregation and
value field. Cohorts require an explicit workspace, timezone-aware half-open
window and declared dimensions. Deterministic fixtures prove that events
outside any boundary cannot leak into a result.

Metric output is a rebuildable projection, never a canonical business fact.
