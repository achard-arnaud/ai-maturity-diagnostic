---
name: qualification-tunnel-router
description: Route private-network intake, demand/use-case catalog lifecycle, B2B account qualification and post-use-case nudging through the correct owner skill. Use when the user adds contacts, asks for ICB mapping or network prioritization, wants to create or refresh company studies, harvest use cases, consolidate a sector, qualify a company, assess product fit, select people after a match, continue an existing study, launch the tunnel, generate use-case nudges, or determine the next step. Only route and check handoff artifacts; do not perform substantive analysis.
---

# Qualification Tunnel Router

## Responsibility

Route the request to exactly one owner skill, or to a short ordered sequence when the user explicitly requests several stages. Cover network intake, demand catalog lifecycle, account qualification and post-use-case nudging without performing substantive analysis.

## Procedure

1. Inspect the request, study manifest and existing artifacts when present.
2. Read [routing-table.md](references/routing-table.md) when the request crosses stages or is ambiguous.
3. Identify the current stage from the artifact gates below.
4. Select the sole owner skill for the next stage.
5. Return only the current stage, missing required artifacts, next skill, ordered sequence when needed, and stop condition.

## Core routes

- Route company reality, public signals, priorities, organization, hiring, newsflow, capability gaps, buying context and initial demand qualification to `enterprise-demand-intelligence`.
- Route company-level harvesting, adding or updating of product-blind AI/use-flow records to `enterprise-use-case-intelligence`.
- Route offer definition, ICP, anti-ICP, outcomes, evidence, hard gates and product unknowns to `product-icp-intelligence`.
- Route comparison of a qualified account with versioned product profiles to `opportunity-fit-matching`.
- Route pilot, contact hypothesis or commercial proof based on an existing match to `engagement-pilot-design`.
- Route private contact-file ingestion and entity creation to `network-contact-intake`.
- Route ICB classification to `enterprise-icb-mapping`.
- Route theoretical network prioritization to `network-account-screening`.
- Route study creation and refresh queues to `network-study-orchestration`.
- Route person selection after a fit decision to `person-opportunity-targeting`.
- Route cross-account ICB synthesis and sector benchmarking to `sector-intelligence-consolidation`.
- Route productivization, explicit dependency-upsell or company use-case packaging to `use-case-nudging` **only after** a use-case inventory exists.

## Artifact gates

Before matching, require:

1. `05_enterprise_demand_profile.yaml` conforming to the enterprise contract;
2. versioned product snapshots for every candidate offer.

`05b_use_case_inventory.yaml` is optional for initial matching and must never substitute for the demand profile or hard gates.

Before engagement design, require:

1. a completed `06_product_fit_matrix.yaml`;
2. no failed blocking gate on the selected offer;
3. a named or explicitly unknown sponsor and terrain owner;
4. a measurable workflow or a discovery step that can establish one.

Before nudging, require:

1. `05b_use_case_inventory.yaml` conforming to the use-case contract;
2. the nudge runtime to load **only that inventory and its embedded feedback/outcomes**.

Nudging must not load ICB mappings, sector rollups, the enterprise demand profile, product catalog or product-fit matrix.

## Multi-stage requests

### Demand / sector lifecycle

```text
network-contact-intake
-> enterprise-icb-mapping
-> network-account-screening
-> network-study-orchestration
-> enterprise-demand-intelligence
-> enterprise-use-case-intelligence
-> sector-intelligence-consolidation (only at >=3 eligible studies)
```

### Qualification lifecycle

```text
enterprise-demand-intelligence
-> product-icp-intelligence (only when a product profile is missing or stale)
-> opportunity-fit-matching
-> person-opportunity-targeting (only when private contacts exist)
-> engagement-pilot-design
```

### Nudging lifecycle

```text
enterprise-use-case-intelligence
-> use-case-nudging
-> human review / falsifier
-> enterprise-use-case-intelligence (feedback refresh when new evidence exists)
```

Preserve every contract artifact. Never skip a handoff because equivalent information appears in chat context.
