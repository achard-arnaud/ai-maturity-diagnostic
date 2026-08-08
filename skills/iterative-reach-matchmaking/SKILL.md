---
name: iterative-reach-matchmaking
description: Build an evidence-bounded first-wave and second-wave stakeholder/reach strategy after a valid positive company-product fit, bridging ICP personas, private contact targets, organization/decision evidence, current newsflow and relevant company use cases. Use when the user asks who to contact first or next, which promoter/prescriber/user/technical/veto roles matter, how to expand a second round, or how current newsflow changes outreach timing. Do not recompute fit, infer authority from titles, send outbound messages, or target people before role/fit gates are satisfied.
---

# Iterative Reach Matchmaking

## Responsibility

Turn a valid opportunity fit plus existing company/person evidence into an iterative stakeholder map. This is the bridge from `which company + which offer` to `which validated people, in which order, for which discovery purpose`.

## Required inputs

- study manifest and valid positive `06_product_fit_matrix.yaml`;
- selected immutable product snapshot and ICP personas;
- `06b_contact_targets.yaml` when private contacts exist;
- enterprise demand profile;
- organization/decision evidence already collected, when available;
- newsflow evidence already collected, when available;
- company UC/value-chain artifacts when relevant.

## Preconditions

Stop or route backward unless:

1. selected decision is `PURSUE` or `VALIDATE`;
2. no blocker/critical fit gate is `FAIL`;
3. a blocker/critical `OPEN` is treated as a validation constraint and never silently overridden;
4. contact identities/relationships belong to the same company;
5. role currency remains explicit.

## Stakeholder roles

Use hypotheses, not titles-as-truth:

- `promoter`: economic sponsor/champion able to promote the problem/initiative;
- `prescriber`: influencer, domain or functional authority shaping the solution/decision;
- `terrain_user`: workflow owner/operator/user who can validate pain, baseline and adoption;
- `technical_sponsor`: architecture/data/AI/engineering owner relevant to feasibility;
- `veto_control`: security/risk/compliance/legal/procurement/control role that may gate execution.

A person can hold multiple hypotheses. Preserve evidence and confidence separately from the role label.

## Wave logic

### First wave
Prefer people with:

- current/dately validated role;
- strong persona/role overlap with the selected product ICP;
- direct relevance to the matched gap/use case;
- evidence of influence/ownership beyond title where available;
- a current newsflow or initiative trigger when relevant.

### Second wave
Expand when:

- no first-wave person is ready;
- sponsor/prescriber/terrain coverage is incomplete;
- the first contact should validate another stakeholder;
- a veto/control gate needs early qualification;
- org evidence suggests a different decision path.

Second wave is not lower quality by definition; it is a deliberate expansion of the stakeholder system.

### Validation-only
Use for stale roles, weak identity/mandate evidence, or people whose relevance must be confirmed before outreach.

## Newsflow

Newsflow may influence:

- `why_now`;
- which stakeholder to validate first;
- the discovery angle;
- timing priority.

It must never change product fit, score, gate status or authority truth.

## Procedure

1. Validate the selected fit and product snapshot.
2. Read existing contact targets; do not add unrelated people from memory.
3. Overlay product ICP personas with demand gaps/use cases and org/decision signals.
4. Assign stakeholder-role hypotheses and evidence refs.
5. Add current newsflow triggers as timing context only.
6. Classify each person into first/second/validation-only wave.
7. Create resolver actions for stale role, missing mandate, missing stakeholder lane or missing org evidence.
8. Write `06c_reach_strategy.yaml` conforming to `contracts/reach_strategy.schema.yaml`.
9. Do not draft/send outbound copy unless a separate user request routes to an approved communication workflow.

## Iterative handoffs

- Missing current role -> `person-opportunity-targeting` role-validation route.
- Missing org/decision evidence -> `tech-leadership-org-intelligence`.
- Missing demand/use-case relevance -> `enterprise-demand-intelligence` / `enterprise-use-case-intelligence`.
- Invalid/blocked fit -> `opportunity-fit-matching`.
- Valid reach map -> `engagement-pilot-design` for discovery/proof design.

## Quality gates

Reject or block a reach target when:

- company or offer IDs mismatch the selected opportunity;
- current role is asserted from title alone;
- authority is inferred without evidence;
- a fit blocker/critical FAIL exists;
- newsflow is used to manufacture product fit;
- person-level private data is published into public/sector artifacts.
