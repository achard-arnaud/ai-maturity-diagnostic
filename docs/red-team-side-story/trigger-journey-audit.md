# Trigger provenance & journey completeness audit

Scope: deep pass on `docs/red-team-side-story/moscow-next-sprints.md`'s M1-M3 /
S1-S4 / C1-C3, answering four questions per item: (1) what triggers it today,
concretely; (2) does a human have a logical manual trigger; (3) does that
trigger sit in a coherent journey; (4) is the journey E2E-tested. All citations
are `file:line` against this branch's tip (`34e8d65`). Where something could
not be found, this doc says "not found" rather than assuming.

---

## Cross-cutting taxonomy: every frontend button/form/CTA in `app/frontend/app.js`

Classification key:
- **A. Full-process trigger** — starts a whole multi-step agent workflow (a
  `openInvoke(...)` call against a named skill, or `openWorkflow(...)` which
  opens the guided multi-step drawer backed by `POST /api/workflows/plan`).
- **B. Single-step trigger** — one bounded backend mutation with an immediate
  synchronous result (a plain `POST`/`PATCH` to a REST endpoint, no skill
  involved).
- **C. Read/navigation only** — fetches/displays data, or navigates between
  panels; no mutation.

| Element (selector / event listener) | Line(s) | Class | What it does |
|---|---|---|---|
| `.invokeBtn` (skill grid "Appel unitaire") | `app.js:165` | A | `openInvoke(skillId)` — opens the freeform skill-invoke drawer for any catalog skill |
| `.offerAuditBtn` | `app.js:176` | A | `openInvoke("product-icp-intelligence", ...)` |
| `.offerFlowBtn` | `app.js:177` | A | `openWorkflow("offer", ...)` — full guided flow |
| `.offerOppBtn` | `app.js:178` | C | `openOfferOpportunities` — read-only cross-reference into qualification |
| `.offerEditBtn` | `app.js:179` | B | opens `offerEditForm`; submit does `PATCH /api/catalog/offers/{id}` (`app.js:560`) |
| `.sectorDetailBtn` / `.sectorHeritageBtn` | `app.js:211-212` | C | open detail/heritage read panels |
| `.sectorPrimaryBtn` (`runSectorPrimary`) | `app.js:213, 217-227` | A | `openInvoke("sector-intelligence-consolidation" \| "network-contact-intake", ...)` |
| `.sectorFlowBtn` | `app.js:214` | A | `openWorkflow("demand", ...)` |
| `#detailPrimary` / `#detailBenchmark` | `app.js:250-251` | A | same as sectorPrimaryBtn |
| `#detailHeritage` / `#detailHarvest` | `app.js:252, 254-258` | A/C | heritage read, or `openInvoke("enterprise-use-case-intelligence", ...)` |
| `#detailFlow` | `app.js:253` | A | `openWorkflow("demand", ...)` |
| `.useFlowBtn` | `app.js:259` | A | `openInvoke("enterprise-use-case-intelligence", ...)` |
| `.companyOrgBtn` | `app.js:260` | A | `openInvoke("tech-leadership-org-intelligence", ...)` |
| `.companyHeritageBtn` / `.ucGraphBtn` | `app.js:261` | C | read graph panels |
| `.companyFlowBtn` | `app.js:262` | A | `openWorkflow("company", ...)` |
| `.companyQualBtn` | `app.js:263` | C | `jumpToQualification` — tab navigation |
| `.valueChainBtn` | `app.js:264` | C | opens value-chain analysis (may trigger `#refreshValueChain` A-action inside) |
| `#refreshValueChain` | `app.js:283-286` | A | `POST /api/value-chain/prepare` then `openInvoke(...)` |
| `#validateAdjacent` | `app.js:287` | A | `openInvoke("enterprise-use-case-intelligence", ...)` |
| `#valueChainFlow` | `app.js:288` | A | `openWorkflow("value_chain", ...)` |
| resolver buttons (`.resolverBtn`, `bindResolverButtons`) | `app.js:67-82` | A or C | if `resolver.owner_skill` set, opens skill-invoke (A); else opens a **read-only** "human action" info panel (C) — see note below |
| `.blockerActionBtn` (cancel/step_back/force) | `app.js:84-91, 111-118` | B | `POST /api/qualification/actions` |
| `.workflowSkillBtn` ("Préparer" inside a workflow step) | `app.js:143, 148-151` | A | `openInvoke(step.skill, ...)` |
| `.jumpQualification` | `app.js:189` | C | tab navigation |
| `.reachBtn` | `app.js:387, 392` | C | `POST /api/reach/preview` (read) opened in a data panel |
| `#prepareReach` | `app.js:401-404` | A | `POST /api/reach/prepare` (returns a skill-invocation *request*, not a write) then `openInvoke(...)` |
| `#reachFlow` | `app.js:405` | A | `openWorkflow("reach", ...)` |
| `.crossSellBtn` (`launchCrossSell`) | `app.js:388, 671-677` | B | `POST /api/campaigns/cross-sell` — real, synchronous, persisted write |
| `.qualFlowBtn` | `app.js:389` | A | `openWorkflow("qualification", ...)` |
| `.nudgeBtn` (productivization/upsell/cross-sell generate) | `app.js:417-425, 781` | C | `POST /api/nudging/generate` — pure computation, nothing persisted |
| `#fullNudgeFlow` | `app.js:782` | A | `openWorkflow("nudging", ...)` |
| `#nudgeGraph` / `#ucGraphBtn` (nudging tab) | `app.js:783-784` | C | read graph panels |
| `#nudgeSkillCall` | `app.js:785` | A | `openInvoke("use-case-nudging", ...)` |
| `.followNavBtn` | `app.js:433-437` | C | tab navigation (or `jumpToQualification`) |
| resolver buttons inside follow-up cards | `app.js:432` | A/C | same as above |
| `#catalogSearchBtn` / Enter in `#catalogSearchQuery` | `app.js:787-788` | C | `GET /api/catalog/search` |
| `.viewCatalogResult` | `app.js:484` | C | `openOfferOpportunities` |
| `#candidatesFilterForm` submit | `app.js:779` | C | `loadCandidates()` — filtered `GET` |
| `.viewCandidateBtn` | `app.js:506, 510-527` | C | `GET /api/catalog/candidates/{id}` detail panel |
| `.promoteCandidateBtn` (`promoteCandidate`) | `app.js:505, 529-538` | B | `POST /api/catalog/candidates/{id}/promote` |
| `#offerEditForm` submit | `app.js:549-565` | B | `PATCH /api/catalog/offers/{id}` |
| `#peopleSearchForm` submit | `app.js:790` | C | `GET /api/network/people` |
| `#companiesSearchForm` submit | `app.js:791` | C | `GET /api/network/companies` |
| `.open360Btn` | `app.js:599` | C | `GET /api/accounts/{id}/360` |
| `#reassignBtn` (inside Account 360, admin-only) | `app.js:618-626` | B | `POST /admin/network/companies/{id}/reassign` |
| `#loadDuplicatesBtn` | `app.js:823` | C | `GET /api/network/duplicates` (read-only; no dismiss action wired) |
| `#globalAddContact` | `app.js:732` | A | `openInvoke("network-contact-intake", ...)` — freeform prompt |
| `#createContactDirect` | `app.js:750-760` | B | `POST /api/network/people` (structured mini-form inside invoke drawer) |
| `#createPersonForm` submit | `app.js:794-807` | B | `POST /api/network/people` (Réseau tab structured form) |
| `#createCompanyForm` submit | `app.js:809-821` | B | `POST /api/network/companies` |
| `#discoverForm` submit | `app.js:762-768` | B | `POST /api/catalog/discover` |
| `#harvestForm` submit | `app.js:770-777` | B | `POST /api/catalog/harvest` |
| `#prospectingForm` submit (`launchProspectingCampaign`) | `app.js:825, 657-669` | B | `POST /api/campaigns/prospecting` |
| kanban board render (`loadKanban`) | `app.js:459-472` | C | `GET /api/kanban/board`, no per-card action wired |
| `#runSkill` (invoke drawer's actual "run") | `app.js:736-748` | A | `POST /api/skills/{id}/invoke` — executes the skill (or no-ops if executor not configured) |
| nav tab buttons | `app.js:729` | C | `showPanel` |

**Counts** (representative, not exhaustive to the very last handler): **A ≈ 26**
full-process/skill triggers, **B ≈ 13** single-step bounded backend actions,
**C ≈ 20** read/navigation-only elements. The single largest category is A —
most of the app's "action" surface routes to `openInvoke`/`openWorkflow`
against an agent skill, not to a bounded synchronous write. The CRM-sprint
additions (`createPersonForm`, `createCompanyForm`, `prospectingForm`,
`crossSellBtn`, `promoteCandidate`, `offerEditForm`, `blockerActionBtn`,
`reassignBtn`) are the app's only true "B" cluster, and they are all recent
(per the current-state map, "the CRM-sprint style additions").

One structural note on resolver buttons: `bindResolverButtons` (`app.js:67-82`)
is the single dispatcher behind most blocker/nudge/follow-up "resolve" CTAs
across the app. It branches on `resolver.owner_skill`: if present, it opens
the skill-invoke drawer (category A); if absent (i.e. `human_action` only,
per `app/blockers.py:27-28`'s either/or contract), it opens a **read-only**
info panel describing the required state and postcondition, with **no
button to actually perform the human action** — the human has to go do it
outside the app entirely. This is a specific, systemic gap that recurs across
several MoSCoW items below.

---

## M1 — network-index rebuild visibility after person/company creation

**Gap cited**: `app/network_writer.py:24-31`.

1. **What triggers it today**: nothing in the frontend. The only "trigger" is
   the documented manual admin call `POST /admin/network/rebuild-index`
   (`app/server.py:280-283`), which has no button anywhere in `app/frontend/app.js`
   or `app/frontend/index.html`. `create_person`/`create_company` themselves are
   triggered by `#createPersonForm`/`#createCompanyForm` submit (`app.js:794-821`)
   and `#createContactDirect` (`app.js:750-760`), which call `POST
   /api/network/people` / `/companies` — but none of those handlers calls the
   rebuild endpoint afterward, nor shows a "stale index" banner.
2. **Does a human have a logical manual trigger**: **No** for the rebuild step
   itself. The creation forms exist and work (B-class), but the necessary
   follow-up (index rebuild) has no UI element at all — only an admin curling
   `POST /admin/network/rebuild-index` or running
   `scripts/rebuild_network_index.py` could do it.
3. **Journey coherence**: N/A — there is no button to reach. A human who just
   created a contact via `#createPersonForm` and then searches for them via
   `#peopleSearchForm` (`app.js:790, 572-586`) will get an empty/stale result
   with no explanation and no in-app remedy. This is exactly the "UX trap"
   the current-state map already names.
4. **E2E coverage**: not mentioned in any of `tests/e2e/journey-*.spec.ts` —
   none of the three specs asserts on index staleness or a rebuild banner.
   `journey-b-contact.spec.ts` and `journey-c-company.spec.ts` GAP-flag
   *other* contact/company gaps (structured form, detail page, kanban) but
   never this one.

**Classification for synthesis**: cheap wiring gap. `POST
/admin/network/rebuild-index` already exists and works; this needs (a) the
create-person/create-company handlers to call it (or a "index stale, click to
rebuild" banner wired to it) — no new backend logic required, purely a
missing button/call.

---

## M2 — demand-profile intake form

**Gap cited**: `app/demand.py` has no write path (whole file).

1. **What triggers it today**: nothing. `DemandCatalog` (`app/demand.py`) is
   confirmed read-only end to end — `snapshot()` (`app/demand.py:124-201`) and
   `inventories()` (`app/demand.py:203-221`) only read
   `05_enterprise_demand_profile.yaml` (`app/demand.py:103`) and related YAML;
   grepping the whole module for `write`/`POST`/`save` finds nothing. The only
   "trigger" for a demand profile to come into existence is an agent running
   the (unnamed-in-code, referenced in current-state-map) offline skill
   pipeline against `studies/<id>/05_enterprise_demand_profile.yaml` — there is
   no `blocker.owner_skill` in this codebase that names a specific skill for
   *creating* a demand profile from scratch (the closest is
   `runSectorPrimary`'s `network-contact-intake`/`sector-intelligence-consolidation`
   invokes at `app.js:217-227`, which add a company/contact candidate, not a
   demand profile).
2. **Does a human have a logical manual trigger**: **No.** `GET /api/demand`
   and `GET /api/demand/inventories` (`app/server.py:192-198`) render into
   `renderDemand()` (`app.js:200-293`) — a read-only sector/company/use-case
   browser. There is no form anywhere in `index.html`/`app.js` to type in a
   company name, evidence claims, capability gaps, or confidence.
3. **Journey coherence**: N/A — no button exists.
4. **E2E coverage**: not mentioned. None of the three E2E specs GAP-flags a
   missing demand-intake form specifically (they cover product/contact/company
   journeys, not the demand-profile-creation journey at all).

**Classification for synthesis**: real work, not just wiring. `app/demand.py`
has zero write functions to call — a form would need a new backend write path
(a `create_demand_profile`-equivalent function plus a route), not merely a
button pointed at an existing function.

---

## M3 — reach "prepare" should write the strategy artifact

**Gap cited**: `app/reach.py:251-282` (specifically `prepare_request`,
`app/reach.py:261-291`, and the inline `# TODO(red-team-spec)` at
`app/reach.py:256-260`).

1. **What triggers it today**: `#prepareReach` (`app.js:398, 401-404`), inside
   the reach data panel opened by `.reachBtn` (`app.js:387, 392-410`). Clicking
   it calls `POST /api/reach/prepare` → `ReachMatchmaker.prepare_request`
   (`app/reach.py:261-291`), which **only builds a skill-invocation request**
   (`schema_version`, `status: "prepared"`, `skill:
   "iterative-reach-matchmaking"`, `input`, `context_paths`,
   `expected_artifact"`) and returns it to `openInvoke(prepared.skill,
   prepared.input, ...)` (`app.js:403`) — i.e. the button's real effect is to
   open the skill-invoke drawer for an agent to run, not to write
   `06c_reach_strategy.yaml` itself.
2. **Does a human have a logical manual trigger**: **Partial.** The button
   exists and is reachable, but its actual effect is "hand this off to an
   agent skill," not "produce the artifact yourself." A human clicking it gets
   the invoke drawer pre-filled with the skill name/input — from there, unless
   `AI_DIAGNOSTIC_SKILL_EXECUTOR` is configured server-side (`app.js:37-40`,
   `#executorBanner`), nothing is actually written; `#runSkill`
   (`app.js:736-748`) would need to be clicked too, and even then execution
   depends on the executor being wired up externally.
3. **Journey coherence**: **Yes, reachable** — Qualification tab →
   `.reachBtn` (only shown when `row.decision === "pursue" || "validate"`,
   `app.js:381`) → reach data panel → `#prepareReach`. This is a natural next
   step from where an operator would be. But it dead-ends at "please go run a
   skill" per the current-state map's own §3 finding
   (`docs/red-team-side-story/current-state-map.md:160-164`), so the visible
   result the human gets is a prompt to invoke an agent, not a usable
   artifact.
4. **E2E coverage**: `tests/e2e/journey-b-contact.spec.ts:90-104` ("Reach flow
   operates on aggregate stakeholder lanes...") covers the read-side
   preview/lanes rendering, but no spec in `tests/e2e/journey-*.spec.ts`
   asserts on `#prepareReach`'s behavior or on `06c_reach_strategy.yaml` being
   written — not mentioned.

**Classification for synthesis**: real work. `prepare_request` would need a
genuinely new writer function (mirroring `network_writer.py`'s pattern) that
turns the already-computed `preview()` stakeholder waves into a minimal
`06c_reach_strategy.yaml` — the button placement is already correct, but the
backend function it calls needs new write logic, not just a route.

---

## S1 — campaign draft→sent transition

**Gap cited**: `app/campaigns.py:132` (now `app/campaigns.py:137`,
`"status": "draft"`, with the `# TODO(red-team-spec)` at
`app/campaigns.py:132-136`).

1. **What triggers it today**: `#prospectingForm` submit → `launchProspectingCampaign`
   (`app.js:825, 657-669`) → `POST /api/campaigns/prospecting` →
   `launch_prospecting_campaign` (`app/campaigns.py:112-140`), which always
   writes `"status": "draft"` and never advances it. `loadCampaigns()`
   (`app.js:648-655`) renders `campaigns.jsonl` records read-only, each shown
   as `<article>...<span class="badge">${c.status}</span></article>`
   (`app.js:653`) — no per-card action of any kind.
2. **Does a human have a logical manual trigger**: **No.** There is no button,
   form, or CTA anywhere that transitions a campaign's status. The gap is
   exactly as MoSCoW states: `campaigns.py` has no second status value and no
   function to set one.
3. **Journey coherence**: N/A — no button exists to click.
4. **E2E coverage**: not mentioned. None of `tests/e2e/journey-*.spec.ts`
   references campaigns at all (`grep` for "campaign" in `tests/e2e/` returns
   nothing).

**Classification for synthesis**: cheap, once a `advance_campaign_status`-style
function is added to `campaigns.py` (this is a very small backend addition —
a status enum plus a setter, following the module's existing
read-modify-atomic-rewrite convention at `app/campaigns.py:14-16`) — then it
is "wire a button" work. As of today neither the backend function nor the
button exists, so it is a small two-sided addition, not a pure wiring task.

---

## S2 — stale-volume counter on follow-up dashboard

**Gap cited**: `app/dashboard.py:26-137` (specifically the `# TODO(red-team-spec)`
at `app/dashboard.py:137-141`).

1. **What triggers it today**: nothing — there is no counter to trigger.
   `FollowUpDashboard.items()` (`app/dashboard.py:26-142`) recomputes a flat
   priority list fresh on every call, with no first-seen/age tracking
   anywhere in the function or the dataclass.
2. **Does a human have a logical manual trigger**: **N/A — this is a passive
   metric, not an action.** The "trigger" concept does not really apply; the
   dashboard is populated automatically by `GET /api/follow-up` →
   `renderFollowUp()` (`app.js:428-438`) every time the Suivi tab loads. What
   is missing is a *derived number* (count of P0/P1 items open > N days), not
   a human-clickable action.
3. **Journey coherence**: the Suivi tab itself is reachable (`data-target="backlog"`
   nav button, `app.js:729`, `index.html:27`) and already renders
   `#followUpGrid` (`app.js:428-431`) — a stale-volume counter would slot in
   next to it with no new navigation needed. So the *display slot* is
   coherent; there is simply no counter computed yet.
4. **E2E coverage**: `tests/e2e/journey-a-product.spec.ts:123-128` ("Suivi tab
   lists follow-up items as a flat list") covers the existing flat list, but
   no assertion anywhere mentions a stale-volume count — not mentioned.

**Classification for synthesis**: real (small) work, not just wiring — there
is no UI element to hook up because the underlying data model has no
first-seen timestamp at all; `dashboard.py` would need new persisted state
(when did each follow-up item first appear) before any counter/button could
exist. This is the one item where the backend gap is a missing *field*, not
a missing *function*.

---

## S3 — filterable BlockerActionLog view

**Gap cited**: `app/blocker_actions.py` (whole file), rendered today only via
Account 360's `recent_actions`.

1. **What triggers it today**: `BlockerActionLog.record(...)`
   (`app/blocker_actions.py:42-86`) is triggered by the qualification blocker
   buttons — `.blockerActionBtn` (`app.js:84-91`, bound at `app.js:111-118`,
   `recordBlockerAction` at `app.js:93-107`) → `POST
   /api/qualification/actions`. Reading it back happens only through
   `app/account_view.py:69-70`'s `recent_actions` field, rendered at
   `app.js:613, 616` inside `openAccount360` — a small, unfilterable list
   embedded in the Account 360 overlay panel, not a dedicated browse view.
2. **Does a human have a logical manual trigger**: **Partial.** *Writing* to
   the log has a real, working manual trigger (the blocker action buttons).
   *Browsing/filtering* it does not: there is no search box, no date/step/action
   filter, and no standalone panel — a human can only see a company's recent
   actions by opening that company's Account 360 first, and even then it is
   an unfiltered tail, not a filterable list (`app/account_view.py:69-70`
   likely truncates or returns as-is; no filter parameters are accepted by
   `get_account_360`, `app/account_view.py:38-86`, per the current-state map).
3. **Journey coherence**: reachable (Réseau tab → company search →
   `.open360Btn` → Account 360 overlay → "Actions récentes" card,
   `app.js:599, 606-630`), but it is buried inside an otherwise read-only
   aggregation view rather than being its own first-class destination —
   exactly as the MoSCoW item states.
4. **E2E coverage**: not mentioned. No `tests/e2e/journey-*.spec.ts` spec
   opens Account 360 or asserts on `recent_actions`/blocker-action-log
   content at all.

**Classification for synthesis**: cheap — `BlockerActionLog.list_actions`
(`app/blocker_actions.py:88-102`) already exists and is real, tested state;
this needs only a new read endpoint (e.g. a cross-study `GET
/api/blocker-actions?...` wrapping repeated `list_actions` calls plus filter
params) and a UI list/table, no new write logic.

---

## S4 — accept/reject on nudges

**Gap cited**: `app/nudging.py` (`status: "hypothesis"` never transitions,
confirmed via the `# TODO(red-team-spec)` at `app/nudging.py:188-191`).

1. **What triggers it today**: `.nudgeBtn` buttons (`app.js:417-425, 781`) →
   `generateNudges(mode)` → `POST /api/nudging/generate` →
   `UseCaseNudger.generate` (`app/nudging.py:175-206`), which **always**
   returns freshly-generated nudges with `"status": "hypothesis"`
   (`app/nudging.py:97, 132, 171`) and persists nothing (`generate()` "recomputes
   on every call," current-state-map §4). There is no `owner_skill`/blocker
   object attached to an individual nudge at all — nudges are plain data, not
   blocker-shaped, so the `bindResolverButtons` accept/reject-adjacent pattern
   used elsewhere does not even apply here.
2. **Does a human have a logical manual trigger**: **No.** `#nudgeResults`
   (`app.js:420-425`) renders each nudge as a read-only `<article>` with mode,
   rationale, status badge, confidence, and falsifier text — no button of any
   kind is attached to an individual nudge card.
3. **Journey coherence**: N/A — no button exists to click.
4. **E2E coverage**: `tests/e2e/journey-a-product.spec.ts:132-142` ("Nudging
   tab generates cross-sell packages...") covers generation only; no
   assertion anywhere checks for an accept/reject control — not mentioned.

**Classification for synthesis**: real work, not just wiring. Because
`generate()` never persists a nudge (`nudge_id`s are regenerated with a fresh
`uuid.uuid4()` every call, `app/nudging.py:86, 121, 160`), there is nothing
stable to accept/reject against yet — a persistence layer (a nudge-decisions
JSONL, analogous to `campaigns.jsonl`) would need to exist before any
accept/reject button could mean anything durable.

---

## C1 — kanban stage-alias lint

1. **Trigger today**: none — `_QUALIFICATION_STAGE_ALIASES`
   (`app/kanban.py:66`, referenced in the module's own header comment
   `app/kanban.py:1-36`) is a hand-maintained dict with no test or CLI hook.
2. **Manual trigger**: N/A — this is a developer-facing lint/test, not a
   user-facing action; no UI element applies.
3. **Journey coherence**: N/A.
4. **E2E coverage**: not applicable/not mentioned — this is a unit-test-level
   concern, not an E2E journey.

## C2 — surface `nudging.falsifier` more prominently

1. **Trigger today**: `falsifier` is already rendered as plain text inside
   each nudge card — `<small>Falsifier: ${esc(n.falsifier)}</small>`
   (`app.js:424`). So the *display* already exists; what's missing is making
   it a checklist item rather than a trailing caption.
2. **Manual trigger**: **Partial** — the text is visible today (Yes, it
   displays); there is no interactive "I checked this" affordance (No,
   nothing to click).
3. **Journey coherence**: reachable via Nudging tab → generate → nudge card,
   same path as S4.
4. **E2E coverage**: not mentioned specifically (the nudging generation test,
   `journey-a-product.spec.ts:132-142`, doesn't assert on falsifier content).

## C3 — one-click "not a duplicate" dismissal

1. **Trigger today**: `#loadDuplicatesBtn` (`app.js:823`) → `loadDuplicates()`
   (`app.js:635-642`) → `GET /api/network/duplicates`, rendering
   `find_potential_duplicates` (`app/network_index.py:306-364`) results as
   plain cards with no action button (`app.js:640`).
2. **Manual trigger**: **No** for dismissal — the detection/display trigger
   exists and works (Yes for viewing), but there is no button to dismiss a
   pair as "not a duplicate," and no backend function to persist that
   decision either (grep of `network_index.py`/`network_writer.py` for
   "dismiss"/"not_duplicate" finds nothing).
3. **Journey coherence**: reachable (Réseau tab → `#loadDuplicatesBtn`), a
   natural place for the missing button to live.
4. **E2E coverage**: not mentioned in any `tests/e2e/journey-*.spec.ts`.

**Classification for C1-C3**: C1 is a test/lint addition (no UI at all,
correctly out of scope for "trigger journey" analysis). C2 is genuinely
cheap — the display exists, only a checkbox/interaction needs adding. C3 is
cheap on the backend (the read-side is "already fully implemented," per
MoSCoW's own note) but needs a new small write function plus a button.

---

## Synthesis

**Cheap — wire a button to an existing backend function (or a near-trivial
backend addition) that already produces a usable result:**
- **M1** (rebuild-index) — `POST /admin/network/rebuild-index` already
  exists and works; only needs to be called after create, or exposed as a
  banner CTA.
- **S3** (BlockerActionLog view) — `list_actions()` already exists and is
  tested; only needs a new filtered read endpoint + list UI.
- **C2** (falsifier as checklist) — text is already rendered; needs only an
  interaction affordance.
- **C3** (duplicate dismissal) — read side is fully built; needs a small new
  write function plus a button.
- **S1** (campaign draft→sent) is *nearly* this cheap: it needs one small new
  status-setter function in `campaigns.py` (no design work, the module
  already documents intending a lifecycle) plus a button — small but not
  zero backend work.

**More work — the backend function itself doesn't yet produce a UI-usable
result:**
- **M2** (demand intake) — `app/demand.py` has no write path at all; a form
  needs new backend logic before any button matters.
- **M3** (reach prepare → write artifact) — `prepare_request` only builds a
  skill-invocation request; the button placement is already right, but the
  function needs a real writer.
- **S2** (stale-volume counter) — there is no first-seen/age field to compute
  a counter from; this is a data-model gap, not a UI gap.
- **S4** (nudge accept/reject) — nudges are never persisted (fresh UUIDs every
  call), so there is nothing stable to accept/reject against yet; needs a
  persistence layer first.

**Flag: no item found where "this is fundamentally an agent-only step with no
sensible human-manual equivalent" applies to an M/S item itself.** All eight
M/S items describe either (a) a manual UI action that should exist alongside
the agent path, or (b) a backend gap blocking a manual action that is clearly
meant to be human-triggerable (a demand intake form, a reach-artifact writer,
a stale counter, a nudge decision). None of them is a case where a human
manual trigger would be nonsensical.

That said, one **structural** pattern surfaced during this audit that the
MoSCoW list does not currently name, and is worth flagging explicitly: the
`bindResolverButtons` dispatcher (`app.js:67-82`) means that **every** blocker
whose resolution is `human_action`-only (no `owner_skill`) renders as a
**read-only info panel with no actual action button** — the current-role
human-review gate in `app/reach.py:164-175` (`role_blocker`, built via
`human_review_blocker`, `app/blockers.py:93-103`, which always sets
`human_action` and never `owner_skill`) is the clearest example: a human
reading that blocker learns what they must go verify, but has no button in
the app to record "I verified this." This is not itself one of the audited
M/S/C items, but it is the same shape of gap as S4 (a decision with no
recording mechanism) and may be worth a follow-up MoSCoW item if a second
GTM engagement hits it.

Separately, this audit found that the three `tests/e2e/journey-*.spec.ts`
GAP-flagged "shared kanban board" assertions
(`journey-a-product.spec.ts:146-153`, `journey-b-contact.spec.ts:108-114`,
`journey-c-company.spec.ts:135-141`) target `page.getByRole("region", {
name: /Kanban|Pipeline/i })`, and the kanban feature that now exists
(`app/kanban.py`, mounted at `index.html:53, 120, 174` with
`role="region" aria-label="Kanban pipeline"`, and rendered via `loadKanban()`
at `app.js:459-472`) was built *after* those specs were written — the kanban
sections' `aria-label`s match the tests' regex. These three GAP tests are
very likely stale (would now pass) rather than describing a still-real gap;
this is outside the M/S/C scope of this audit but is flagged here since it
affects how "GAP-flagged" should be read for the kanban-related claims in
those three spec files going forward.
