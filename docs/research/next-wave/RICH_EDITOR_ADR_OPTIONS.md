# Rich editor ADR options (candidate Epic E16)

Status: **RESEARCH ONLY**. No runtime code was written or modified to produce
this document, and nothing here authorizes building or wiring an editor.
Prepared for francois.arnaud.rjc@gmail.com as an input to the architecture
owner's E16 scoping decision, per the repo's own harvest gate G4 ("no new
search engine, editor, exporter or notes system is built before auditing
existing repos and libraries" — see
`docs/research/next-wave/HARVEST_SEARCH_SOCIAL_NETWORKS.md` §9). This is
CLAUDE_01 Workstream E.

This document assumes and builds on
[`HARVEST_NOTES_STORYTELLING.md`](./HARVEST_NOTES_STORYTELLING.md), which
already audited `achard-arnaud/skills-notes-and-storytelling`'s document
model (fragments, claims, scaffolds) and its DOCX/render-QA boundary in
detail. It is not repeated here; where relevant this document cites it and
adds one net-new finding that note did not cover (§5).

---

## 1. What content model `ai-maturity-diagnostic` actually uses today

This is the load-bearing question for E16: an editor choice is meaningless
without first knowing what it would need to edit.

**Contract text fields (`contracts/*.schema.yaml`) are all plain, bounded
strings — never markdown, never structured JSON blocks.** Checked every
schema with a free-text field; representative examples:

- `contracts/claim_v1.schema.yaml`: `statement: {type: string, maxLength:
  500}` — a single bounded plain-text sentence, immutable (superseded, never
  edited in place per its own `x-rules`).
- `contracts/discovery_note_v1.schema.yaml`: `summary: {type: string,
  minLength: 1, maxLength: 4000}`, with an explicit rule: *"The summary is
  bounded to 4,000 characters to prevent the commercial log from becoming an
  ungoverned evidence store."* — a deliberate design choice against a large
  free-form/rich body field, not an oversight.
- All other free-text fields across the 60 schemas in `contracts/` follow
  the same shape: `{type: string}` with an occasional `maxLength`, no
  `format: markdown`, no nested block/array-of-rich-nodes structure anywhere.

**The one real DOCX generator (`skills/tech-leadership-org-intelligence/
scripts/build_org_tech_note.py`) confirms the same pattern end to end.** Its
input contract (`REQUIRED_TOP_LEVEL`, `REQUIRED_PERSON`) is a hand-authored
JSON config of plain strings and arrays of plain strings — e.g.
`bullets(document, cfg["method_notes"])` and `bullets(document,
cfg["unknowns"])` just iterate a `list[str]` into DOCX bullet paragraphs.
There is no markdown parser, no HTML-to-DOCX conversion, and no rich
inline-formatting (bold/links/citations) support in the renderer — every
string is rendered as flat text in one style.

**The frontend (`app/frontend/*.js`) renders no rich text anywhere and has
no authoring surface at all.** Audited `app.js` (982 lines), `router.js`,
`gtm-spaces.js`, `index.html`:

- Every dynamic view is built by string-templating already-escaped values
  through an `esc()` helper into `innerHTML` (cards, tables, kanban columns,
  badges) — read-only rendering of plain strings, not rich content.
- The **only** non-plain-text rendering in the whole frontend is a Mermaid
  diagram (`app/frontend/vendor/mermaid.min.js`, loaded via a plain
  `<script>` tag, no bundler) used once, in `buildMermaidGraph()`/
  `mermaidSafeId()` (`app.js:319-356`), to draw a use-case graph from
  structured node/edge data — not to render user-authored rich text.
- There is **no** `contenteditable`, no rich `<textarea>`-based authoring
  widget, no draft/save flow for any free-text field found anywhere in the
  frontend. Nothing today lets a user edit a claim statement, discovery-note
  summary, or note body as anything richer than whatever native HTML input
  the (unseen, since this session did not find one) authoring form uses.

**Conclusion for §1: there is no existing rich-content model to preserve
compatibility with, and no existing rich-text renderer to extend.** The
"content model fit" question for E16 is not "which library matches our
current rich model" (there isn't one) but "how much richness, if any, does
the product actually need to add, given every field today is a short,
governed, plain string." This materially changes the ADR's risk profile: the
cheapest option is not a migration, it is simply not building an editor.

---

## 2. The no-bundler constraint (ADR-010) is a real, direct tension

`docs/governance/ADR-010_GTM_FRONTEND_REPLATFORM.md` (accepted 2026-09-17,
scope: Epic 12) is explicit: *"Keep the existing dependency-free SPA for
E12... Do not introduce React, a bundler or a second client state store in
this Epic,"* conditional on navigation/workspace logic staying out of a
`app.js` monolith, with *"Failure to hold that boundary triggers a successor
ADR before E12 release."* The measured baseline it cites (`app.js` 885
lines / 72KB at the time) shows this is an actively-enforced constraint, not
a stale note — and the pattern holds today: Mermaid is loaded as a
plain `<script src="/vendor/mermaid.min.js">`, not as an npm dependency
bundled with a build step.

Every mainstream rich-text editor (ProseMirror, TipTap, Slate, Lexical,
Quill, EditorJS) ships as an npm package assuming a bundler (webpack,
Vite, Rollup) for tree-shaking, CSS-in-JS or plugin composition. Some
(TipTap, Quill) publish a UMD/CDN build that can be script-tagged like
Mermaid was, but with real costs: larger single-file payloads (typically
150-400KB+ minified for a usable feature set, versus Mermaid's ~600KB but
used for a single diagram render, not live editing), no tree-shaking of
unused plugins, and a CDN build is usually the *last* thing these projects
optimize, so it lags the bundler-first API surface and examples. **This is
the central tension the brief asked to flag explicitly: any rich editor
library is choosing E16 as the moment E12's no-bundler decision either holds
(accept a heavier, plugin-poor CDN build, or accept vanilla `contenteditable`
+ hand-rolled toolbar) or breaks (introduce a bundler, which ADR-010 treated
as a decision serious enough to need its own successor ADR, not a side
effect of picking an editor).**

---

## 3. Collaboration requirement check

Searched `app/` and `skills/` for any signal of real-time multi-user editing
(websocket, socket.io, CRDT, Yjs, operational-transform, "collab*",
"realtime"/"real-time"). The only matches are the Mermaid vendor bundle
(unrelated) and two unrelated business-content usages of the word
"collaboration" in `skills/ai-hiring-workspace-intelligence` (describing a
hiring team's cross-functional collaboration, not a software feature).
**No evidence anywhere in the repo of a requirement for simultaneous
multi-user editing of the same document.** This repo's actual concurrency
model is claim-level immutability with supersession
(`contracts/claim_v1.schema.yaml`'s `x-rules`: *"a claim is never silently
overwritten... status flips to superseded"*), which is a single-writer,
append-only pattern, not a multi-cursor live-editing pattern. Any editor
requiring CRDT/OT sync infrastructure (Yjs, ShareDB) would be solving a
problem this product does not have today.

---

## 4. Exportability check against the storytelling/DOCX pipeline

Per `HARVEST_NOTES_STORYTELLING.md` §5, `skills-notes-and-storytelling`
defines an `{OutputSpecification} → {DocumentQAReport}` interface
(`contracts/docx-runtime-interface.schema.json`) that assumes rendering is
"someone else's job." `ai-maturity-diagnostic`'s actual renderer,
`build_org_tech_note.py`, consumes plain strings/arrays directly with
`python-docx` — it does not parse markdown or HTML, and has no round-trip
path from a rich-text/JSON-blocks document model back into its JSON config
shape. Any editor whose native save format is richer than "plain string or
array of plain strings" would need a **new** export/flattening step before
it could reach either that renderer or the newer `nice-output-engine`
pipeline (see `DOCUMENT_COMPOSITION_EXPORT_OPTIONS.md`, which documents
`nice-output-engine`'s own `universal-sections-v1` block model: title,
evidence status, metric, body, bullets, or a ≤5-column table — itself a
flat, non-nested block shape, not a rich-text tree). An editor whose native
model already matches "flat blocks of plain text, bullets and tables" (e.g.
Markdown or a shallow JSON-blocks schema) would need little or no
flattening; a full inline-rich-text-tree model (ProseMirror/TipTap's native
`doc/paragraph/text+marks` schema) would need a dedicated serializer written
and maintained specifically for this repo's two renderers, since neither
implements a generic rich-document importer.

---

## 5. Net-new finding not covered by `HARVEST_NOTES_STORYTELLING.md`: a second render pipeline exists

`HARVEST_NOTES_STORYTELLING.md` scoped its DOCX/render-QA comparison to
`build_org_tech_note.py` and `scripts/check_release.py`'s two DOCX gate
steps. This document additionally found `skills/nice-output-engine/`, a
second, independently built rendering skill (Jinja2 + Playwright,
`requirements.txt`: `Jinja2>=3.1`, `playwright>=1.45`) that renders
HTML → PDF/PNG with a code-level visual-QA pass (`scripts/qa.py`: overlap,
overflow, out-of-bounds, small-font and low-padding detection via a
Playwright-injected DOM check) — already used by `business-intelligence-nice`
and `application-nice` per their `SKILL.md`s. This exists as an "input
family" contract, `universal-sections-v1` (`references/output-contract.md`):
"a universal page contains a header, optional decision, ordered sections,
and blocks. Blocks may contain a title, evidence status, metric, body,
bullets, or a table with at most five columns." That is itself a real,
already-shipped, flat structured-block content model — closer to the
"structured-JSON-blocks" editor archetype than anything else in this repo —
though it is a **render input contract**, not an editor: nothing produces or
edits `universal-sections-v1` JSON by hand today except an upstream skill's
own generation logic. `business-intelligence-nice`'s `SKILL.md` states the
intended source-of-truth split directly: *"Use HTML/PDF/PNG rendering only
for a polished artifact; retain a structured Markdown or JSON source of
truth."* This is the single strongest piece of existing-repo evidence for
which content model E16 should target, and it argues for Option 2 or 4
below over a full rich-text-tree editor. See
`DOCUMENT_COMPOSITION_EXPORT_OPTIONS.md` for the full inventory and export
arbitration.

---

## 6. Short-listed options

### Option 1 — Plain Markdown + a read-only/lightly-interactive viewer

Author content as Markdown strings (already compatible with every existing
`{type: string}` field, just with a documented lightweight syntax
convention); render with a small dependency-free Markdown-to-HTML function
or a single small vendored library (e.g. `marked`, ~40KB min, no bundler
required — script-taggable like Mermaid already is).

### Option 2 — Structured JSON blocks (Notion/EditorJS-style, or reuse `universal-sections-v1`)

Model documents as an ordered array of typed blocks (`heading`, `paragraph`,
`bullets`, `table`, `metric`), either adopting EditorJS's block model or —
more directly reusable — extending `nice-output-engine`'s own
`universal-sections-v1` shape (§5) into an editable form, since that schema
already exists, is already consumed by a shipped renderer, and already
matches the flat, non-nested string/array pattern used everywhere else in
the repo.

### Option 3 — ProseMirror/TipTap-style rich-text editor

A full inline-rich-text-tree editor (bold/italic/links/nested lists/tables/
citations as first-class inline marks and node types), the closest to a
"Google-Docs-like" authoring experience.

### Option 4 — No new editor; extend existing plain-text/Markdown fields

Add no editing library at all. Keep contract fields as bounded plain
strings (optionally documenting a Markdown subset as an informal
convention, without a parser), and let any richer presentation continue to
be generated by upstream skills into `nice-output-engine`/DOCX inputs rather
than authored by hand in the frontend.

## 7. Scoring

| Criterion | Opt 1: Markdown+viewer | Opt 2: JSON blocks | Opt 3: ProseMirror/TipTap | Opt 4: No new editor |
|---|---|---|---|---|
| Document-model fit with today's contracts (§1) | High — strings stay strings, syntax is a convention | Medium-High — needs new nested-array fields, but shape matches `universal-sections-v1` (§5) already | Low — native model is a rich node/mark tree, nothing in this repo produces or consumes that today | Highest — zero schema change |
| License | Permissive (MIT-class libs) | Permissive (EditorJS: Apache-2.0-class; or in-house, no license) | Permissive (MIT: ProseMirror, TipTap core) but TipTap's advanced/collab extensions are paid | Not applicable |
| Maintenance burden | Low — tiny surface, easy to hand-roll or vendor | Medium — schema + block-renderer to own | High — plugin/schema/serializer surface, steepest learning curve of the four | Lowest |
| No-bundler compatibility (§2) | High — CDN script tag, small payload | High — no framework required, plain JS render loop | Low — ecosystem assumes a bundler; CDN builds exist but are second-class and still sizable | Highest — nothing to load |
| Accessibility | Depends on hand-built viewer markup; straightforward for read-mostly content | Same as Opt 1, plus block-level ARIA roles needed | Editors generally invest in a11y (ProseMirror/TipTap have decent a11y track records) but only if configured carefully | Not applicable |
| Tables/images/links/citations | Markdown covers all natively; images/citations need a convention | Native per block type; matches `universal-sections-v1`'s existing ≤5-column table cap | Native and richest of the four | None beyond what a plain string can encode (a link as raw text/URL) |
| Plugin ecosystem | Small (Markdown extensions) | Small unless EditorJS adopted (then large) | Largest of the four | None |
| Collaboration (§3) | Not needed; not offered | Not needed; not offered | Not needed; available but unused complexity if adopted | Not needed |
| Exportability to DOCX/storytelling pipeline (§4) | High — Markdown → plain text/bullets is a short, well-understood mapping | High if built against `universal-sections-v1` — same shape the renderer already expects | Low — needs a bespoke serializer from a rich node tree down to flat strings/bullets/tables, maintained indefinitely | Highest — nothing to convert |
| Bundle/perf cost given no-bundler constraint | Low | Low | Medium-High | None |
| Lock-in | Low (Markdown is portable) | Medium (custom or EditorJS block schema becomes a de facto contract) | High (ProseMirror/TipTap document schema is not portable to another editor without a rewrite) | None |
| Migration path if outgrown | Add richer Markdown extensions or move to Opt 2 later | Add block types incrementally; can still degrade to Markdown per block | Downgrading later means discarding authored rich content or writing a lossy exporter | Adopting any of 1-3 later starts from a clean slate (no debt to unwind) |

## 8. Framing for the architecture owner (not a decision)

Given §1 (every existing field is a short bounded plain string, no rich
model exists to preserve), §2 (ADR-010's no-bundler constraint is a live,
enforced boundary that most rich-editor libraries assume away), §3 (no
collaboration requirement), §4 (both existing renderers consume flat
strings/bullets/tables, not rich trees), and §5 (a flat structured-block
contract, `universal-sections-v1`, already exists and is already consumed
by a shipped renderer), **the evidence points toward Option 4 (no new
editor) as the default, with Option 2 — built directly against the
already-existing `universal-sections-v1` block shape rather than a new
schema — as the only enrichment worth an ADR if the architecture owner
decides plain strings are genuinely insufficient.** Option 1 is a reasonable
middle ground if only inline emphasis/links are needed without new block
types. Option 3 is not supported by any evidence gathered here: there is no
existing rich-text renderer, no collaboration need, and a direct conflict
with ADR-010's no-bundler decision that would require its own successor ADR
before a ProseMirror/TipTap-class dependency could be introduced at all.

This is a recommendation for the architecture owner's ADR to weigh, not a
decision. It reflects what this research found in the repository as of
2026-09-17 and does not account for product-strategy considerations (e.g. a
planned authoring-heavy feature not yet reflected in any contract or skill)
that only the architecture owner and product owner would know.

---

## Closing (required)

**PROPOSE_ONLY.** This document is an input to the architecture owner's E16
scoping decision, not authorization to build an editor. Per this repo's own
harvest gate G4 ("no new search engine, editor, exporter or notes system is
built before auditing existing repos and libraries" —
`docs/research/next-wave/HARVEST_SEARCH_SOCIAL_NETWORKS.md` §9), this
document exists specifically to satisfy that audit requirement for a
candidate editor capability; it authorizes no runtime code, dependency,
schema change, or frontend change. No editor, library, or schema field
should be added on the basis of this note alone until an accepted ADR,
written by the architecture owner and informed by this research, says
otherwise.
