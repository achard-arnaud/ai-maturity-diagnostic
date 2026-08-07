---
name: enterprise-use-case-intelligence
description: Build or refresh a product-blind inventory of AI and automation use cases for one company study, including workflow, evidence status, maturity, explicit dependencies, repeatability, reusable assets, feedback and unknowns. Use when the user wants to harvest, consolidate, add or update use flows/use cases beneath an enterprise study. Do not load product profiles, score offer fit, infer sector demand, or create nudges.
---

# Enterprise Use-Case Intelligence

## Responsibility

Create the operational use-case layer beneath an enterprise study while preserving evidence provenance and uncertainty.

## Required inputs

- one managed company study;
- its evidence artifacts and claim IDs;
- optional prior `05b_use_case_inventory.yaml` when refreshing.

## Procedure

1. Read the study manifest and product-blind evidence artifacts only.
2. Identify workflows/use cases that are directly observed or defensibly inferred from evidence.
3. Create stable `UC-...` IDs and preserve prior IDs when refreshing.
4. Record line of business, workflow, job-to-be-done, problem/outcome, evidence status and maturity.
5. Add dependency/enabler edges only when the relation is explicit or separately evidenced.
6. Record repeatability, variant axes and reusable assets without assuming productization is desirable.
7. Attach company feedback/outcomes only with claim provenance.
8. Preserve unknowns and confidence.
9. Write `05b_use_case_inventory.yaml` conforming to `contracts/use_case_inventory.schema.yaml`.

## Boundaries

Never:
- load `product_catalog/` or product snapshots;
- recommend an offer;
- treat ICB membership as evidence that a use case exists;
- copy a use case from another company into this company inventory without company evidence;
- create upsell/cross-sell conclusions.

The inventory is demand-side truth. Nudging is a downstream consumer with stricter input boundaries.
