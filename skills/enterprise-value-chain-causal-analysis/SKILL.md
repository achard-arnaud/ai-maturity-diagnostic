---
name: enterprise-value-chain-causal-analysis
description: Decompose one company use case into its surrounding operating/value chain and causal constraints using Porter-style activity mapping and Ishikawa categories, while preserving company evidence, unknowns and validation questions. Use when a known enterprise use case needs upstream/downstream workflow analysis, handoffs, control points, value effects, root-cause hypotheses or adjacent-workflow discovery. Do not load products, infer demand from ICB/sector patterns, or promote adjacent workflow hypotheses into canonical use cases.
---

# Enterprise Value-Chain & Causal Analysis

## Responsibility

Explain where an already evidenced company use case sits in the wider operating chain and what may constrain its outcome. Porter and Ishikawa are analytical lenses, not evidence sources.

## Required inputs

- one managed company study;
- `05b_use_case_inventory.yaml`;
- the target `use_case_id`;
- product-blind study evidence and claim IDs;
- optional prior `05c_value_chain_causal_map.yaml` for refresh.

## Procedure

1. Confirm the target UC exists in the company inventory.
2. Trace only evidence-supported upstream/focal/downstream activities and support activities.
3. Identify handoffs, control points and observable value effects across value/cost/quality/time/risk.
4. Decompose supported or explicitly hypothetical causes into: people, process, technology, data, governance/control, environment/external.
5. Separate facts from hypotheses. Every analytical inference must keep a basis/evidence reference or an explicit unknown.
6. Identify adjacent workflow hypotheses only when the existing evidence or workflow structure supports the relation.
7. Never create a new canonical UC. Emit a validation question and route any candidate back to `enterprise-use-case-intelligence`.
8. Write/refresh `05c_value_chain_causal_map.yaml` conforming to `contracts/value_chain_causal.schema.yaml`.

## Porter lens

Use a practical operating-chain interpretation rather than forcing textbook categories. Preserve:

- upstream activity/input;
- focal activity performed by the UC;
- downstream activity/output/decision;
- support activities such as technology, HR/capability, procurement/vendor, data and governance;
- handoffs and control points;
- effects on value, cost, quality, time and risk.

Do not claim a complete corporate Porter value chain from one UC.

## Ishikawa lens

Use six default causal branches:

- people;
- process;
- technology;
- data;
- governance/control;
- environment/external.

A category may be empty. Do not fill it to make the diagram look complete.

## Handoffs

- Candidate adjacent workflow -> `enterprise-use-case-intelligence` for evidence validation/canonicalization.
- Organization/person question -> `tech-leadership-org-intelligence` or role validation, without assigning authority.
- Product/matching question -> stop; this skill is product-blind.
- Same-company related UC exploration -> derived UC graph.

## Quality gates

Fail or remain incomplete when:

- the target UC is not canonical in `05b`;
- product/offer language appears as evidence;
- ICB membership substitutes for company evidence;
- an adjacent workflow is silently promoted to a UC;
- an Ishikawa cause is asserted without basis;
- the analysis claims a complete enterprise value chain from partial evidence.
