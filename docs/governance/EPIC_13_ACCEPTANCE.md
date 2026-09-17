# Epic 13 acceptance — Insights, Cost and Governed Learning

## Result

Insights now projects funnel, quality and execution cost from an explicit,
replayable event cohort. Source, sector and product dimensions are declared;
small cohorts are suppressed and no raw event is returned by the analytics API.

LearningProposal distinguishes retrospective, red-team and dreaming inputs.
Review decisions are audited, acceptance only authorizes a bounded experiment,
and a measured proposal links its baseline/canary experiment and result. NRT
drift or metric regression requires rollback.

## Sprint evidence

- S01: metric catalog and cohort policy.
- S02: reproducible event projections and reconciliation.
- S03: audited proposal lifecycle with no auto-mutation.
- S04: baseline/canary evaluation and drift rollback.
- S05: workspace-safe Insights API and actionable, privacy-aware UI.

## Rollback and compatibility

Delete or disable the Insights route/UI to remove the projection. Rebuilding it
from the unchanged event journal restores the same output. Business artifacts
and source events are not migrated or rewritten.
