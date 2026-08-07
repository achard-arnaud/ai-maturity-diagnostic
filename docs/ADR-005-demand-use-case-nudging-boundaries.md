# ADR-005 — Demand catalog, use-case graph and nudging boundaries

- Status: accepted for v0.6 implementation
- Date: 2026-08-07

## Context

The repository already has ICB mapping, company studies, sector consolidation and product matching, but these are mostly file/script-oriented. A user-facing demand catalog needs a stable operational unit beneath the company: the use case.

Introducing a use-case graph also creates a risk: reusing it for initial qualification could silently bypass the evidence and hard-gate architecture.

## Decision

### Demand catalog
ICB is a navigation and aggregation taxonomy. Sector maturity is based on the existing study eligibility rules, not on contact counts or company names.

### Use-case truth
Company use cases live in a dedicated study artifact (`05b_use_case_inventory.yaml`). They are derived from company evidence and remain product-blind.

### Matching
Initial account/product qualification continues to use `05_enterprise_demand_profile.yaml` + immutable product snapshots through `opportunity-fit-matching`. Use-case inventory may support validation questions or pilot detail later, but cannot replace the demand profile or hard gates.

### Nudging
Nudging is a separate post/use-case expansion system. Its implementation must not import or load:
- ICB taxonomy or mappings;
- sector rollups;
- enterprise demand profiles;
- product catalog or product-fit matrix.

It may load only use-case inventory and recorded use-case feedback/outcomes.

## Consequences

- Sector discovery and nudge generation cannot contaminate each other.
- A sector similarity is never sufficient to recommend a use case.
- An upsell requires an explicit dependency/enabler edge.
- Cross-sell is packaging of already catalogued use cases, not inferred account fit.
- Productivization improves an existing use case instead of inventing new demand.
