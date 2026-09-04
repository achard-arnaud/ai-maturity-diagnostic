---
name: executive-entity-briefing
description: Produce evidence-grounded one- or two-page meeting briefs about a named external company, its material products/frameworks/methods, and a named person. Use for "pitch me the company and the person", executive meeting preparation, founder/CEO briefings, or a Nice two-pager. Build canonical company, external-product and person intelligence atoms first, then assemble a persona-specific brief. Do not use internal offer ICP/product_catalog truth, recompute product fit, infer buying authority from a title, or let rendering change claims.
---

# Executive Entity Briefing

## Responsibility

Turn public evidence about an external company, its material offerings or intellectual assets, and a person into three canonical intelligence atoms plus one derived brief.

The canonical atoms are audience-neutral. Personal relevance for `francois-pro` or `sarah-pro` belongs only in the assembly layer.

Read [references/metaprompt.md](references/metaprompt.md) before research and [references/assembly-policy.md](references/assembly-policy.md) before writing the final brief. Reuse the evidence discipline from `../business-intelligence-nice/references/research-and-evidence-os.md`.

## Required inputs

- named company or resolvable organization;
- named person or resolvable role-holder;
- purpose: meeting prep, networking, diligence, interview, partnership or general briefing;
- audience persona: `francois-pro | sarah-pro | neutral`;
- cutoff date;
- optional user-provided lead/message/context.

## Canonical outputs

Write or return four independent objects conforming to the repository contracts:

1. `company_intelligence_atom` -> `contracts/company_intelligence_atom.schema.yaml`;
2. zero or more `external_product_intelligence_atom` -> `contracts/external_product_intelligence_atom.schema.yaml`;
3. `person_intelligence_atom` -> `contracts/person_intelligence_atom.schema.yaml`;
4. `executive_entity_brief` -> `contracts/executive_entity_brief.schema.yaml`.

The external-product atom describes products, services, platforms, frameworks, methodologies or named programs owned by the researched target. It is deliberately separate from `contracts/product_profile.schema.yaml`, which describes our own canonical offers.

## Procedure

1. Resolve company/person identity and note ambiguity before synthesis.
2. Research company trajectory, activity, business model, footprint and strategic signals.
3. Extract every named product, framework, methodology, platform, service family or program that materially explains positioning.
4. Assign product materiality: `core | material | supporting | incidental`.
5. Create a separate external-product atom for every `core` or `material` item.
6. Research the person's career spine, current role, expertise, public theses and observable contribution to company positioning.
7. Freeze source IDs, claim IDs, dates, epistemic status, contradictions and unknowns inside the atoms.
8. Assemble the final brief without strengthening or mutating the atoms.
9. If a Nice artifact is requested, hand the frozen brief to `$nice-output-engine` using `entity-two-pager`.

## Material-product gate

A `core` or `material` product/framework/methodology MUST:

- exist as its own external-product atom;
- be referenced from the company atom;
- appear by name in page 2 `product_spotlights`;
- receive a compact explanation of problem, promise, mechanism, role in positioning, proof status, differentiation and unknowns.

If this gate fails, the two-pager is incomplete even when the company and person prose is strong.

## Boundaries

Never:

- use `product_catalog/` as truth about the target company's offerings;
- convert a public title into buying authority or decision rights;
- merge company, product and person facts into one untraceable narrative object;
- place audience-specific fit inside a canonical atom;
- omit a material named product because the page is dense;
- invent revenue, client count, headcount, ownership, deployment scale or proof;
- treat a thought-leadership statement as deployed capability.

## Definition of done

- company, product(s) and person are separately addressable and source-linked;
- every material external product survives assembly;
- page 1 answers "who are they?";
- page 2 answers "what do they actually sell/build/teach, why does it matter, and what should I discuss?";
- audience fit is explicitly derived, not canonical;
- uncertainties and falsifiers remain visible;
- rendering is a downstream concern.
