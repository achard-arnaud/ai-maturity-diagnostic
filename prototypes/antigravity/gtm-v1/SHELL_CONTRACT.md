# GTM V1 — Shell Contract

**Authority: NONE.** This document and everything under `prototypes/antigravity/gtm-v1/**`
is UX exploration. It fixes no domain, data, API, security or state-machine
decision. Every object shown is mock data conforming to the canonical shapes
named in `ANTIGRAVITY_00_UI_V1_MISSION.md` — no new canonical object is
invented here.

This takes over the Antigravity mission (`ANTIGRAVITY_00/01/02/03`) after
Antigravity itself could not deliver it. Same isolation rules, same
deliverables, same "no structuring decision" boundary — just executed by
Claude Code instead. Every screen's own `SCREEN_CONTRACT.md` cites this file
rather than repeating it.

## 1. Global shell

Rendered by `shared/shell.js`'s `GtmProtoShell.render(activeNav, options)`,
injected into a `<div id="gtmShell"></div>` present on every page — this is
the one piece of markup every screen shares, so the nav/header never drifts
between screens.

Slots:

```text
header:    workspace switcher · global search entry · create/add action ·
           notifications · current user
sidebar:   Home · Discover · Research · Fit · Targets · Reach · Engagement ·
           Pipeline · Insights   (daily sidebar, per mission doc)
           ── separator ──
           Admin / Automation & Settings   (present, visually secondary)
main:      screen content (the only part each screen's HTML owns)
context rail: optional, per-screen — declared, not injected by the shell
```

`activeNav` must be one of the 10 canonical nav ids and gets
`aria-current="page"`. The Admin item is always rendered but is visually
deprioritized (per "daily sidebar" guidance — Admin is not a daily-use
space).

## 2. Visual language — epistemic status vocabulary

Every badge below pairs an icon glyph + text label + color, per the mission's
"do not rely on color alone" rule — colorblind-safe and screen-reader-usable
without color. Defined once in `shared/components.css`, reused everywhere:

| Class | Glyph | Label | Meaning |
|---|---|---|---|
| `.epi-fact` | ● | Fait | Directly observed, sourced |
| `.epi-inference` | ◐ | Inférence | Derived from facts, not itself observed |
| `.epi-hypothesis` | ◇ | Hypothèse | Proposed, unconfirmed, falsifiable |
| `.epi-unknown` | ? | Inconnu | Explicitly not yet known |
| `.confidence` (`.confidence-high/med/low`) | ▮▮▮/▮▮▯/▮▯▯ | Confiance | Evidence strength, independent of epistemic status |
| `.freshness` (`.freshness-fresh/aging/stale`) | ⟳ | Fraîcheur | Time-since-verified, decays visually |
| `.source-badge` | 🔗 | Source | Always links to provenance, never bare text |
| `.blocker-badge` | ⛔ | Bloqué | An unresolved blocker; always pairs with a resolver CTA |
| `.version-badge` | v# | Version | Snapshot/assessment version, for anything with immutable history |
| `.human-decision-badge` | 👤 | Décision humaine | A human verdict, never a computed score standing alone |

`.epi-*` classes are mutually exclusive per fact instance (a claim is fact
*or* inference *or* hypothesis *or* unknown, never two at once) — this is a
UI rule, not a re-derivation of the domain's own claim-typing logic.

## 2b. Literal vs. generated markup

`shared/shell.js`'s `render()` looks for a `<template id="gtmMainContent">`
in the page and, if present, moves its contents into the injected
`#gtmMain` slot verbatim before anything else runs. Any page a reviewer or
`checks/check_screen.py` needs to inspect literally — **every `states.html`,
always** — must author its content this way (plain HTML inside the
template tag), not build it via JS string concatenation from
`mock-data.js`. Pages whose content is naturally data-driven (an
`index.html` rendering a mock company list) may build `#gtmMain` from
`mock-data.js` in a `<script>` instead — the checker never inspects those
beyond confirming the shell/stylesheet links are present.

## 3. Screen states

Every screen must be able to render, and its `states.html` demo page must
show all 8, one at a time behind a state switcher:

`default · loading · empty · error · blocked · stale · partial-data · success`

Rendered via `shared/components.css`'s `.state-banner` (a dismissible strip
at the top of `main`) plus, where relevant, an in-place empty/error state
replacing a list/table body. `default` and `success` look like normal
content — no banner; the other 6 all show a banner with an icon, one
sentence, and (for `blocked`) a resolver CTA per the "Blocker = action à
résoudre" pattern already established in the real product.

## 4. Mock data

`shared/mock-data.js` exports one small, internally-consistent fixture set
per canonical object (`Company, Person, Signal, ResearchCase, Evidence,
Demand, Product, ProductSnapshot, FitAssessment, TargetPlan, Sequence,
Touchpoint, EngagementEvent, Opportunity, Deal, Artifact`), cross-linked by
id (e.g. the same `company_id` appears in Signals, ResearchCases, Demands,
Fits for one demo account, "Acme Corp") so a reviewer can click through
Discover → Research → Fit → Targets on one coherent account rather than
disconnected screens. No screen invents its own ad hoc mock object shape.

## 5. Interaction rules (forbidden as simulated truth)

Per the mission doc, never simulate as real business behavior: automatic
Signal→Demand promotion, a Fit without a ProductSnapshot, a Target before a
valid Fit, an Opportunity created on an ungoverned click, authority inferred
from a title, engagement inferred from a sent email. Every mock CTA that
would cross one of these lines is rendered `disabled` with a tooltip
explaining what real gate blocks it (see each screen's own
`DECISION_REQUIRED` section for the exact gate).

## 6. Responsive breakpoints

Reuses the production shell's own breakpoint (`ADR-010`'s 720px mobile /
900px tablet split, confirmed in `docs/research/next-wave/
RESPONSIVE_ANDROID_OPPORTUNITY.md`) so a reviewer comparing prototype to
production isn't comparing against a different breakpoint contract:
`Desktop >900px · Tablet 720–900px · Mobile ≤720px`.

## 7. Compliance check

`checks/check_screen.py <screen-dir>` is this contract's executable form —
run it against every screen directory before calling that screen done. It
does not replace human/design review; it only catches missing states,
missing contract sections, and shell/vocabulary drift.
