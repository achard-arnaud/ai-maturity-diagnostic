---
name: sector-intelligence-consolidation
description: Consolidate evidence from multiple current company studies in one ICB sector into recurring strategic priorities, capability gaps, maturity patterns, training themes, use cases by line of business, contradictions, dependencies and unknowns. Use only when at least three sufficiently complete account studies share a defensible ICB sector. Do not generalize from contact counts, stale studies, mixed sectors, repeated unsupported hypotheses, or use the sector rollup as a nudging input.
---

# Sector Intelligence Consolidation

## Responsibility

Create a traceable sector view from account evidence without turning repetition into truth.

Read [consolidation-policy.md](references/consolidation-policy.md) before synthesis.

## Procedure

1. Run `python scripts/build_sector_rollups.py` to test eligibility and scaffold the evidence pool.
2. Require at least three current, complete studies in the same candidate or validated ICB sector.
3. Mark candidate/mixed classification as `exploratory`; require all mappings `validated` for `decision_grade`.
4. Load the generated evidence pool and every referenced account claim.
5. When `05b_use_case_inventory.yaml` exists, preserve company/study/use-case IDs, evidence status, maturity, dependency edges, feedback and inventory version in the sector evidence pool.
6. Separate recurring facts, recurring inferences, recurring use-case patterns, contradictions and corpus bias.
7. Synthesize priorities, gaps, maturity, training and use cases by line of business without copying one company use case into another company’s demand truth.
8. Preserve company and claim/use-case IDs plus ICB mapping status in every sector conclusion.
9. Record missing account types, missing use-case evidence and triggers for refresh.

Write `data/private/sector_rollups/ICB-<sector>.yaml`. Do not publish person-level data in a sector rollup.

## Boundary with nudging

Sector consolidation is useful for research, benchmarking and initial qualification context. It is **not** an allowed input to `use-case-nudging`. Nudging must remain based on one company’s own use-case inventory and embedded feedback only.
