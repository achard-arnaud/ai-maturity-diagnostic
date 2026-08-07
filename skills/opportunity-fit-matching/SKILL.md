---
name: opportunity-fit-matching
description: Match an already-qualified enterprise demand profile against one or more versioned product profiles. Use when the user asks which offer fits a company, whether Astraforge is appropriate, how strong product fit is, which hard gates block a deal, how candidate offers compare, or whether to pursue, validate, nurture, or disqualify. Do not conduct fresh company research, redefine product truth, or design the final pilot.
---

# Opportunity Fit Matching

## Responsibility

Perform the only authorized crossing between account reality and product truth.

```text
enterprise demand profile + immutable product snapshots
-> eligibility gates -> fit dimensions -> comparison -> decision
```

## Required inputs

1. `05_enterprise_demand_profile.yaml` conforming to the enterprise contract.
2. One or more immutable product snapshots conforming to the product contract.

Stop and route backward if either side is missing. Do not reconstruct it from memory or chat.

Read [gates.md](references/gates.md) before eligibility decisions, [scoring.md](references/scoring.md) before scoring, and [decision-policy.md](references/decision-policy.md) before issuing a decision.

## Procedure

1. Verify versions, provenance, and boundary compliance on both sides.
2. Map each enterprise capability gap to candidate product problems and outcomes.
3. Apply offer-specific and generic hard gates before scoring.
4. Score only eligible offers.
5. Record contradictions, unknowns, and evidence sensitivity.
6. Compare the leading offer with at least one credible alternative when available.
7. State observable evidence that would invalidate every positive result.
8. Produce `06_product_fit_matrix.yaml` conforming to `contracts/product_fit.schema.yaml`.

## Rules

- Treat signal, need, product fit, and commercial commitment as different states.
- Never let a high score override a failed gate.
- Any blocker/critical `FAIL` forbids both `PURSUE` and `VALIDATE`; use `NURTURE` or `DISQUALIFY` as appropriate.
- Cap a decision at `VALIDATE` when a blocker/critical gate remains `OPEN`.
- Keep the top-level decision identical to the selected match decision and calculate scores with the canonical weights.
- Do not prefer the most sophisticated offer by default.
- Do not perform fresh research or detailed pilot design.
