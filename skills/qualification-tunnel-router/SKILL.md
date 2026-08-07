---
name: qualification-tunnel-router
description: Route private-network intake, demand/use-case/value-chain lifecycle, B2B qualification, iterative stakeholder reach and post-use-case nudging through the correct owner skill. Use when the user adds contacts, asks for ICB mapping, wants to create or refresh studies, harvest or analyze use cases, qualify a company, assess product fit, select or expand people after a match, consolidate a sector, generate nudges, resolve a workflow blocker, or determine the next governed step. Only route and check handoff artifacts; do not perform substantive analysis.
---

# Qualification Tunnel Router

## Responsibility

Route the request to exactly one owner skill, or to a short ordered sequence when several stages are explicitly requested. Cover network intake, demand/use-case/value-chain lifecycle, account-product matching, iterative person/reach qualification and post-use-case nudging without performing substantive analysis.

## Procedure

1. Inspect the request, study manifest and existing artifacts when present.
2. Read [routing-table.md](references/routing-table.md) when the request crosses stages or is ambiguous.
3. Identify the current stage from the artifact gates below.
4. If a blocker exists, route to the action that can **resolve its prerequisite**; never bypass it.
5. Select the sole owner skill for the next stage.
6. Return current stage, missing artifacts/blockers, resolver/next skill, ordered sequence when needed, expected postcondition and stop condition.

## Core routes

- Company reality, priorities, organization/hiring/newsflow, capability gaps and buying context -> `enterprise-demand-intelligence`.
- Company-level harvesting/add/update of product-blind use cases -> `enterprise-use-case-intelligence`.
- Porter-style operating/value-chain and Ishikawa causal analysis around an already canonical company UC -> `enterprise-value-chain-causal-analysis`.
- Detailed organization, decision system, influence structure or missing stakeholder-lane discovery -> `tech-leadership-org-intelligence`.
- Offer definition, ICP, anti-ICP, outcomes, evidence, hard gates and unknowns -> `product-icp-intelligence`.
- Qualified account × versioned product comparison -> `opportunity-fit-matching`.
- Initial private person selection after a valid positive fit -> `person-opportunity-targeting`.
- First/second-wave promoter/prescriber/user/technical/veto orchestration after valid fit and contact targeting -> `iterative-reach-matchmaking`.
- Pilot/discovery/proof design after fit and reach -> `engagement-pilot-design`.
- Private contact-file ingestion -> `network-contact-intake`.
- ICB classification -> `enterprise-icb-mapping`.
- Product-blind network prioritization -> `network-account-screening`.
- Study creation/refresh queue -> `network-study-orchestration`.
- Cross-account ICB synthesis/benchmark -> `sector-intelligence-consolidation`.
- Productivization, explicit dependency upsell or feedback-backed same-company packaging -> `use-case-nudging` only after a company UC inventory exists.

The derived UC graph is a **view**, not an owner skill or canonical store. It materializes typed links from owner artifacts.

## Artifact gates

### Before value-chain analysis

Require a canonical target UC in `05b_use_case_inventory.yaml`. Adjacent workflow hypotheses from `05c` can only become UCs through `enterprise-use-case-intelligence` with company evidence.

### Before matching

Require:

1. `05_enterprise_demand_profile.yaml` conforming to the enterprise contract;
2. versioned product snapshots for candidate offers.

`05b` and `05c` may enrich explainability but never substitute for demand evidence or hard gates.

### Before person targeting

Require:

1. selected `PURSUE` or `VALIDATE` match;
2. selected offer snapshot;
3. no blocker/critical `FAIL`;
4. no invalid top-level/match decision mismatch.

A role/title does not prove authority or current employment.

### Before iterative reach

Require:

1. the same valid positive fit;
2. company-linked `06b_contact_targets.yaml` or an explicit blocker routing to contact/org expansion;
3. current-role status kept explicit;
4. any blocker/critical `OPEN` carried as a validation constraint.

`iterative-reach-matchmaking` may read org/newsflow/use-case context already collected. Newsflow changes `why_now` or validation order only; it never changes fit.

### Before engagement design

Require:

1. completed valid `06_product_fit_matrix.yaml`;
2. no failed blocker/critical gate;
3. a reviewed reach/stakeholder path, or explicit discovery route establishing sponsor/terrain ownership;
4. measurable workflow or a discovery step able to establish one.

### Before nudging

Require `05b_use_case_inventory.yaml`. Nudging reads only same-company UC inventory, explicit dependencies/reusable attributes and embedded feedback/outcomes. It must not load ICB, sector rollup, demand profile, product catalog or product-fit matrix.

## Multi-stage requests

### Demand / sector lifecycle

```text
network-contact-intake
-> enterprise-icb-mapping
-> network-account-screening
-> network-study-orchestration
-> enterprise-demand-intelligence
-> enterprise-use-case-intelligence
-> enterprise-value-chain-causal-analysis (selected canonical UCs)
-> derived UC graph / heritage view
-> sector-intelligence-consolidation (only at >=3 eligible studies)
```

### Qualification / reach lifecycle

```text
enterprise-demand-intelligence
-> product-icp-intelligence (only when product truth/snapshot is missing or stale)
-> opportunity-fit-matching
-> person-opportunity-targeting
-> tech-leadership-org-intelligence (when stakeholder/current-role/decision evidence needs expansion)
-> iterative-reach-matchmaking
-> engagement-pilot-design
```

The org and reach stages may iterate: reach can expose a missing promoter/prescriber/terrain/veto lane, route back to org/role validation, then rebuild `06c` without recomputing product fit.

### Nudging lifecycle

```text
enterprise-use-case-intelligence
-> same-company derived UC graph
-> use-case-nudging
-> human review / falsifier
-> enterprise-use-case-intelligence (feedback refresh when observed evidence exists)
```

## Blocker rule

A blocker is not a terminal UI state. Return or expose:

- why it blocks;
- required state/evidence;
- owner skill or explicit human action;
- resolver CTA/input;
- expected postcondition.

The resolver must advance toward the missing prerequisite, not modify a score/status to make the blocker disappear.

Preserve every contract artifact. Never skip a handoff because equivalent information appears in chat context.
