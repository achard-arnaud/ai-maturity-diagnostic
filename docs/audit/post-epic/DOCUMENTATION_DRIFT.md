# Documentation Drift — verified 2026-09-17

## 1. The drift already identified: `AGENTS.md` line 219

```
AGENTS.md:219:Les menus principaux restent `Demande`, `Offres`, `Qualification`, `Nudging`, `Suivi`, `Skills`. Porter/Ishikawa, patrimoine UC et Reach sont des vues contextuelles reliées aux artefacts existants ; ils ne deviennent pas des silos ou vérités concurrentes.
```

Confirmed stale: E12 (merged, `main`@`7a8a618`) ships a completely different
primary navigation — `app/frontend/router.js` defines exactly nine spaces:
`home, discover, research, fit, targets, reach, engagement, pipeline,
insights`, served at `/w/{workspace}/{space}`. The old six-item menu
(`Demande/Offres/Qualification/Nudging/Suivi/Skills`) still exists in the
DOM (`index.html`'s `#legacyNav`) but is **hidden by default**
(`id="legacyNav" class="hidden"`) and only reachable via `?legacy=1` — it is
explicitly *not* primary navigation any more, confirmed by
`tests/test_gtm_shell_quality.py::test_legacy_panels_remain_for_one_release_but_not_in_primary_nav`.

Confirmed: `docs/governance/SUPERSESSION_REGISTRY.md`'s "Vocabulary
alignment" section (E00-S02, before E12 existed) only rules on
`AGENTS.md`'s *object* vocabulary (network/enterprise/product/commercial/
learning) matching `02_DOMAIN_AND_TRUTH_MODEL.md` — it says nothing about,
and cannot have anticipated, a navigation replatform that happened 12 Epics
later. The task's framing is correct: that decision does not cover the nav
change, and nothing since has revisited it.

## 2. The same drift also exists in `README.md` — not previously flagged

```
README.md:261:Les menus principaux restent volontairement compacts : **Demande · Offres · Qualification · Nudging · Suivi · Skills**. Les vues Reach, Porter/Ishikawa et Patrimoine UC sont contextuelles afin d'éviter un CRM parallèle.
```

Identical wording problem to `AGENTS.md:219`, in the "### Navigation et
suivi" section (`README.md` lines 259–266). This section is not a passing
mention: `README.md` lines 166–266 (~100 lines, "## Control plane v0.6 —
parcours demande, matching et nudging") describe the pre-GTM control plane
in detail — ASCII menu diagram at lines 173–176
(`DEMANDE / OFFRES / QUALIFICATION / NUDGING`), a "### Catalogue de demande"
subsection, a "### Qualification et matching" subsection, a "### Nudging"
subsection, and the "### Navigation et suivi" subsection containing line
261 — all written in the present tense as if this is still the live
interface.

## 3. Broader than one line: `README.md` and `AGENTS.md` never mention the
GTM replatform at all

Grepped both files for every GTM space name and for "GTM" itself
(`Home.*Discover`, `Pipeline`, `Insights`, `GTM`): **zero matches in either
file.** Between them, `README.md` and `AGENTS.md` are the two top-level
documents most likely to be read first by a new contributor or agent, and
neither one mentions that:
- Thirteen Epics (E00–E13) beyond the README's own "v0.9 CRM" have shipped
  since the README's title was last updated to `v0.9`.
- The frontend has been replatformed (E12) onto a job-based, nine-space,
  URL-routed shell (`ADR-010`), with the old panel-based UI demoted to an
  opt-in legacy mode.
- An Insights/cost/governed-learning layer (E13) now exists with its own
  API and UI space.

This is a larger gap than the single menu-vocabulary line: the two
documents describe a snapshot of the product from before Epic 01 even
started, with no forward pointer to `docs/gtm-transformation/` or to the
Epic acceptance records in `docs/governance/` for anyone who lands on
`README.md` first.

## 4. Tests: none assert the old menu vocabulary

Grepped `tests/` for `Demande.*Offres`, `Qualification.*Nudging.*Suivi`,
`"Demande"`, `'Demande'`: **no test asserts the old menu labels as current
UI content.** (One `tests/e2e/journey-c-company.spec.ts` match was a
false-positive from an unrelated broader pattern, re-checked and confirmed
not to reference the six-item menu.) So this drift is documentation-only —
no test would need to change alongside a doc fix, and no test is silently
protecting the stale wording.

## 5. `feat/prospection-principes-todo` — present-tense "unmerged branch"
wording is now stale (branch → tag)

Nine governance documents describe this branch in the present tense as
retained-but-unmerged:
`docs/governance/EPIC_00_ACCEPTANCE.md:27`,
`docs/governance/TRACEABILITY_MATRIX.md:40`,
`docs/governance/EPIC_02_ACCEPTANCE.md:50-53`,
`docs/governance/EPIC_03_ACCEPTANCE.md:62-63`,
`docs/governance/EPIC_04_ACCEPTANCE.md:74-78`,
`docs/governance/EPIC_05_ACCEPTANCE.md:78-81`,
`docs/governance/EPIC_06_ACCEPTANCE.md:76-77`,
`docs/governance/EPIC_07_ACCEPTANCE.md:70-73`,
`docs/governance/EPIC_08_ACCEPTANCE.md:77-80`,
`docs/governance/EPIC_09_ACCEPTANCE.md:75-78`,
`docs/governance/EPIC_10_ACCEPTANCE.md:75-79`,
and `docs/governance/SUPERSESSION_REGISTRY.md:50`.

As of this audit the branch does **not** exist on `origin` as a live branch
(`git ls-remote --heads origin` does not list it) — it exists only as
`refs/tags/archive/pre-gtm-cleanup-2026-09-16/feat-prospection-principes-todo`.
The underlying decision (leave it unmerged; it fails the package validator)
is unaffected and does not need re-litigating — only the "still on a
branch" phrasing across these twelve files is now inaccurate. Lowest-priority
item in this list (cosmetic; the skill content is unreachable either way).

## 6. Epic 11 has no spec doc and no acceptance record — a documentation-
authority gap, not just a wording drift

Every Epic 00–10, 12 and 13 has both a
`docs/gtm-transformation/epics/EPIC_0X_*.md` (or, for 12/13, an equivalent
ADR/known-limitations record) **and** a `docs/governance/EPIC_0X_ACCEPTANCE.md`.
Epic 11 ("Opportunity, Proof, Deal and Expansion") has **neither** — its
only written record is six `docs/governance/sprint-log/E11-S0[1-6]_STOP.md`
files and a one-line mention each in
`docs/gtm-transformation/12_PROGRAM_ROADMAP.md` and
`01_AS_IS_AUDIT_AND_GAP_MAP.md` (gap row G13). The code and tests for E11
are real and substantive (verified — see `EPIC_DELIVERY_MATRIX.md`), so this
is not a "did the work happen" gap, but it is a governance-consistency gap:
anyone auditing "is Epic 11 accepted?" the way every other Epic can be
checked (its own `EPIC_XX_ACCEPTANCE.md` "Go/No-Go" line) will find nothing
for E11. **Closed in this same closeout pass**:
`docs/governance/EPIC_11_ACCEPTANCE.md` was authored retroactively from the
six STOP files, following the exact template every other Epic uses.

## 7. Epic 13's STOP files live in a different place with a different name
than every other Epic's

Every other Epic's sprint STOP files are
`docs/governance/sprint-log/E0X-S0Y_STOP.md`. Epic 13's are
`docs/governance/EPIC_13_S0Y_STOP.md` — one directory up, and
`EPIC_13_S0Y` instead of `E13-S0Y`. Functionally harmless (this audit found
and read them without difficulty), but it breaks the otherwise-consistent
`docs/governance/sprint-log/` convention that a tool or future audit might
reasonably assume holds for all thirteen Epics.

## 8. Acceptance-record claim not matched by code: E12-S03's "real
endpoints" claim — FIXED in this closeout pass

`docs/governance/sprint-log/E12-S03_STOP.md` states: "Home, Discover and
Research now render workspace-scoped queues from their real endpoints
inside the route-owned GTM view." True for Home and Discover. **Was false
for Research as shipped**: the Research space calls
`GET /api/v1/workspaces/{workspace}/research-cases`, and no backend route
by that name existed anywhere in `app/` (see `FRONT_BACK_ROUTE_MATRIX.md`
for the full trace) — despite the underlying store function
(`app.research_case_store.list_cases`/`get_case`) already existing, fully
tested, and simply never wired to an HTTP route. This was the one place in
this audit where a governance document's own claim did not match the
running code — everywhere else checked, the STOP/ACCEPTANCE record's claim
was accurate once its own self-declared deferrals are taken into account.

**Fixed same pass**: `app/research_routes.py` now exposes both routes over
the existing store functions; `tests/test_research_routes.py` gained 7
tests (written first against the broken route, confirmed failing, then made
to pass); `tests/test_gtm_upstream_spaces.py` was strengthened from a
string-match into a real request that would have caught this class of bug
(confirmed: fails on the pre-fix route file, passes after). A short
addendum was appended to `docs/governance/sprint-log/E12-S03_STOP.md`
itself recording the correction non-destructively, rather than editing its
original (inaccurate) claim out of the historical record.

## Summary table

| Location | Drift | Severity | Status |
|---|---|---|---|
| `AGENTS.md:219` | Old 6-item menu stated as current | Medium — already flagged by the requester | Fixed: supersession note added, old text kept as historical/legacy-mode record |
| `README.md:261` (+ lines 166-266 generally) | Same old menu, plus ~100 lines describing pre-GTM control plane as current | Medium-High — larger surface than AGENTS.md alone | Partially fixed: supersession banner + line-261 fix added this pass; a full restructuring of the ~100-line pre-GTM section is a follow-up, not done here |
| `README.md`, `AGENTS.md` overall | Zero mention of the GTM replatform (E00-E13) anywhere | High — systemic, not a single line | Fixed: both files now point to `docs/gtm-transformation/` and the GTM shell at the top |
| 12 governance docs | "unmerged branch" wording for `feat/prospection-principes-todo`, now a tag | Low — cosmetic | Fixed: wording updated in all 12 files |
| Epic 11 | No spec doc, no `EPIC_11_ACCEPTANCE.md` | Medium — governance-consistency gap, code itself is fine | Fixed: `docs/governance/EPIC_11_ACCEPTANCE.md` authored |
| Epic 13 STOP files | Wrong directory/naming convention | Low — cosmetic | Not fixed this pass — moving files risks breaking existing cross-references for a purely cosmetic gain; left as a known, low-priority item |
| `E12-S03_STOP.md` | Claims Research uses a "real endpoint"; it doesn't | **High — this is a real, functional bug, not just stale prose** | **Fixed: backend route implemented + tests added (see item 8)** |
