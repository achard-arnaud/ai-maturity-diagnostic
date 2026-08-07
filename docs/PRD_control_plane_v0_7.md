# PRD — Control Plane v0.7

## 1. Objective

Turn the v0.6 local control plane into an iterative decision/navigation system connecting company demand, use cases, operating context, product fit and stakeholder reach without weakening the existing truth boundaries.

The user must be able to answer, from persisted evidence:

1. Where does a use case sit in the operating/value chain and what causes constrain it?
2. Which adjacent workflows should be investigated next, without inventing demand?
3. Which company, matched offer and ICP persona are in play?
4. Which people should be validated/contacted first vs second, and why now?
5. What exact blocker prevents the next step and which CTA resolves it?
6. Which use-case patterns/assets are reusable within a company or sector without copying demand across companies?

## 2. Non-negotiable invariants

- Enterprise research and company use-case truth remain product-blind until matching.
- ICB is classification/navigation context, not proof of need.
- Hard gates precede scoring and outreach.
- Person targeting starts only after valid positive fit; title alone never proves authority.
- Newsflow changes timing/angle and validation priority, never product fit.
- Sector and cross-company UC relations are hypotheses unless supported by company evidence.
- Product truth remains canonical only in `product_catalog/` and immutable study snapshots.
- No outbound message is sent by this release.
- Local/non-production security posture remains unchanged.

## 3. New artifacts

### 3.1 `05c_value_chain_causal_map.yaml`
One study-level document containing per-UC analyses:

- `use_case_id` and source evidence IDs;
- Porter decomposition:
  - upstream activities;
  - focal activity;
  - downstream activities;
  - support activities;
  - handoffs;
  - control points;
  - value effects: revenue/value, cost, quality, time, risk;
- Ishikawa causes:
  - people;
  - process;
  - technology;
  - data;
  - governance/control;
  - environment/external;
- adjacent workflow hypotheses;
- validation questions;
- unknowns/confidence.

It is product-blind and cannot create a canonical company UC by itself.

### 3.2 Derived UC graph
No new canonical store. The graph endpoint materializes nodes/edges from:

- `05b_use_case_inventory.yaml`;
- `05c_value_chain_causal_map.yaml`;
- optional sector rollup evidence pools.

Typed edges:

- `depends_on` / `enables` — explicit dependency;
- `variant_of` — explicit variant relation;
- `shares_asset` — deterministic same-company reusable-asset overlap;
- `same_outcome` — deterministic same-company outcome-family overlap;
- `value_chain_neighbor` — explicit adjacency in 05c;
- `causal_neighbor` — explicit shared causal constraint in 05c;
- `similar_pattern` — cross-company/sector hypothesis only, never demand proof.

Every edge carries `scope`, `basis`, `confidence`, and `evidence_refs`.

### 3.3 `06c_reach_strategy.yaml`
Downstream of a valid positive fit and contact targeting. It bridges existing artifacts without recomputing them:

- company/study/ICB context;
- selected offer/profile version and fit decision;
- ICP personas;
- validated/uncertain people;
- org/decision evidence references;
- newsflow trigger references;
- relevant company UC/value-chain context;
- stakeholder role hypotheses:
  - promoter/economic sponsor;
  - prescriber/influencer;
  - terrain owner/user;
  - technical sponsor;
  - veto/control;
- outreach wave: `first`, `second`, `validation_only`;
- why this person / why now;
- required validations;
- CTA/postcondition.

The artifact never sends outreach and never upgrades role authority from title alone.

## 4. User journeys

### 4.1 Company / UC deep dive

`Demand > sector > company > use case`

Available CTAs:

- Add / update use flow;
- **Analyse chaîne de valeur**;
- Explore UC graph;
- Open organization;
- Open qualification;
- Open nudging;
- Full company journey.

`Analyse chaîne de valeur` prepares `enterprise-value-chain-causal-analysis` with the company inventory and study evidence paths.

### 4.2 Iterative reach matchmaking

After positive fit:

`Demand profile -> product snapshot -> valid matching -> people -> org/newsflow enrichment -> reach strategy -> pilot`

The reach cockpit displays first/second-wave people by role hypothesis and explicit missing validations. If first-wave evidence is weak, the user can expand the second round rather than forcing a single contact.

### 4.3 Blocker resolution

Every workflow step uses a normalized blocker model:

- `blocker_id`;
- `category`;
- `message`;
- `required_state`;
- `owner_skill` or `human_action`;
- `cta_label`;
- `cta_input`;
- `context_paths`;
- `postcondition`;
- `prepare_only_safe`.

Blocked buttons never disappear. They become resolver CTAs.

## 5. Cross-menu information architecture

Primary menus remain:

- **Demande** — ICB/company/studies/use cases/value chain/UC heritage;
- **Offres** — canonical offer lifecycle + opportunities using current snapshots;
- **Qualification** — artifact gates, matching, contacts, reach, pilot;
- **Nudging** — UC-only expansion hypotheses;
- **Suivi** — unresolved blockers and actionable next steps;
- **Skills** — technical/manual unit invocation.

Cross-links are contextual handoffs only. No frontend business truth is duplicated.

## 6. Dashboards

### Demand dashboard

- sector readiness;
- company study state;
- UC count;
- value-chain analyses count;
- unresolved UC evidence/graph questions;
- benchmark readiness.

### Use-case heritage

Two views:

- by company: canonical UC cards + typed internal graph edges;
- by ICB sector: observed UC patterns, companies represented, evidence scope and similarity hypotheses.

### Follow-up dashboard

Priority ordering:

1. hard/blocking qualification actions;
2. current-role validation / reach blockers;
3. demand/study/use-case completeness;
4. sector benchmark readiness;
5. nudging review/feedback;
6. release/productization TODO.

## 7. Zettelkasten decision

Use only the useful mechanics: atomic notes, stable IDs, typed links and backlinks. Do **not** add a separate Zettelkasten UI/database, free-form note corpus, embedding service, graph database or vector store in v0.7.

Revisit only if real usage shows one of these measurable problems:

- cross-inventory navigation latency;
- repeated inability to find related UCs;
- graph size makes materialization too slow;
- manual link maintenance becomes the dominant operating cost.

## 8. Coverage and QA

CI must run release validation and an explicit coverage gate.

Coverage target: **>=80% line coverage** for the Python control-plane and deterministic domain modules exercised by the test suite. The report must include `app/` and the deterministic scripts/modules used by the local workflows; external acquisition adapters and document renderers may be omitted only when documented because they require third-party/network/visual integration tests.

Tests must include:

- Porter/Ishikawa boundary and no product leakage;
- UC graph edge provenance and no cross-company demand promotion;
- reach first/second-wave logic and title-authority guardrail;
- blocker resolver contract;
- menu/handoff contract;
- coverage gate.

## 9. Definition of done

- RFC #14 feedback gates recorded.
- PRD/ADR/user-flow/TODO updated.
- New skills, contracts, backend endpoints and frontend journeys implemented.
- Every governed blocker displayed by the control plane has a resolver CTA or explicit human resolution action.
- No regression of v0.5/v0.6 invariants.
- QA and coverage >=80% green.
- Remaining post-holiday actions explicitly separated from completed engineering.