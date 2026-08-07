# ADR-006 — Derived UC graph, evidence-bounded reach and blocker resolver CTAs

## Status
Accepted for v0.7 local control plane.

## Context
v0.6 exposes Demand, Offers, Qualification and Nudging but leaves three structural gaps: use cases are not decomposed into surrounding operational/value chains; downstream person targeting is not presented as an iterative stakeholder/reach strategy; blockers can be visible without a normalized resolving action. A full graph/CRM platform would add persistence, duplicate truths and operating cost before real usage proves the need.

## Decision

### 1. Value-chain analysis is a distinct demand-side artifact
`05c_value_chain_causal_map.yaml` is owned by `enterprise-value-chain-causal-analysis`. It reads only company study evidence plus `05b_use_case_inventory.yaml`. Porter and Ishikawa are analytical lenses, not sources. Adjacent workflows remain hypotheses until company evidence promotes them through `enterprise-use-case-intelligence`.

### 2. UC graph is derived, not canonical
`app.uc_graph` materializes a graph on demand from existing inventories and value-chain artifacts. It never persists an independent truth store. Edges are typed and evidence-scoped. Cross-company links are always hypotheses.

### 3. Reach is downstream of valid fit
`iterative-reach-matchmaking` and `app.reach` may bridge account, product snapshot, contact targets, org evidence, newsflow and UC context only after a selected `PURSUE`/`VALIDATE` match passes blocker/critical gates. It never recomputes product fit or sends outbound communication.

Stakeholder roles are hypotheses: promoter/sponsor, prescriber/influencer, terrain owner/user, technical sponsor, veto/control. Current-role evidence and influence/mandate evidence remain separate.

### 4. Blockers become first-class navigation objects
`app.blockers` normalizes blockers into resolver actions. Every blocked workflow step carries an owner skill or explicit human action, a CTA, required state and expected postcondition. A resolver routes backward to prerequisites; it never overrides them.

### 5. Zettelkasten principles, not Zettelkasten infrastructure
Adopt stable atomic UC IDs, typed links and backlinks. Reject a separate note database, graph DB, vector store or embedding layer in v0.7. This is the value-for-money decision until usage metrics demonstrate a retrieval/scaling problem.

## Consequences

### Positive
- Better cross-menu navigation without duplicating business truth.
- UC reuse and dependency discovery becomes explainable.
- Outreach progression can expand to a second stakeholder wave instead of forcing one guessed sponsor.
- Blocked workflows become actionable.
- Minimal infrastructure/maintenance cost.

### Costs
- Graph materialization is recomputed from files.
- Similarity beyond deterministic typed relations remains limited.
- Human/evidence review remains required for cross-company patterns and stakeholder authority.

## Rejected alternatives

### Persist a graph database now
Rejected: no demonstrated scale/performance need; creates synchronization and security burden.

### Let sector patterns populate company use cases automatically
Rejected: violates the demand-proof boundary.

### Let org titles determine outreach role
Rejected: titles are role signals, not authority evidence.

### Fold Porter/Ishikawa into the UC inventory itself
Rejected: would mix observed use-case truth with analytical hypotheses and make refresh/versioning harder.

## Feedback gates
Before release, review:
1. boundary integrity;
2. architecture value-for-money;
3. UX CTA usefulness;
4. false-positive graph/reach hypotheses;
5. coverage/release QA.