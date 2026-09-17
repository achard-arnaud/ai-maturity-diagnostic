# Document composition & export options (candidate Epic E17)

Status: **RESEARCH ONLY**. No runtime code was written or modified to
produce this document, and nothing here authorizes building or wiring an
exporter. Prepared for francois.arnaud.rjc@gmail.com as an input to the
architecture owner's E17 scoping decision, per the repo's own harvest gate
G4 ("no new search engine, editor, exporter or notes system is built before
auditing existing repos and libraries" —
`docs/research/next-wave/HARVEST_SEARCH_SOCIAL_NETWORKS.md` §9). This is
CLAUDE_01 Workstream F.

This document assumes and builds on
[`HARVEST_NOTES_STORYTELLING.md`](./HARVEST_NOTES_STORYTELLING.md) §5
(document generation / DOCX / render-QA boundary), which already compared
`build_org_tech_note.py` and `scripts/check_release.py`'s DOCX gate against
`skills-notes-and-storytelling`'s `output-spec.schema.json` /
`qa-report.schema.json` / `docx-runtime-interface.schema.json` contracts and
reached a scoped `EXTRACT_PATTERN` verdict. That comparison is not repeated
here. This document instead (a) inventories *every* export/render use case
in this repo, including one the earlier note did not cover, and (b)
arbitrates OpenCanva-or-alternatives at BUILD/PLUGIN/SERVICE/HYBRID/DEFER
level, as this workstream's brief specifically asks.

---

## 1. OpenCanva / alternatives signal check

Searched the full repo (`.md`, `.py`, `.js`, `.yaml`, `.json`, case-
insensitive) for `opencanva`, `open-canva`, `open canva`, `canva`. **Zero
references anywhere** — not in any `SKILL.md`, contract, script, ADR,
governance doc, or the two prior harvest notes. No named alternative
composition/export tool (Canva API, Google Slides API, a template-engine
SaaS, etc.) is referenced anywhere in this repo or in either of the two
repos already harvested (`search-social-networks`,
`skills-notes-and-storytelling`) either.

**There is zero existing signal of demand for OpenCanva or a named
alternative in this codebase.** Per the brief's own instruction, this leans
the arbitration toward DEFER for that specific tool unless the export-use-
case inventory below turns up real, unmet demand beyond what already ships.
It does not.

---

## 2. Full export/render use-case inventory

Grepped `docx|pptx|pdf|export|render` across `skills/`, `app/`, `scripts/`
(46 raw hits; filtered below to genuine export/render/composition surfaces,
excluding unrelated HTML-page-serving code in `app/authruntime/app.py` and
an unrelated `arxiv` API export param in `scripts/advanced_research.py`).

### 2a. `build_org_tech_note.py` (DOCX) — already covered in depth

Covered fully in `HARVEST_NOTES_STORYTELLING.md` §5. Summary for
cross-reference only: python-docx + Pillow renderer, hand-authored JSON
config, structural-schema validation only (no visual QA), gated in
`scripts/check_release.py` ("DOCX example configuration" /
"DOCX example generation" against
`skills/tech-leadership-org-intelligence/assets/examples/isagri_config.json`).
This is the **only** export use case the earlier note found, because it was
scoped to comparing against `skills-notes-and-storytelling`.

### 2b. `nice-output-engine` (HTML/PDF/PNG) — NOT covered by the earlier note; the most important new finding here

`skills/nice-output-engine/` is a second, complete, independently-built
rendering skill:

- **Pipeline:** Jinja2 templates (`templates/document.html.j2`,
  `templates/universal-document.html.j2`) → HTML → Playwright-driven
  Chromium → PDF and per-page PNG screenshots
  (`scripts/render.py::render_browser`, `page.pdf(...)`,
  `requirements.txt`: `Jinja2>=3.1`, `playwright>=1.45`).
- **Templates registered** in `templates/manifest.json`: `executive-brief`
  (A4 landscape, 1-2 pages), `benchmark-matrix` (A4 landscape, 2-4 pages),
  `business-note` (A4 portrait, 5-7 pages), `application-pack` (A4 portrait,
  2-7 pages) — a real, in-use template catalog, not a stub.
  `SKILL.md`: "Add templates progressively... Register every template in
  `templates/manifest.json`... Reuse `templates/universal-document.html.j2`
  for new narrative families before creating another renderer."
- **Content contract:** `references/output-contract.md` defines
  `universal-sections-v1`: "a universal page contains a header, optional
  decision, ordered sections, and blocks. Blocks may contain a title,
  evidence status, metric, body, bullets, or a table with at most five
  columns." This is a real, already-shipped structured-block content model
  (see also `RICH_EDITOR_ADR_OPTIONS.md` §5).
- **Visual QA already exists in code**, not just schema: `scripts/qa.py`
  drives Playwright to inject a DOM-inspection script
  (`MIN_FONT_PX = 12.0` / 9pt, `MIN_PADDING_PX = 12.0` / 9pt) that detects
  element overlaps, overflow, out-of-bounds elements, and undersized
  fonts/padding per rendered page, and takes page screenshots for manual
  100%/150% review (`SKILL.md` §"Render and validate", step 4: "Inspect
  every page PNG at 100% and 150% using the visual-review rubric").
- **Consumers:** `skills/business-intelligence-nice/SKILL.md` and
  `skills/application-nice/SKILL.md` both explicitly invoke
  `$nice-output-engine` for visual artifacts, with an explicit
  source-of-truth discipline: *"Use HTML/PDF/PNG rendering only for a
  polished artifact; retain a structured Markdown or JSON source of
  truth... If the rendering skill is unavailable, deliver the validated
  functional content and state that visual production remains pending."*
  (`business-intelligence-nice/SKILL.md`).
- **Not gated in CI.** `scripts/check_release.py` gates only
  `build_org_tech_note.py`'s DOCX example (§2a); it never invokes
  `nice-output-engine`'s `render.py` or `qa.py`. `.github/workflows/qa.yml`
  installs Node/Playwright only for the browser E12 E2E gate
  (`scripts/run_e2e_gate.py`), a different Playwright installation (npm) from
  the one `nice-output-engine` needs (pip `playwright>=1.45`). The only test
  reference found (`tests/test_control_plane.py:28`,
  `self.assertIn("nice-output-engine", skill_ids)`) checks that the skill is
  *registered* in a catalog, not that it renders correctly. **This is a real
  gap worth naming: a working HTML→PDF/PNG pipeline with its own visual-QA
  script exists and ships, but nothing in CI proves it still renders
  correctly after a change.**

**Why this matters for the OpenCanva arbitration:** the product does not
lack a composition/export capability beyond DOCX. It has *two* renderers
already — one for DOCX (structured org/tech notes), one for
HTML/PDF/PNG (four template families covering executive briefs, benchmarks,
business notes, and application packs) — with the second one already
including a page-layout visual-QA loop that is, in some respects (automated
overlap/overflow/font-size detection, not just structural JSON validation),
more advanced than what the DOCX path has. There is no PPTX generator
anywhere in the repo.

### 2c. `scripts/check_release.py`'s "DOCX example configuration/generation" gate

Read in full (lines ~95-140+). Confirmed: this gate exercises only §2a
(`build_org_tech_note.py --validate-only` then a full `--output` render
against the one checked-in example config). It does not touch
`nice-output-engine` at all (§2b) — confirming §2b's CI gap directly rather
than by absence.

### 2d. Non-composition "export" hits (for completeness, explicitly out of scope)

- `app/reach_channel_adapter.py`: `ManualExportRecord`/`build_manual_export`
  — this is a manual-outreach-channel record for a human to execute by hand
  (e.g. a phone call script), not a document/composition export. Unrelated
  to E17.
- `app/authruntime/app.py`: `_render_*_page` functions return
  `HTMLResponse` for internal admin/control-plane pages (memberships, audit,
  overrides). Ordinary server-side page rendering, not a document
  composition/export feature.
- `scripts/advanced_research.py`: `export.arxiv.org` is an external API
  hostname, unrelated to this repo's own export capability.

None of these change the inventory in §2a/§2b.

---

## 3. Arbitration: BUILD / PLUGIN / SERVICE / HYBRID / DEFER

Applying the brief's own framing — "if there's zero existing signal of need
beyond the one DOCX generator, say so plainly and lean DEFER unless you find
real evidence of demand for PDF/HTML/PPTX beyond DOCX" — with the correction
that this research *did* find more than the one DOCX generator (§2b):

- **OpenCanva specifically: DEFER.** Zero references anywhere in this repo
  or either harvested repo (§1). There is no unmet need it would address:
  HTML/PDF/PNG composition already ships via `nice-output-engine`, and DOCX
  already ships via `build_org_tech_note.py`. Introducing a third,
  externally-hosted or third-party composition tool with no in-repo demand
  signal would duplicate capability that already exists, add a new
  dependency/licensing surface, and contradict G4's own audit-first
  discipline. No qualifying evidence was found to justify BUILD, PLUGIN,
  SERVICE, or HYBRID adoption of OpenCanva or any named alternative.

- **The broader "does E17 need new composition/export capability at all"
  question: mostly DEFER, with one narrow HYBRID item.** The repo does not
  lack PDF/HTML rendering (§2b exists and works) or DOCX rendering (§2a
  exists and is CI-gated). There is no PPTX use case anywhere in the repo —
  building one now would be speculative, not evidence-driven, so PPTX stays
  DEFER until a real use case appears.
  - The one **narrow, evidence-backed HYBRID recommendation**: close the CI
    gap found in §2b by adding `nice-output-engine`'s existing `render.py`
    `--html-only` smoke path (or a small subset of `qa.py`) to
    `scripts/check_release.py`, the same way `build_org_tech_note.py`'s
    example is gated today. This is "HYBRID" only in the sense that it
    wires two things that already exist (an existing renderer, an existing
    release gate script) together — it is explicitly **not** new
    composition/export functionality, and even this narrow item is a
    proposal for the architecture owner to weigh, not something this
    document authorizes.
  - If the architecture owner later finds real product demand for a richer
    composition surface than `universal-sections-v1`'s flat blocks (e.g. the
    scaffold/output-spec/QA-report pattern `HARVEST_NOTES_STORYTELLING.md`
    §5 flagged as `EXTRACT_PATTERN`), the natural home for that is **BUILD,
    scoped as new templates/blocks inside `nice-output-engine`** (which
    already has the extension point: "Add templates progressively... Reuse
    `templates/universal-document.html.j2` for new narrative families
    before creating another renderer") — not a new external SERVICE or
    PLUGIN dependency, since the in-repo renderer already covers the same
    ground.

---

## 4. Summary table

| Capability | Exists today? | Where | CI-gated? | Visual QA? | Verdict |
|---|---|---|---|---|---|
| DOCX generation | Yes | `build_org_tech_note.py` | Yes (`check_release.py`) | Structural only (no visual QA) | Ships; no action needed |
| HTML/PDF/PNG generation | Yes | `nice-output-engine` | **No** | Yes, in code (`qa.py`) — unused in CI | Close the CI gap (HYBRID, narrow); do not replace |
| PPTX generation | No | — | — | — | DEFER (no demand signal) |
| OpenCanva / named external composition tool | No | — | — | — | DEFER (zero references anywhere; would duplicate #1/#2) |

---

## Closing (required)

**PROPOSE_ONLY.** This document is an input to the architecture owner's E17
scoping decision, not authorization to build an exporter. Per this repo's
own harvest gate G4 ("no new search engine, editor, exporter or notes system
is built before auditing existing repos and libraries" —
`docs/research/next-wave/HARVEST_SEARCH_SOCIAL_NETWORKS.md` §9), this
document exists specifically to satisfy that audit requirement for a
candidate export/composition capability; it authorizes no runtime code,
dependency, CI change, or schema change — including the narrow CI-gap item
in §3. No exporter, external service, or new template/format should be
added on the basis of this note alone until an accepted ADR, written by the
architecture owner and informed by this research, says otherwise.
