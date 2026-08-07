---
name: business-intelligence-nice
description: Produce evidence-grounded business intelligence for Sarah-Pro, from a decision question through corporate strategy, organization and power, hiring and capabilities, newsflow, enterprise demand, offer truth, benchmarking, fit, and pilot design. Use for company or market analysis, strategic intelligence, due diligence, benchmarks, business notes, decision briefs, transformation diagnostics, offer/ICP work, or executive recommendations. Keep functional analysis independent from visual rendering and use nice-output-engine only after the content and evidence contracts are complete.
---

# Business Intelligence Nice

## Operating principle

Answer the decision before decorating the answer. Build the functional substance, evidence ledger, contradictions, options, and recommendation first. Hand a frozen content specification to `$nice-output-engine` only after the analysis passes its gates.

Read [references/sarah-pro-operating-model.md](references/sarah-pro-operating-model.md) for Sarah-Pro defaults. Read [references/research-and-evidence-os.md](references/research-and-evidence-os.md) before substantive research. Read [references/template-playbooks.md](references/template-playbooks.md) when selecting the final artifact. Read [references/capability-harvest-map.md](references/capability-harvest-map.md) only when the request spans several intelligence lanes.

## Frame the decision

1. State the audience, decision, entity, geography, time horizon, cutoff date, and excluded scope.
2. Identify up to three unknowns capable of changing the recommendation.
3. Select only the intelligence lanes required by the decision.
4. Choose the output family provisionally; never let a page target distort the research.
5. Proceed with explicit assumptions when missing information is non-critical. Ask only when the answer would materially change the mission.

## Select intelligence lanes

- **Corporate trajectory** — priorities, economic drivers, funded transformation, capabilities, and the real role of AI.
- **Organization and power** — legal structure, leaders, decision rights, RACI hypotheses, influence, and vetoes.
- **Hiring and capability** — team model, delivery, platform, governance, adoption, sourcing, and maturity signals.
- **Newsflow and momentum** — announcements versus execution, partnerships, launches, appointments, incidents, and build-buy-partner posture.
- **Enterprise demand** — observable desired state, current capability, material gaps, timing, sponsors, terrain owners, and constraints.
- **Offer truth and ICP** — canonical problem, anti-problem, outcomes, capabilities, evidence, ICP, anti-ICP, gates, alternatives, and unknowns.
- **Benchmark and fit** — eligibility gates, comparable options, weighted dimensions, sensitivity, falsifiers, and decision.
- **Proof and action** — smallest representative test, baseline, KPI, guardrails, responsibilities, and `SCALE | ITERATE | STOP` criteria.

Never execute every lane by default. Use a full pass only for a complete diagnostic or due diligence.

## Build the decision spine

Use this chain:

```text
source -> atomic fact -> implication -> decision relevance
-> option or capability gap -> falsifier -> recommendation -> next action
```

Separate account reality from offer truth until an explicit fit stage. Apply gates before scores. Compare every positive recommendation with a credible alternative, including a non-AI, process, rule, tool, or management response when relevant.

## Produce the functional package

Before rendering, complete:

1. executive answer and decision requested;
2. evidence ledger with dates, grades, confidence, and contradictions;
3. analysis by selected lanes;
4. options, trade-offs, exclusions, and falsifiers;
5. recommendation with conditions and confidence;
6. owner, next action, validation question, and stop condition;
7. a content specification conforming to `assets/business-intelligence-content.schema.json`.

Do not compress uncertainty to fit a visual. Return incomplete evidence to research and return excessive content to synthesis.

## Render separately

Select the smallest useful output contract and invoke `$nice-output-engine` with the frozen content specification. Use HTML/PDF/PNG rendering only for a polished artifact; retain a structured Markdown or JSON source of truth. If the rendering skill is unavailable, deliver the validated functional content and state that visual production remains pending.

## Quality gates

- Every material conclusion has direct support, triangulation, or an explicit inference label.
- Dates of announcement, event, launch, deployment, and observation remain distinct.
- Titles do not prove power; job postings do not prove deployed capability; partnerships do not prove adoption.
- Unknown pricing, ownership, maturity, baseline, or access remains unknown.
- A failed blocker cannot be averaged away by a score.
- The recommendation states what evidence would reverse it.
- The final action is bounded, owned, measurable, and reversible where possible.
