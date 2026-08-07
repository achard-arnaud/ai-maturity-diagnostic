---
name: qualification-tunnel-router
description: Route private-network intake and B2B account qualification through the correct owner skill. Use when the user adds contacts, asks for ICB mapping or network prioritization, wants to create or refresh company studies, qualify a company, assess product fit, select people after a match, consolidate a sector, continue an existing study, launch the tunnel, or determine the next step. Only route and check handoff artifacts; do not perform substantive analysis.
---

# Qualification Tunnel Router

## Responsibility

Route the request to exactly one owner skill, or to a short ordered sequence when the user explicitly requests several stages. Cover both network intake and account qualification without performing substantive analysis.

## Procedure

1. Inspect the request, the study manifest, and existing artifacts when present.
2. Read [routing-table.md](references/routing-table.md) when the request crosses stages or is ambiguous.
3. Identify the current stage from the artifact gates below.
4. Select the sole owner skill for the next stage.
5. Return only the current stage, missing required artifacts, next skill, ordered sequence when needed, and stop condition.

## Core routes

- Route company reality, public signals, priorities, organization, hiring, newsflow, capability gaps, and buying context to `enterprise-demand-intelligence`.
- Route offer definition, ICP, anti-ICP, outcomes, evidence, hard gates, and product unknowns to `product-icp-intelligence`.
- Route comparison of a qualified account with versioned product profiles to `opportunity-fit-matching`.
- Route pilot, contact hypothesis, or commercial proof based on an existing match to `engagement-pilot-design`.
- Route private contact-file ingestion and entity creation to `network-contact-intake`.
- Route ICB classification to `enterprise-icb-mapping`.
- Route theoretical network prioritization to `network-account-screening`.
- Route study creation and refresh queues to `network-study-orchestration`.
- Route person selection after a fit decision to `person-opportunity-targeting`.
- Route cross-account ICB synthesis to `sector-intelligence-consolidation`.

## Artifact gates

Before matching, require:

1. `05_enterprise_demand_profile.yaml` conforming to the enterprise contract;
2. versioned product snapshots for every candidate offer.

Before engagement design, require:

1. a completed `06_product_fit_matrix.yaml`;
2. no failed blocking gate on the selected offer;
3. a named or explicitly unknown sponsor and terrain owner;
4. a measurable workflow or a discovery step that can establish one.

## Multi-stage requests

Sequence stages without merging their responsibilities:

```text
enterprise-demand-intelligence
-> product-icp-intelligence (only when a product profile is missing or stale)
-> opportunity-fit-matching
-> person-opportunity-targeting (only when private contacts exist)
-> engagement-pilot-design
```

Preserve every contract artifact. Never skip a handoff because equivalent information appears in chat context.
