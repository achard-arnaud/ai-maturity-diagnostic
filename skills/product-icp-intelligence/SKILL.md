---
name: product-icp-intelligence
description: 'Define, audit, or update the canonical ICP and product truth for one offer independently of any target account. Use when formalizing Astraforge or another offer: problem and anti-problem, outcomes, ICP and anti-ICP, personas, capabilities, prerequisites, hard gates, use-case families, proof, alternatives, pricing status, pilot pattern, unknowns, and product evidence. Do not research a named company or decide whether a specific account is a fit.'
---

# Product ICP Intelligence

## Responsibility

Create a versioned, falsifiable description of one product or service offer. State the observable customer conditions under which the offer may create value, required prerequisites, and supporting evidence.

## Required inputs

- raw product evidence;
- owner or product-team directions;
- existing product profile when updating;
- customer references or metrics when available.

Read [evidence-policy.md](references/evidence-policy.md) before strengthening any claim. Read [icp-model.md](references/icp-model.md) when defining ICP, anti-ICP, and hard gates.

## Procedure

1. Identify the canonical problem rather than the feature set.
2. Define the anti-problem: adjacent situations that should not buy.
3. Define measurable outcomes and their evidence status.
4. Describe ICP conditions across problem, maturity, workflow, technical, organizational, economic, and timing dimensions.
5. Define anti-ICP and structural disqualification conditions.
6. Map sponsor, terrain owner, users, and veto players.
7. Separate proven, plausible, planned, and unknown capabilities.
8. Define hard gates and the canonical proof pattern.
9. Record alternatives and when they are better.
10. Record unknowns explicitly and increment `profile_version` when canonical truth changes.
11. Write one profile under `product_catalog/OFFER-<id>_<slug>.yaml` conforming to `contracts/product_profile.schema.yaml`.

Store raw sources separately under `evidence/product/<product>/`.

## Boundaries

Never:

- research or score a named account;
- import account-study evidence into a canonical profile unless it is a formal reference case;
- hide unknown pricing, architecture, deployment, security, or references;
- strengthen a product aspiration into a proven capability without stronger evidence;
- merge all offers into a monolithic catalog document.

Fail the update if the ICP is only firmographic, the anti-ICP is missing, a hard gate is only a score, capabilities lack evidence status, or product claims become stronger without stronger sources.
