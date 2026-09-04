---
name: nice-output-engine
description: Render structured, decision-ready content into polished HTML, PDF, and page PNG artifacts with isolated design tokens, selectable templates, minimum typography and padding, page-contract checks, and automated visual QA. Use after a functional skill has completed the research and content model, for executive briefs, benchmarks, business notes, application packs, or a new reusable document template. Do not perform research, scoring, or business analysis.
---

# Nice Output Engine

## Boundary

Accept a validated content specification from an upstream skill and own only composition, rendering, visual QA, and delivery. Never strengthen a claim, change an evidence status, invent a metric, or decide what the document should conclude.

Read [references/output-contract.md](references/output-contract.md) before mapping content. Read [references/template-catalog.md](references/template-catalog.md) when selecting or adding a template. Read [references/visual-review.md](references/visual-review.md) before final delivery.

## Select the output contract

1. Identify the requested artifact and audience.
2. Select the smallest registered template that can carry the decision logic.
3. Preserve the upstream evidence taxonomy and source identifiers.
4. Keep palette, typography, spacing, and page geometry in theme tokens.
5. Add a new template only when the content cannot be represented without distorting meaning.

Registered families:

- `executive-brief`: A4 landscape, one or two pages;
- `entity-two-pager`: A4 portrait, exactly two pages for company × material product × person meeting briefs;
- `benchmark-matrix`: A4 landscape, two to four pages;
- `business-note`: A4 portrait, five to seven pages;
- `application-pack`: A4 portrait, two to seven pages.

## Render and validate

1. Build: `python scripts/cli.py build <config.json> --output <dir> --name <artifact>`.
2. Smoke-test a template without Chromium when needed: append `--html-only`.
3. QA: `python scripts/cli.py qa <artifact.html> --report <qa.json> --screenshots <dir>`.
4. Inspect every page PNG at 100% and 150% using the visual-review rubric.
5. Improve hierarchy, density, alignment, wording, card heights, or theme tokens.
6. Rebuild and rerun QA. Deliver only after automated and visual checks pass.

## Non-negotiable rules

- Prefer 11 pt body text; never render below 9 pt.
- Prefer 11 pt card padding; never render below 9 pt.
- Permit no clipping, overlap, overflow, or out-of-bounds element.
- Use a diagram only when it replaces weaker prose.
- Limit tables to five columns; prefer three.
- Keep semantic colors stable within one artifact.
- Isolate the decision, recommendation, or next action from evidence detail.
- Re-render the PDF once with the PDF workflow before delivery.

## Add templates progressively

Register every template in `templates/manifest.json` with its page range, orientation, input family, and intended use. Reuse `templates/universal-document.html.j2` for new narrative families before creating another renderer. Add one representative example and test the minimum and maximum page contracts. Do not duplicate business logic inside templates.
