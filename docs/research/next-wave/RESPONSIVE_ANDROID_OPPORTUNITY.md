# Responsive / Android opportunity audit — candidate Epic E21

Status: **research and proposal only**. No runtime code was written or
modified to produce this document.

Source read in full: `tests/test_gtm_shell_quality.py`, `app/frontend/styles.css`
(316 lines), `app/frontend/router.js`, `app/frontend/gtm-spaces.js`,
`docs/governance/ADR-010_GTM_FRONTEND_REPLATFORM.md`,
`docs/audit/post-epic/FRONT_BACK_ROUTE_MATRIX.md`. Confirmed by direct
`find`/`grep`: no `manifest.json`, no service worker, and no PWA scaffolding
of any kind exists in `app/frontend/` today.

## 1. What `tests/test_gtm_shell_quality.py` and `styles.css` actually assert/implement — confirmed and extended

The prior E12 audit's findings are **confirmed exactly**:

- `test_accessibility_and_mobile_contracts` asserts `aria-current` in
  `app.js`, `focus-visible` in `styles.css`, one media query
  `@media (max-width: 720px)`, and `min-height: 44px` inside it.
- `test_navigation_has_telemetry_and_rollback_flag` asserts a
  `gtm:navigation` `CustomEvent` and the `?legacy=1` rollback path exist.
- `test_legacy_panels_remain_for_one_release_but_not_in_primary_nav`
  confirms the pre-E12 panel nav is still present but hidden
  (`id="legacyNav" class="hidden"`) and excluded from the primary GTM nav.

**Extending the audit**, `styles.css` (316 lines total) has exactly three
breakpoints, not one:

| Breakpoint | What it changes |
| --- | --- |
| `max-width: 900px` | `.analysis-grid`/`.edge-row` collapse to one column (Company-360/analysis views) |
| `max-width: 820px` | Header stacks vertically; `.split`, `.company-row`, `.use-case-list` collapse to one column; workflow-step grid narrows; panel padding shrinks |
| `max-width: 720px` (the one the test asserts) | Header stacks; nav becomes sticky with 44px-min-height buttons; `main` gets 16px inline padding; **all** `.grid`/`.split`/`.form` layouts force to one column; drawers go full-width |

So there is a genuine, if unlabeled, three-tier responsive scheme
(≈desktop / ≈tablet-ish 820-900px / ≈phone 720px), not a single
mobile-only breakpoint — but there is no dedicated tablet breakpoint in the
900–1200px range where a real tablet in portrait (e.g. 810px-wide iPad)
would actually sit between "phone" and "desktop" behavior; a device in that
zone gets the 820px rules (phone-shaped single-column layouts), not a
tablet-optimized two-column layout. This matters for the matrix below:
"tablet" today behaves like "small phone," not like its own tier.

Touch-target sizing (`min-height: 44px`) is applied to `nav button` only —
confirmed by grep, it is not a global rule. Buttons and interactive
elements inside space content (the generic card list in `gtm-spaces.js`,
form inputs, table row actions) have no asserted minimum touch-target size,
so 44px compliance is a navigation-chrome guarantee, not a page-content
guarantee.

## 2. Per-space FULL / READ / QUICK_ACTION / NOT_SUPPORTED matrix

Basis: `app/frontend/gtm-spaces.js`'s per-space config (generic card list
for 7 of 9 spaces, purpose-built rendering for Pipeline and Insights — per
`docs/audit/post-epic/FRONT_BACK_ROUTE_MATRIX.md` §"Generic-card vs.
purpose-built"), each space's actual write-capable routes (§ same doc's
per-space table), and the CSS breakpoints in §1. "Desktop" = >900px,
"Tablet" = 720–900px (today behaves like the 820px phone-adjacent rules,
per §1's finding), "Mobile" = ≤720px.

| Space | Desktop | Tablet | Mobile | Why |
| --- | --- | --- | --- | --- |
| **Home** | FULL | FULL | READ | Generic card list backed by the legacy `/api/follow-up` dashboard endpoint (read-only by nature — a follow-up digest); single-column collapse at 720px keeps it usable, but there is no mobile-specific quick action (e.g., "mark handled") wired in `gtm-spaces.js` today. |
| **Discover** | FULL | FULL | READ | Backed by `GET /api/v1/workspaces/{ws}/signals`, real endpoint, `require_workspace_access`-gated. `POST /signals/{id}/queue-research` exists server-side but is not exposed as a mobile-reachable action in the generic card renderer — reading signals works at any width, triggering "queue for research" from a phone does not today. |
| **Research** | READ | READ | READ | `FRONT_BACK_ROUTE_MATRIX.md` originally found this space calling a backend route that did not exist at all (`research-cases`), making it NOT_SUPPORTED at every width — **that was fixed in the same closeout pass this research was written in** (`app/research_routes.py` now exposes `GET /research-cases`/`GET /research-cases/{id}` over the pre-existing, pre-tested store functions). With the route fixed, Research is architecturally identical to Discover/Targets/Reach: a GET-only, generic-card, read-only space, so it collapses cleanly at 720px like the others — READ at every tier, same ceiling as Fit/Targets/Reach, not a mobile-specific gap. |
| **Fit** | READ | READ | READ | The backend has a real write path (`POST`/`PATCH /fit-assessments`, confirmed in the route matrix), but it is not exposed through the generic card UI at all today — no form/action for it is wired in `gtm-spaces.js`. So Fit's actual ceiling at any screen width is "read + gate-badge display," not "read + write," and every tier is capped at READ until that UI is built. |
| **Targets** | READ | READ | READ | `GET /target-plans` only (route matrix confirms GET-only router, no POST/PATCH). Generic card list. |
| **Reach** | READ | READ | READ | `GET /sequences` only (GET-only router). Generic card list. |
| **Engagement** | READ | READ | READ | `GET /conversations` only (GET-only router). Generic card list. |
| **Pipeline** | FULL | QUICK_ACTION | NOT_SUPPORTED | Purpose-built Kanban board (`config.board=true`, flattened stage columns) — the one space with genuinely custom rendering. A Kanban board is inherently the hardest layout to collapse to a phone width: `styles.css` has no board-specific mobile rule, and forcing `.grid`/`.split` to one column (the 720px rule) does not by itself turn a multi-column Kanban into a usable single-column stage list — that would need dedicated board CSS/JS this repo does not have yet. At tablet width the board is cramped but a single "move stage" quick action is plausible; at phone width, not supported without new work. |
| **Insights** | FULL | READ | NOT_SUPPORTED | Purpose-built `renderInsights()` — funnel/quality/cost metric tiles plus a LearningProposal review section with an admin-link handoff. Metric tiles can reasonably reflow to one column at 720px (generic grid collapse applies), but the LearningProposal review actions (`POST /learning-proposals/{id}/transitions`, a meaningful approve/reject decision) are not designed as touch-first controls, and reviewing a proposal's evidence-and-rationale on a phone screen is a poor experience even if technically reachable. |
| **Admin** | FULL | READ | NOT_SUPPORTED | `app/authruntime/app.py`'s admin pages are hand-rolled `<table border="1">` HTML with no responsive CSS applied at all (they don't load `styles.css`'s media queries the way the GTM shell does — they are separate, minimal HTML strings). Wide tables (users, memberships, audit log, overrides) do not reflow; they are usable at tablet width by horizontal scroll at best, and effectively unusable on a phone. |

## 3. Responsive web vs. installable PWA vs. TWA vs. Capacitor vs. React Native vs. native — grounded in ADR-010

ADR-010 is explicit and current (accepted 2026-09-17, Epic 12 scope): "Keep
the existing dependency-free SPA... Do not introduce React, a bundler or a
second client state store." This is a live, binding constraint, not
historical context — it was reaffirmed for E12 and nothing in E13's merge
supersedes it. Every option below is evaluated against that constraint
directly, not against a generic "pick a mobile framework" rubric.

| Option | Compatible with ADR-010 (no bundler, vanilla JS)? | What it would take | Verdict |
| --- | --- | --- | --- |
| **Responsive web (current)** | Yes — it is what exists | Already built; §1/§2 show it is a real but incomplete three-tier scheme | **Keep extending this first.** Lowest cost, zero new deployment surface, already has test coverage (`test_gtm_shell_quality.py`) to build on. |
| **Installable PWA (manifest + service worker)** | **Yes, cleanly.** A `manifest.json` is static JSON; a service worker is a plain `.js` file registered via `navigator.serviceWorker.register(...)` — no bundler, no framework, no build step. This is squarely inside "dependency-free vanilla JS." | Add `manifest.json` (name, icons, `display: standalone`, theme colors), a minimal service worker (cache the static shell files already listed in `server.py`'s `_STATIC_FILES`, and let API calls pass through — no offline business-data caching needed to get "installable"), register it from `index.html`. | **The clear near-term win.** It is the only mobile-delivery option that is simultaneously (a) fully ADR-010-compliant with no successor ADR needed, (b) buildable as additive files alongside the existing shell, and (c) gets a home-screen icon and standalone window on Android today. |
| **TWA (Trusted Web Activity)** | Compatible with the *web* side (a TWA just wraps an existing PWA in a thin native Android shell for Play Store distribution) | Requires the PWA above to exist first, plus a small separate Android project (Digital Asset Links, Play Store listing) — that project is native Android tooling, not a change to `app/frontend/`, so it does not touch ADR-010 at all | **A reasonable follow-on to the PWA, not a replacement for it** — only worth doing once there's a business reason to be in the Play Store specifically (vs. just "add to home screen" from the browser). |
| **Capacitor** | **No, not without a successor ADR.** Capacitor wraps a web app in a native shell but its own tooling (native plugin bridge, `npx cap sync`, platform projects) assumes an npm-based build pipeline — even a minimal Capacitor project introduces `package.json`-driven build tooling ADR-010 explicitly ruled out for the web shell itself. It could in principle wrap the *existing* unbundled JS/CSS/HTML as-is (Capacitor doesn't strictly require a bundler for the web content), but the project scaffolding and native plugin layer is new build-tooling surface the current ADR was written to avoid taking on. | Would need its own ADR justifying the added toolchain, scoped narrowly to "packaging," not to changing the frontend's authoring model | **Possible later, but only for native-API access the PWA can't get (e.g., contacts, deep OS integration) — not justified today.** |
| **React Native** | **No, directly contradicts ADR-010.** React Native requires a Metro bundler, a separate component model (not vanilla DOM/CSS), and effectively a rewrite of `app.js`/`gtm-spaces.js`/`router.js`/`styles.css` into JSX/RN components — exactly "introduce React... and a bundler," the two things ADR-010 names explicitly as rejected for this Epic's scope. | A full frontend rewrite plus new native build pipelines (Xcode/Gradle) | **Not compatible without superseding ADR-010 outright** — this would be a new architecture decision, not an E21 deliverable, and the measured-spike table in ADR-010 (0 build artifacts today vs. "new runtime/toolchain required") argues directly against it at current scale. |
| **Fully native (Kotlin/Swift)** | N/A — orthogonal to ADR-010 since it wouldn't reuse the web frontend at all | A second, independently maintained client duplicating every GTM space's UI logic | **Reject for now** — highest cost, no reuse of the existing (if imperfect) responsive shell, and nothing in the current gap analysis (a three-tier CSS scheme that mostly works, a missing PWA manifest) justifies that cost. |

**Recommendation: pursue the PWA path (manifest + service worker) as the
E21 near-term deliverable.** It is the only option that adds real
mobile/Android value (installable, home-screen icon, standalone display)
while staying fully inside ADR-010's current, accepted constraint — no
successor ADR needed. TWA is a plausible fast-follow once a PWA exists, if
Play Store presence specifically is wanted. Capacitor/React Native/native
should not be scoped into E21; any of them would require explicitly
superseding ADR-010 first, which is an architecture decision for the owner,
not something this research document should presuppose.

## 4. Candidate mobile jobs from the brief — realistic near-term wins vs. desktop-first

| Candidate job | Verdict | Why |
| --- | --- | --- |
| **My Day** (Home space digest) | **Near-term win.** Home is already READ-capable end-to-end (§2), backed by a simple list endpoint, and a daily-digest job is exactly what a phone-sized, read-first, single-column card list is good at. Needs no new backend route. |
| **Quick follow-up** | **Near-term win, with one addition.** Discover/Home already render actionable-looking cards; the missing piece is wiring a mobile-reachable "queue for research" or "mark followed-up" action into the generic card renderer (`gtm-spaces.js`) for the routes that already support it server-side (e.g., `POST /signals/{id}/queue-research`). This is UI wiring, not new backend work. |
| **Signal review** | **Near-term win.** Discover is READ-complete at every width today (§2); reviewing a signal list on a phone works now. |
| **Note capture** | **Desktop-first for now.** No note/annotation object or endpoint was found anywhere in the audited routes — this would be new backend work (a write endpoint plus a data model) before it is a frontend/mobile question at all; scoping it into E21 without that backend piece first would be premature. |
| **Meeting context** (presumably: Company 360 / research-case context before a call) | **Blocked, not just desktop-first.** Company 360 (`GET /api/v1/workspaces/{ws}/companies/{id}/360`, confirmed working) is READ-capable and could reasonably work on a phone, but the *research-case* half of "meeting context" runs into the confirmed Research-space defect (§2) — the backing route doesn't exist. Fix the backend defect first; then this becomes a near-term win, not before. |
| **Approve/reject** (LearningProposal transitions, Insights) | **Desktop-first.** Per §2, Insights is NOT_SUPPORTED on mobile — reviewing evidence/rationale and making an approve/reject call on proposal transitions is a decision-quality task better suited to a larger screen; the underlying data (evidence refs, hypothesis text) is not designed for phone-width review, and getting this wrong has real governance consequences (E13's proposal lifecycle). Not a responsive-CSS problem to fix — a UX-design problem for a screen this small. |
| **Read Company 360** | **Near-term win.** Already a real, working, workspace-scoped GET route; read-only Company 360 is a good fit for the existing 720px single-column collapse. |
| **Pipeline consultation** (read the board, not edit it) | **Near-term win, if scoped to read-only.** Per §2, Pipeline is FULL on desktop, QUICK_ACTION-plausible on tablet, NOT_SUPPORTED on phone for the *board* interaction — but "consultation" (viewing where deals stand, without dragging cards between stages) could be served by a phone-specific list view of the same `pipeline-board` data (stage-grouped list instead of Kanban columns) without needing the board's drag/column layout at all. That is new frontend rendering work, not a backend gap, and is a reasonable E21-scoped deliverable distinct from "make the Kanban board itself responsive," which is a harder, lower-priority problem. |

**Overall recommendation for E21:** ship the PWA shell (§3) plus the
already-READ-capable jobs (My Day, quick follow-up, signal review, read
Company 360, read-only pipeline consultation) as the near-term mobile
surface; treat note capture and meeting context as blocked on backend work
that exists independently of E21 (a notes endpoint — the Research-space
routing defect this paragraph originally also listed here was fixed in
this same closeout pass, see §2); and keep approve/reject decisions and full Kanban board
editing desktop-first by design, not as a temporary limitation to be
"fixed" later — they are large-screen, high-consequence tasks that a phone
form factor genuinely serves poorly.

---

**This document is a proposal for the architecture owner's E21 scoping
decision, not authorization to build.** Every finding above is a research
input; no runtime code, manifest, service worker, or route change should be
made on the basis of this document alone until the architecture owner has
reviewed and ratified a scope for E21, including whether any option beyond
the PWA path requires first superseding ADR-010.
