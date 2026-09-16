# MoSCoW — next 2-3 sprints

Grounded in `docs/red-team-side-story/current-state-map.md` (this branch).
Weighted toward what gets the first real customer — the L&D
academy-as-a-service onboarding — usable end-to-end, not toward
architectural completeness. These are small, shippable increments, not
the BMAD spec's epics.

Every Must/Should item cites the specific gap (file:line) it closes.
Every Won't item states why, per the deferred spec's own reasoning
already recorded in `DEFERRED_STATUS.md` (no real E2E cycle run yet to
justify the heavier mechanism).

## Must (blocks a first real customer onboarding end-to-end)

| # | Item | Gap it closes | Why Must |
|---|---|---|---|
| M1 | Fix the network-index rebuild UX trap: auto-trigger (or at minimum surface a visible "index stale, click to rebuild" banner) after `POST /api/network/people` / `/companies` | `app/network_writer.py:24-31` (documented gap: a created record is invisible in search until an admin manually calls `POST /admin/network/rebuild-index`) | A first customer's operator creating contacts live and not seeing them appear is the single most likely "this tool is broken" moment in an onboarding demo. |
| M2 | Add a minimal in-app demand-profile intake form (company name, evidence claims, capability gaps, confidence) that writes `05_enterprise_demand_profile.yaml` directly, bypassing the offline skill pipeline for the common case | `app/demand.py` has no write path at all; `DemandCatalog` is read-only (whole file) | Without this, onboarding the L&D academy account requires someone to hand-author YAML offline before the app does anything useful — that is not "usable end-to-end." |
| M3 | Let reach "prepare" actually write a minimal `06c_reach_strategy.yaml` from the stakeholder waves already computed in `preview()`, instead of only producing a skill-invocation request | `app/reach.py:251-282` (`prepare_request` only prepares a request; nothing writes the artifact) | Reach is the stage right before real outreach; today it dead-ends at "please go run a skill," which breaks the flow for a first customer's operator using only the web app. |

## Should (materially improves the first-customer flow, not blocking)

| # | Item | Gap it closes | Why Should |
|---|---|---|---|
| S1 | Give a campaign a second status transition (e.g. `draft` → `sent`) with a UI action, even without full CRM semantics | `app/campaigns.py:132` (`status: "draft"` never advances anywhere in the codebase, despite the module docstring saying a campaign "can also change over time") | Cheap, and closes the most visible "this looks unfinished" gap in the CRM sprint's own code comments. |
| S2 | Add a lightweight stale-volume counter to the follow-up dashboard (count of `P0`/`P1` items open > N days) | `app/dashboard.py:26-137` has no time-in-state tracking at all | Directly feeds the decision gate this task's own brief names ("revisit once follow-up volume exceeds N/week") — without the counter, nobody can tell when that gate is reached. |
| S3 | Surface `BlockerActionLog` entries as a filterable list (not just buried inside Account 360's `recent_actions`) | `app/blocker_actions.py` is real persisted state with no dedicated browse view | Small UI addition on top of existing, already-tested state; makes the one genuinely production-ready piece of the audit actually visible day to day. |
| S4 | Add an accept/reject action on a generated nudge (persist the decision; no need to change nudge generation logic) | `app/nudging.py` — `status: "hypothesis"` never transitions (confirmed: no other module reads/writes `nudge_id`/`status` after generation) | Cross-sell/upsell hypotheses matter for a second and third GTM engagement (the two other real companies mentioned in this task's context), and this is the cheapest way to start capturing which nudges were actually useful. |

## Could (nice, not needed for the first customer, low cost if picked up incidentally)

| # | Item | Rationale |
|---|---|---|
| C1 | Deterministic lint check for the kanban stage-alias table staying in sync with `QualificationCockpit`'s stage vocabulary | `app/kanban.py:66` already documents the reconciliation by hand; a tiny unit test (not a general linter engine) would catch drift cheaply. |
| C2 | Show `nudging.falsifier` text more prominently in the nudging UI as a manual checklist item (still no automated check) | Costs almost nothing, makes the existing field earn its keep without building any red-team execution. |
| C3 | Expose `find_potential_duplicates` (`app/network_index.py:306-364`) results with a one-click "not a duplicate" dismissal that persists | Already fully implemented read-side; only the dismissal-persistence part is missing, and it is optional for a first customer with a small contact list. |

## Won't (explicitly deferred, with reason)

| # | Item (from the BMAD spec) | Why Won't now |
|---|---|---|
| W1 | Full Issue/CounterPerspective registry (Epic 2 in the deferred spec) | No real E2E cycle has produced a recurring, named disagreement yet to justify a cross-study registry — same reasoning as `DEFERRED_STATUS.md`'s core argument; the audit above finds several ad hoc, per-stage blocker mechanisms already doing a narrower version of this job adequately for one customer. |
| W2 | SideStory composition/storytelling layer (spec §03) | No outreach has happened yet through this tool for a real prospect; composing narratives before a single real pitch has gone out risks designing the wrong shape. |
| W3 | System Red-Team / bounded falsification loopback (spec §01, Epic 5) | The two places closest to "red-teaming a decision" already exist inline (`_fit_violation` in `app/qualification.py:45-63`, the current-role human-review gate in `app/reach.py:164-175`) and are working; a separate red-team subsystem has nothing new to falsify yet. |
| W4 | Dreaming/Loopback learning engine (spec §07) | Explicitly requires real run history/outcomes to learn from; per the audit, outcome-capture is missing at *every* stage (§1-7 of the current-state map), so there is nothing yet for a learning loop to consume. |
| W5 | Deterministic contract linter / Epic 1's ADR-002 "ports" abstraction across qualification/reach/nudging | `app/kanban.py`'s own docstring already documents the vocabulary mismatch by hand and it works; introducing a formal ports/contracts layer now is exactly the "designing a platform ahead of demonstrated need" pattern `DEFERRED_STATUS.md` already named on the storage/Baserow question. |
| W6 | Full campaign lifecycle / CRM stage machine beyond S1's single extra transition | One real customer with modest contact volume does not need a general stage machine yet; S1 buys the visible fix cheaply without committing to the larger design. |

## Cross-cutting note

Several "Should"/"Could" items above line up with the inline
`# TODO(red-team-spec):` comments added in this same change (Step 3) —
each of those comments names a concrete revisit trigger (e.g. "second
workspace onboards," "follow-up volume exceeds N/week") so that revisiting
this MoSCoW list later has a real signal to check against instead of
guessing.
