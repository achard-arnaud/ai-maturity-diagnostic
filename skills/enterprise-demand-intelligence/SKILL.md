---
name: enterprise-demand-intelligence
description: Build evidence-based demand intelligence for a target company before any product recommendation. Use for account research, strategic priorities, organization and power mapping, hiring and capability signals, newsflow, AI maturity, buying context, capability gaps, build-buy-partner posture, and public evidence needed to qualify a lead. Do not load, score, or recommend Astraforge or any offer while this skill is active.
---

# Enterprise Demand Intelligence

## Responsibility

Reconstruct what the company is trying to accomplish, who owns it, what capabilities are observable, which constraints apply, and where material gaps may exist. Keep the result product-agnostic.

## Required inputs

- target entity and geography;
- decision horizon and freshness requirement;
- available public or internal sources;
- prior study artifacts when continuing a study.

Read [source-policy.md](references/source-policy.md) before external research. Read [research-lenses.md](references/research-lenses.md) before planning the four evidence passes. Read `docs/advanced_research_backends.md` before using the shared acquisition runner.

## Advanced acquisition routing

Use `scripts/advanced_research.py` only to acquire normalized public evidence for the appropriate pass. Do not treat its `relevance` field as enterprise-demand confidence or commercial priority.

- strategy: `web`, then primary corporate/IR sources;
- organization: `web`, `linkedin` public index, `youtube`, `github` where relevant;
- capability/hiring: `web`, `linkedin` public index, `github`;
- newsflow: `web`, `twitter`, `youtube`, `hackernews`, `github`, `arxiv` as relevant;
- `perplexity`: optional discovery lane only when a first-party key already exists.

Example:

```bash
python scripts/advanced_research.py "<entreprise> artificial intelligence strategy" --source web --days 365 --limit 15 --pretty
```

Every acquired result must keep its acquisition method and limitations when it enters the evidence ledger. LinkedIn indexed material cannot validate a live role or canonical identity.

## Procedure

1. Scope the entity, geography, time window, and decision to support.
2. Collect evidence across strategy, organization, capability signals, and newsflow.
3. Create atomic claims preserving source, dates, evidence grade, epistemic status, and contradictions.
4. Infer a capability gap only from two independent signals or one strong primary signal.
5. Map sponsor, terrain owner, veto players, timing signals, and constraints without treating titles as proof of power.
6. List unknowns that materially affect qualification.
7. Produce the five study artifacts, ending with `05_enterprise_demand_profile.yaml` conforming to `contracts/enterprise_demand_profile.schema.yaml`.

Use this mandatory chain:

```text
source -> fact claim -> implication -> capability gap -> validation question
```

## Output artifacts

```text
01_strategy_evidence.yaml
02_organization_evidence.yaml
03_capability_signals.yaml
04_newsflow_evidence.yaml
05_enterprise_demand_profile.yaml
```

## Boundaries

Never:

- load the product catalog;
- mention an offer as the answer to a gap;
- score product fit;
- design a pilot;
- reinterpret weak evidence to make a known product relevant;
- emit `recommended_offer`, `offer_score`, or `astraforge_fit`.

Fail the run if marketing language substitutes for operating evidence, a title proves decision power, one job posting proves mature capability, dates are conflated, gaps lack support, or product language enters the demand profile.
