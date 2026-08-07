---
name: enterprise-use-case-intelligence
description: Build or refresh a product-blind inventory of AI and automation use cases for one company study, including workflow, evidence status, maturity, explicit dependencies, repeatability, reusable assets, feedback and unknowns. Use when the user wants to harvest, consolidate, add, update or validate use flows/use cases beneath an enterprise study, including validation of adjacent workflow hypotheses discovered by value-chain analysis. Do not load product profiles, score offer fit, infer sector demand, or create nudges.
---

# Enterprise Use-Case Intelligence

## Responsibility

Create the canonical operational use-case layer beneath an enterprise study while preserving evidence provenance and uncertainty. This skill is the only owner allowed to add a candidate adjacent workflow into the company UC inventory after evidence validation.

## Required inputs

- one managed company study;
- its evidence artifacts and claim IDs;
- optional prior `05b_use_case_inventory.yaml` when refreshing;
- optional `05c_value_chain_causal_map.yaml` when validating adjacent-workflow hypotheses.

## Procedure

1. Read the study manifest and product-blind evidence artifacts only.
2. Identify workflows/use cases that are directly observed or defensibly inferred from company evidence.
3. Create stable `UC-...` IDs and preserve prior IDs when refreshing.
4. Record line of business, workflow, job-to-be-done, problem/outcome, evidence status and maturity.
5. Add dependency/enabler edges only when the relation is explicit or separately evidenced.
6. Record repeatability, variant axes and reusable assets without assuming productization is desirable.
7. Attach company feedback/outcomes only with claim provenance.
8. When `05c` proposes an adjacent workflow, validate it against company evidence. Either promote it with a stable UC ID and evidence refs, keep it hypothetical, or reject it explicitly.
9. Preserve unknowns and confidence.
10. Write `05b_use_case_inventory.yaml` conforming to `contracts/use_case_inventory.schema.yaml`.

## Handoffs

- Known UC needing surrounding workflow/root-cause analysis -> `enterprise-value-chain-causal-analysis`.
- Related-UC exploration -> derived UC graph generated from `05b` + `05c`; the graph is not a canonical store.
- Same-company post-UC commercial hypotheses -> `use-case-nudging` after the inventory is established.
- Sector comparison -> `sector-intelligence-consolidation`; sector patterns never write back automatically into this inventory.

## Graph link discipline

The derived graph may expose:

- `depends_on` / `enables` from explicit dependencies;
- `variant_of` from an explicit same-company relation;
- `shares_asset` and `same_outcome` from deterministic same-company overlap;
- `value_chain_neighbor` / `causal_neighbor` from `05c`;
- `similar_pattern` across companies only as a low-confidence comparative hypothesis.

Never add a graph edge as company demand evidence merely because another company or sector contains a similar UC.

## Boundaries

Never:
- load `product_catalog/` or product snapshots;
- recommend an offer;
- treat ICB membership as evidence that a use case exists;
- copy a use case from another company into this company inventory without company evidence;
- silently canonicalize an adjacent workflow from Porter/Ishikawa analysis;
- create upsell/cross-sell conclusions.

The inventory is demand-side truth. Value-chain analysis and graph views are downstream analytical layers; nudging is a downstream consumer with stricter input boundaries.
