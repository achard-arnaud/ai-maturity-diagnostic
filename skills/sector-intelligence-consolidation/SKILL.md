---
name: sector-intelligence-consolidation
description: Consolidate evidence from multiple current company studies in one ICB sector into recurring strategic priorities, capability gaps, maturity patterns, training themes, use cases by line of business, contradictions, and unknowns. Use only when at least three sufficiently complete account studies share a defensible ICB sector. Do not generalize from contact counts, stale studies, mixed sectors, or repeated unsupported hypotheses.
---

# Sector Intelligence Consolidation

## Responsibility

Create a traceable sector view from account evidence without turning repetition into truth.

Read [consolidation-policy.md](references/consolidation-policy.md) before synthesis.

## Procedure

1. Run `python scripts/build_sector_rollups.py` to test eligibility.
2. Require at least three current, complete studies in the same candidate or validated ICB sector.
3. Mark candidate/mixed classification as `exploratory`; require all mappings `validated` for `decision_grade`.
4. Load the generated evidence pool and every referenced account claim.
5. Separate recurring facts, recurring inferences, contradictions, and corpus bias.
6. Synthesize priorities, gaps, maturity, training, and use cases by line of business.
7. Preserve company and claim IDs plus ICB mapping status in every sector conclusion.
8. Record missing account types and triggers for refresh.

Write `data/private/sector_rollups/ICB-<sector>.yaml`. Do not publish person-level data in a sector rollup.
