# Epic 12 Acceptance — GTM Experience Replatform

## Result

The job-based shell now exposes Home, Discover, Research, Fit, Targets, Reach,
Engagement, Pipeline and Insights on workspace-explicit deep links. Browser
back/refresh is route-owned, APIs remain workspace-scoped, gates remain visible
and analytics are not treated as business truth.

## Sprint evidence

- S01: ADR-010 and measured stack decision.
- S02: workspace-safe router and shell.
- S03: upstream spaces.
- S04: decision/execution spaces and visible gates.
- S05: Engagement/Pipeline/Insights boundary.
- S06: telemetry, accessibility, mobile and rollback.

## Compatibility

Legacy panels remain for one release behind `?legacy=1`; they are absent from
primary navigation. No data migration or rollback is required.
