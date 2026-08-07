---
name: use-case-nudging
description: Generate reviewable productivization, dependency-upsell, or cross-sell-package hypotheses from one company's existing use-case inventory and recorded feedback only. Use after use cases have been inventoried. Do not read ICB, sector rollups, enterprise demand profiles, product catalog, product fit, or infer initial account qualification.
---

# Use-Case Nudging

## Responsibility

Create expansion hypotheses from the use-case graph without re-running or bypassing qualification.

## Allowed inputs

- `05b_use_case_inventory.yaml` for one company;
- recorded feedback/outcomes embedded in that inventory.

## Forbidden inputs

Do not load:
- ICB taxonomy or company ICB mappings;
- sector rollups or sector benchmark conclusions;
- `05_enterprise_demand_profile.yaml`;
- product catalog or product snapshots;
- `06_product_fit_matrix.yaml`.

## Modes

### Productivization
Start from an existing use case. Suggest standardization, serialization, enrichment, cheaper variants, reusable assets or controlled scaling. Do not invent a new use case.

### Dependency upsell
A target use case is eligible only if an explicit `depends_on` or `enables` edge connects it to a use case already in the inventory. No graph edge means no upsell claim.

### Cross-sell package
Bundle two or more use cases already catalogued for the company. Build the story from that company’s recorded feedback/outcomes. Do not use sector similarity as the rationale.

## Procedure

1. Validate the inventory contract and version.
2. Select exactly one mode or explicitly request all three.
3. Generate candidates using only allowed fields.
4. Cite source and target use-case IDs plus feedback evidence.
5. State prerequisites, unknowns and one falsifier for every candidate.
6. Keep status `hypothesis` until human review.
7. Output `09_use_case_nudges.yaml` conforming to `contracts/nudge_recommendation.schema.yaml` when persisted.

## Boundaries

A nudge is not a product-fit decision and must never emit `PURSUE`, `VALIDATE`, product score, ICB rationale, or offer recommendation.
