# Current-state map (Phase A1/A2 audit)

Scope: this document answers, with real `file:line` references on branch
`docs/current-state-audit` (tip at the time of writing: `01c9a1a`), the
inventory the deferred BMAD/SDLC spec's Phase A1 asked for (see
`docs/red-team-side-story/spec/08_BMAD_FULL_SDLC_IMPLEMENTATION.md` §A1 on
the `docs/red-team-side-story-spec-deferred` branch — read for the template
shape only, not adopted here), plus the §A2 gap-map template applied per
stage. It is pure documentation: no capability described below was
invented for this doc, and no code logic was changed to produce it.

Reading lens (per this task's brief, not written into any code comment):
the project's first real user is a corporate L&D "academy-as-a-service"
launch, run by the project owner alongside two other real GTM engagements.
So each stage below also notes, in one line, how close it is to being
usable end-to-end for a first real customer onboarding, vs. still
scaffolding for a demand pattern that has not been exercised for real yet.

---

## 1. Demand / enterprise-profile intake — `app/demand.py`

- **Current input**: per-study YAML artifacts under `studies/<id>/` —
  `05_enterprise_demand_profile.yaml` (evidence claims, capability gaps,
  confidence) and `05b_use_case_inventory.yaml` — plus the ICB taxonomy
  (`data/taxonomies/icb_v5_2026.yaml`) and the private network JSONL
  (`data/private/network/companies.jsonl`,
  `company_icb_mappings.jsonl`). Read via `DemandCatalog._latest_studies`
  (`app/demand.py:84-122`) and `DemandCatalog.snapshot`
  (`app/demand.py:124-201`).
- **Current output**: a sector rollup snapshot (`sectors[]` with
  `benchmark_state`, `eligible_study_count`, `companies[]`) and a flat
  `inventories()` list of use-case inventories (`app/demand.py:203-221`).
  "Eligible" for benchmarking = current (not stale, `app/demand.py:98-99`)
  **and** complete (evidence claims + capability gaps + medium/high
  confidence, `app/demand.py:102`).
- **UI surface**: `GET /api/demand` and `GET /api/demand/inventories`
  (`app/server.py:192-198`) render into `renderDemand()`
  (`app/frontend/app.js:200-293`) — read-only sector/company/use-case
  browsing, no intake form exists in the frontend to create or edit a
  demand profile; profiles are produced offline (by a skill run, not
  through this web app).
- **Gap map**:
  - missing Issue support: yes — no way to flag "this evidence claim is
    contested" against a specific claim; disagreement about a capability
    gap has nowhere to live except outside the tool.
  - missing SideStory support: yes — no narrative composition layer over
    demand evidence for outreach/pitch use (the deferred spec's Issue → SideStory
    pipeline does not exist here in any form).
  - missing red-team: yes — nothing bounded-falsifies a demand profile's
    "complete" classification before it is used downstream.
  - missing linter: yes — no lint step catches things like the well-known
    `# TODO(red-team-spec)` flagged case below (silent staleness at 180
    days regardless of segment).
  - missing outcome-capture: yes — no field records whether a demand
    profile's capability gaps were later validated true or false against
    what fit/reach actually found.
  - **First-customer read**: the intake pipeline assumes a skill-run
    artifact pipeline (studies/*, product_catalog/*) already exists for a
    company before this stage does anything; there is no lightweight
    "just type in an L&D academy customer's profile" path in the web app.
    This is the single biggest scaffolding-vs-usable gap for a fast first
    onboarding — see MoSCoW doc.

## 2. Fit — `app/qualification.py` (product-fit gate logic)

- **Current input**: `06_product_fit_matrix.yaml` (matches, hard gates,
  decision) read per study in `QualificationCockpit.list_studies()`
  (`app/qualification.py:92-224`), reconciled against the demand profile
  and product snapshots.
- **Current output**: a `fit_violation` string when the top-level decision
  cannot be reconciled with the selected match or an unresolved
  blocker/critical gate (`_fit_violation`, `app/qualification.py:45-63`),
  plus the `stage`/`decision`/`current_blocker`/`steps[]` shape consumed
  everywhere else (dashboard, reach, kanban, account 360).
- **UI surface**: `GET /api/qualification` → `renderQualification()`
  (`app/frontend/app.js:369-411`) shows stage badges and the step
  pipeline with blocker CTAs; `POST /api/qualification/actions`
  (`app/server.py:421-459`, wired at `app/frontend/app.js:106`) lets a
  human record `cancel` / `step_back` / `force` against a blocker —
  this is the one qualification action that is genuinely writable from
  the UI today (it appends to `BlockerActionLog`,
  `app/blocker_actions.py:37-81`; it does not itself change the fit
  matrix file).
- **Gap map**:
  - missing Issue support: yes — `_fit_violation` is a single derived
    string, not a structured, trackable "counter-perspective" that a
    human could dispute item-by-item and have it show up cross-study.
  - missing SideStory support: yes — no way to compose the fit decision
    into an outreach-ready narrative; that composition currently happens
    only via the offline `engagement-pilot-design` skill referenced in
    `pilot_blocker` (`app/qualification.py:180-186`).
  - missing red-team: partial — the hard-gate reconciliation
    (`_fit_violation`) is itself a lightweight, deterministic
    falsification check (decision must match a real PASS'd gate), but it
    is baked into normal control flow, not a separate bounded
    red-team pass with a repair/verify loop.
  - missing linter: yes — nothing catches a fit matrix that is
    syntactically valid but semantically degenerate (e.g. exactly one
    match with `decision` copied from the top level, `_selected_match`
    fallback at `app/qualification.py:43`).
  - missing outcome-capture: yes — a `pursue`/`validate` decision is
    never later checked against what actually happened (won/lost/
    stalled); there is no false-positive tracking for fit at all.
  - **First-customer read**: this stage is close to end-to-end usable —
    the blocker/CTA/action-log loop already gives a human a real,
    trackable way to push a study through fit. The gap is entirely
    upstream (getting a demand profile and product snapshot in) and
    downstream (turning `pursue` into an actual outreach action, see
    §3-4).

## 3. Target/person qualification and reach — `app/reach.py`, `app/network_writer.py`, `app/network_index.py`

- **Current input**: `06b_contact_targets.yaml` (per-study contact
  targets with `role_hypotheses`, `persona_matches`, `target_score`,
  `current_role_status`), the selected fit match, and (for role/company
  creation) the private network JSONL layer.
- **Current output**: `ReachMatchmaker.preview()`
  (`app/reach.py:102-249`) computes `stakeholder_roles` (promoter /
  terrain_user / technical_sponsor / veto_control / prescriber,
  `app/reach.py:46-62`), a `wave` (`first` / `second` /
  `validation_only`, `app/reach.py:72-80`), and a `blockers[]` list
  (missing role coverage, unresolved fit gates, unvalidated current-role
  status). `ReachMatchmaker.list_ready()` (`app/reach.py:82-100`) gives a
  flat per-study readiness view for kanban/dashboard/account-360.
- **UI surface**: `GET /api/reach` (list) and `POST /api/reach/preview` /
  `POST /api/reach/prepare` wired at `app/frontend/app.js:394-406`
  (`renderReach`-style flow around line 369+) — the preview is read-only
  (stakeholder table + blockers), and "prepare" only produces a *skill
  invocation request* (`prepare_request`, `app/reach.py:251-282`) — it
  does not itself write `06c_reach_strategy.yaml`; that still requires an
  offline skill run. Person/company creation is separately exposed via
  `POST /api/network/people` / `POST /api/network/companies`
  (`app/frontend/app.js:757, 799, 814`) → `create_person`/`create_company`
  (`app/network_writer.py:84-223`), the only genuinely-writable path in
  this stage.
- **Gap map**:
  - missing Issue support: yes — role-coverage blockers
    (`app/reach.py:196-211`) are generated fresh each `preview()` call and
    not persisted/trackable as a standing issue a human can annotate or
    dismiss with a reason.
  - missing SideStory support: yes — `why_now`/`why_person` are single
    strings assembled ad hoc (`app/reach.py:133, 158-162, 183`), not a
    reusable side-story object referenced from outreach.
  - missing red-team: yes — nothing verifies a `current_role_status`
    claim beyond the human-review gate already built in
    (`role_blocker`, `app/reach.py:164-175`); that gate is a genuine
    control, but it is not a red-team pass, it is a hard precondition.
  - missing linter: yes — no lint over `06b_contact_targets.yaml` shape
    beyond what `preview()` happens to touch at read time.
  - missing outcome-capture: yes — a stakeholder marked `ready`/`first
    wave` is never later reconciled with whether outreach to that person
    actually happened or worked.
  - **Known operational gap, not spec-related** (documented already in
    `app/network_writer.py:24-31`): creating a person/company via the API
    does not rebuild `network_index.sqlite`, so it will not appear in
    `/api/network/people` search until an admin calls
    `POST /admin/network/rebuild-index`. This is a real UX trap for a
    first-customer onboarding session done live.
  - **First-customer read**: the read-side (stakeholder roles, waves,
    blockers) is genuinely useful today. The write-side stops at
    "prepare a skill request" — there is no in-app way to actually build
    `06c_reach_strategy.yaml`, which means a first customer's reach plan
    still depends on someone running an external skill by hand.

## 4. Engagement hypothesis / nudging — `app/nudging.py`

- **Current input**: `05b_use_case_inventory.yaml` only —
  `UseCaseNudger.generate()` explicitly rejects any payload carrying ICB,
  sector, product-fit, or offer context (`_FORBIDDEN_REQUEST_FIELDS`,
  `app/nudging.py:12-20`, enforced in `generate_request`,
  `app/nudging.py:204-212`), by design (input-boundary isolation).
- **Current output**: `nudges[]` in three modes — `productivization`
  (`app/nudging.py:69-99`), `upsell_dependency`
  (`app/nudging.py:101-134`), `cross_sell_package`
  (`app/nudging.py:136-173`) — each a `status: "hypothesis"` object with
  `rationale`, `evidence_feedback`, `falsifier`, `confidence`. Nothing is
  persisted; `generate()` recomputes on every call.
- **UI surface**: `GET /api/nudging/inventories` + `POST
  /api/nudging/generate` wired at `app/frontend/app.js:423` inside
  `renderNudgeInventory()` (`app/frontend/app.js:412-427`) — purely
  read/display; a nudge cannot be accepted, rejected, or tracked from the
  UI. `POST /api/campaigns/cross-sell`
  (`app/campaigns.py:138-158`, UI at `app/frontend/app.js:673`) is the
  only place a nudge (specifically `cross_sell_package`) is turned into a
  persisted record — but that record is just an audit event
  (`kind: "cross_sell_prep"`), not a decision on the nudge itself.
- **Gap map**:
  - missing Issue support: yes — nothing captures "this nudge's
    rationale is wrong" as trackable feedback distinct from
    `evidence_feedback` (which is upstream use-case feedback, not
    feedback on the nudge itself).
  - missing SideStory support: yes — `rationale` is the closest thing to
    a story today, and it is a single templated sentence
    (`app/nudging.py:90, 125, 164`), not a composed narrative.
  - missing red-team: yes — a nudge's `falsifier` field
    (`app/nudging.py:94, 129, 168`) states what *would* falsify it, but
    nothing runs that check; it's documentation of intent, not an
    executed test.
  - missing linter: yes.
  - missing outcome-capture: yes — this is the module with the widest
    input/output/outcome gap of all six stages: `status: "hypothesis"`
    never transitions to `accepted`/`rejected`/`shipped` anywhere in the
    codebase (checked: no other module reads or writes a nudge's
    `status` field or `nudge_id` after generation).
  - **First-customer read**: this is scaffolding, not a first-customer
    blocker — nudging is an expansion/upsell mechanism that only matters
    *after* a first study has real use-case history; it is reasonable to
    leave as read-only hypothesis display for the first onboarding.

## 5. Follow-up / stale-state tracking — `app/dashboard.py` (`FollowUpDashboard`)

- **Current input**: re-derives from `QualificationCockpit.list_studies()`,
  `ValueChainCatalog.list_studies()`, `DemandCatalog.snapshot()`, and
  `RepoControlPlane.backlog()` — `FollowUpDashboard.items()`
  (`app/dashboard.py:26-137`) never stores its own state; it recomputes a
  flat priority list (`P0`/`P1`/`P2`) each call.
- **Current output**: a sorted list of `{id, priority, kind, label, state,
  message, resolver, navigation}` items — one per current qualification
  blocker, pending value-chain analysis, sector benchmark-edge/-ready
  state, and open repo-level TODO.
- **UI surface**: `GET /api/follow-up` → `renderFollowUp()`
  (`app/frontend/app.js:428-439`) — read-only list with a "navigate to
  the source tab" click; there is no snooze, no assignment, no
  "mark handled" action distinct from actually resolving the underlying
  blocker via `/api/qualification/actions`.
- **Gap map**:
  - missing Issue support: yes — each dashboard row is a transient
    projection, not a persisted, ownable issue with its own lifecycle.
  - missing SideStory support: n/a — this stage is about
    stale-state/priority, not narrative.
  - missing red-team: n/a — nothing here decides truth, it reflects
    other modules' truth.
  - missing linter: yes — nothing validates that the dashboard's
    priority ordering (P0/P1/P2 string sort, `app/dashboard.py:137`)
    stays meaningful as more sources are added (a lexical sort of `P0` <
    `P1` < `P2` < `P9` happens to work only because of that exact
    naming).
  - missing outcome-capture: yes — no record of when a follow-up item
    first appeared vs. when it was cleared, so "stale volume" (how many
    follow-ups pile up per week) cannot currently be measured — directly
    relevant to the "revisit once follow-up volume exceeds N/week" gate
    named in this task's brief; see inline TODO.
  - **First-customer read**: this is a genuinely useful single-pane
    "what's blocking me right now" view and is close to end-to-end usable
    as-is for a first onboarding, precisely because it is a read-side
    aggregation of other stages rather than new state to maintain.

## 6. Blockers/unknowns storage — `app/blockers.py`, `app/blocker_actions.py`, blocker construction in `app/qualification.py`/`app/reach.py`/`app/dashboard.py`

- **Current input**: none of its own — `blocker()` (`app/blockers.py:12-42`)
  is a pure constructor called by every other stage to shape a
  standardized blocker dict (deterministic `blocker_id` via
  `sha256(category, key)`, `app/blockers.py:7-9`).
- **Current output**: the blocker dict itself (`category`, `severity`,
  `message`, `required_state`, `owner_skill`/`human_action`, `cta_*`,
  `postcondition`) — never persisted on its own. `BlockerActionLog`
  (`app/blocker_actions.py:20-97`) is the one piece of real persisted
  state in this area: an append-only JSONL of human actions
  (`cancel`/`step_back`/`force`) against a known qualification step,
  written to `studies/<id>/06d_blocker_actions.jsonl`
  (`app/blocker_actions.py:33-35`).
- **UI surface**: blockers render inline wherever they're attached
  (qualification steps, reach preview, dashboard rows); the action log
  itself is only surfaced indirectly through Account 360's
  `recent_actions` (`app/account_view.py:69-70`, rendered at
  `app/frontend/app.js:611`) and is not independently browsable/filterable.
- **Gap map**:
  - missing Issue support: this **is** the closest thing to an Issue
    registry already in the codebase (structured, categorized, with an
    owner and a postcondition) — but it is regenerated fresh on every
    read, not a durable registry a human can browse, dedupe, or dismiss
    with a reason outside the six fixed qualification steps
    `BlockerActionLog` knows about (`STEP_ORDER`,
    `app/blocker_actions.py:15`). Unknowns/blockers on reach role
    coverage or nudging rationale, for example, have no equivalent
    action log at all.
  - missing SideStory support: n/a.
  - missing red-team: n/a — blockers are the *result* of existing checks
    (hard gates, stale-role gates), not themselves red-teamed.
  - missing linter: partial — `blocker()` itself enforces one invariant
    (`owner_skill` or `human_action` required, `app/blockers.py:27-28`)
    but nothing lints for orphaned/duplicate blocker keys across a
    study's history.
  - missing outcome-capture: yes — a `force` action requires a mandatory
    reason (`app/blocker_actions.py:60-61`) which is good discipline, but
    nothing later checks whether forcing past that blocker turned out to
    be right.
  - **First-customer read**: `BlockerActionLog` is real, tested,
    genuinely writable state — one of the most production-ready pieces
    in the whole audit. Its scope is narrow (six qualification steps
    only), which is fine for a first customer's single pipeline.

## 7. Kanban / campaigns / account-360 (recent CRM sprint) — `app/kanban.py`, `app/campaigns.py`, `app/account_view.py`

- **`app/kanban.py`** (`build_board`, `app/kanban.py:74-149`): pure
  read-side re-shaping of qualification/reach/nudging/follow-up into one
  board with `CANONICAL_STAGES` (`app/kanban.py:51-61`). Its own
  docstring (`app/kanban.py:13-35`) documents that the three source
  modules use genuinely incompatible stage vocabularies that this module
  reconciles by convention, not by a shared contract — this is itself the
  kind of ADR-002-style "ports" gap the deferred spec's Epic 1 targets,
  named here as a real, already-self-documented seam rather than a new
  finding.
- **`app/campaigns.py`**: `launch_prospecting_campaign`
  (`app/campaigns.py:112-135`) persists a campaign record from a network
  search (people or companies) — genuinely writable, real state in
  `data/private/network/campaigns.jsonl`. `prepare_cross_sell`
  (`app/campaigns.py:138-158`) is documented (module docstring,
  `app/campaigns.py:1-24`) as recording that a cross-sell prep
  *happened*, not tracking the nudge's own lifecycle (same outcome-gap
  as §4).
  - Frontend: `loadCampaigns()` (`app/frontend/app.js:648-664`, list-only)
    and campaign creation forms wired at `app/frontend/app.js:666, 673`
    — a campaign, once launched, has no further action surface (no
    status transition beyond the initial `"draft"`
    `app/campaigns.py:132`, despite the module docstring noting a
    campaign "can also change over time" — nothing currently changes it).
- **`app/account_view.py`**: `get_account_360`
  (`app/account_view.py:38-86`) is a pure read-side aggregation (company +
  people + qualification + reach + recent blocker actions), returns
  `None` for an unknown company rather than raising (documented design
  choice, `app/account_view.py:16-25`). No write path of its own.
- **UI surface**: `GET /api/kanban/board` → `loadKanban()`
  (`app/frontend/app.js:459-491`); `GET/POST /api/campaigns*` → §above;
  `GET /api/accounts/{id}/360` → `openAccount360()`
  (`app/frontend/app.js:602-622`), including the one write action in this
  group, admin-only workspace reassignment
  (`POST /admin/network/companies/{id}/reassign`).
- **Gap map** (for the group):
  - missing Issue support: yes, throughout.
  - missing SideStory support: yes — Account 360 in particular is the
    natural place a composed customer narrative would eventually live,
    and today has none.
  - missing red-team: n/a — these are aggregation/orchestration modules.
  - missing linter: yes — the kanban stage-alias reconciliation
    (`_QUALIFICATION_STAGE_ALIASES`, `app/kanban.py:66`) is exactly the
    kind of thing a contract linter would catch if a new stage value were
    introduced upstream without updating this map.
  - missing outcome-capture: yes — a campaign's `target_count` is
    recorded at launch time but never checked against how many of those
    targets converted to anything.
  - **First-customer read**: Account 360 + campaigns are the most
    "CRM-shaped" parts of the app and read as closest to what a first
    customer's GTM operator would actually want to open daily. Kanban is
    a nice-to-have consolidated view of state that already exists
    elsewhere; it adds visibility, not new capability.

---

## Summary table

| Stage | File(s) | Writable from UI today? | Biggest gap for first-customer usability |
|---|---|---|---|
| Demand intake | `app/demand.py` | No (read-only) | No in-app intake form; depends on offline skill artifacts |
| Fit | `app/qualification.py` | Partially (blocker actions only) | Fit matrix itself only produced offline |
| Reach | `app/reach.py`, `app/network_writer.py` | Partially (person/company create; reach "prepare" only requests a skill run) | No in-app way to actually build `06c_reach_strategy.yaml`; index-rebuild UX trap |
| Nudging | `app/nudging.py` | No | No accept/reject lifecycle for a nudge |
| Follow-up | `app/dashboard.py` | No (navigates elsewhere) | No stale-volume metric to justify a heavier follow-up system |
| Blockers | `app/blockers.py`, `app/blocker_actions.py` | Yes (cancel/step_back/force) | Scope limited to the six qualification steps |
| Kanban/Campaigns/Account 360 | `app/kanban.py`, `app/campaigns.py`, `app/account_view.py` | Partially (campaign launch; admin reassign) | Campaign status never advances past "draft" |
