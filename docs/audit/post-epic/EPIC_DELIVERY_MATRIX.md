# Epic Delivery Matrix — E00 through E13

Method: for every sprint below, three things were actually opened and
cross-checked — (1) the Epic's own spec doc where one exists
(`docs/gtm-transformation/epics/EPIC_0X_*.md` for E00–E10; see the "Spec
authority" note per epic for E11–E13, which don't follow that path), (2) the
sprint's own `docs/governance/sprint-log/E0X-S0Y_STOP.md` (or
`docs/governance/EPIC_13_S0Y_STOP.md` for E13), and (3) the corresponding
`app/*.py` module and `tests/test_*.py` file, confirmed to exist and to be
substantive (not a stub — actual line counts given below; every test module
listed was independently seen in a full `python -m unittest discover`
run that passed 1149/1149 non-skipped tests at 91% `app/` line coverage, run
in this session, not assumed from a sprint log's own claim).

**Sprint counts actually found** (`ls docs/governance/sprint-log/` +
`docs/governance/EPIC_13_S0*_STOP.md`) — several differ from the cadrage
pack's guessed counts: **E00 has only 1 sprint (S01)**, not S01–S05; E06 has
6 (not "S01..S04+"); E09 has 7; E10 has 5; E13 has 5. Total: **79 sprints**.

Classification key: IMPLEMENTED / PARTIAL / DIFFERENT / NOT_IMPLEMENTED /
REGRESSED / UNKNOWN. "Self-scoped deferral" below means the Epic's own
acceptance record names the gap explicitly as deliberately out of that
sprint's stop condition (not a missed promise) — these are classified
IMPLEMENTED against the sprint's own stop condition, with the deferral noted.

---

## E00 — Governance Baseline and Delivery
Spec: `docs/gtm-transformation/epics/EPIC_00_GOVERNANCE_BASELINE_AND_DELIVERY.md`

| Sprint | Objective | Evidence checked | Class. | Notes |
|---|---|---|---|---|
| S01 | Inventory HEAD/branches/PRD/ADR/tests/routes into a machine-readable baseline | `docs/governance/baseline/E00-S01_baseline.yaml` present; `check_release.py` reproduced 0 errors/88% coverage at the time | IMPLEMENTED | Only 1 sprint in this Epic (task brief's "S01..S05" guess is wrong) |

## E01 — Platform Transaction and Execution Foundations
Spec: `docs/gtm-transformation/epics/EPIC_01_PLATFORM_TRANSACTION_AND_EXECUTION_FOUNDATIONS.md`

| Sprint | Objective | Test module (lines) | App module (lines) | Class. |
|---|---|---|---|---|
| S01 | Catalog ownership ADR + contract | `test_catalog_ownership_policy.py` (23) | `catalog.py` (201) | IMPLEMENTED |
| S02 | ArtifactStore atomic/version writes | `test_artifact_store.py` (63) | `artifact_store.py` (239) | IMPLEMENTED |
| S03 | Append-only, hash-chained EventJournal | `test_event_journal.py` (64) | `event_journal.py` (120) | IMPLEMENTED |
| S04 | Durable run/checkpoint/resume state | `test_run_manager.py` (69) | `run_manager.py` (194) | IMPLEMENTED |
| S05 | Budget/quota/cache/retry/degraded mode | `test_execution_policy.py` (57) | `execution_policy.py` (176), `execution_context.py` (26) | IMPLEMENTED |
| S06 | Dry-run/hash/rollback workspace migration | `test_workspace_migrator.py` (69) | `workspace_migrator.py` (159) | IMPLEMENTED |

Known, self-scoped deferrals (not gaps in the sprints above): distributed
locking for `ArtifactStore`; `product_catalog` excluded from migration by
ADR-008 (deliberate).

## E02 — Canonical Account and Network Graph
Spec: `docs/gtm-transformation/epics/EPIC_02_CANONICAL_ACCOUNT_AND_NETWORK_GRAPH.md`

| Sprint | Objective | Test (lines) | App (lines) | Class. |
|---|---|---|---|---|
| S01 | Person/Company/Relationship/ExternalIdentity v1 schemas | `test_network_identity_v1.py` (162) | `network_identity_v1.py` (121) | IMPLEMENTED |
| S02 | Temporal Role/Employment + currentness | `test_network_temporal.py` (69) | `network_temporal.py` (72) | IMPLEMENTED |
| S03 | Identity resolution / dedup proposals, no auto-merge | `test_identity_resolution.py` (136) | `identity_resolution.py` (157) | IMPLEMENTED — but see limitation below |
| S04 | Read models + v1 API (people/companies/relationships) | `test_network_v1_store.py` (77), `test_network_v1_routes.py` (126) | `network_v1_store.py` (127), `network_v1_routes.py` (104) | IMPLEMENTED |
| S05 | Person 360 / Account 360 composed views | `test_person_view.py` (132), `test_account_view.py` (127) | `person_view.py` (76), `account_view.py` (86) | IMPLEMENTED |
| S06 | Legacy network migration/index/reconciliation | `test_network_v1_migrator.py` (173) | `network_v1_migrator.py` (264/writer), `network_index.py` (425) | IMPLEMENTED |

Self-scoped deferral: `identity_resolution`'s merge proposals are proven in
isolation (S03) but not wired end-to-end to `network_index`'s duplicate
detection or to storage — full detect→propose→review→merge is explicitly
follow-on work, not promised by S03's own stop condition. The v1 API (S04)
has no real production data migrated into it yet outside test fixtures
(deliberate — S01-S06 prove mechanics, not a specific workspace's backfill).

## E03 — Signal-Based Discover
Spec: `docs/gtm-transformation/epics/EPIC_03_SIGNAL_BASED_DISCOVER.md`

| Sprint | Objective | Test (lines) | App (lines) | Class. |
|---|---|---|---|---|
| S01 | Signal schema/source/freshness/dedup policies | `contracts/signal_v1.schema.yaml` + policy tests | `signal_policy.py` (113) | IMPLEMENTED |
| S02 | Ingestion adapters (public/manual/import) with provenance | `test_signal_ingestion.py` (97) | `signal_ingestion.py` (164) | IMPLEMENTED |
| S03 | SavedSearch/List/SmartList/Watchlist | `test_signal_lists.py` (108) | `signal_lists.py` (139) | IMPLEMENTED — no storage layer yet (self-scoped) |
| S04 | Explainable screening score + hard exclusions | `test_signal_screening.py` (100) | `signal_screening.py` (75) | IMPLEMENTED |
| S05 | Discover queue/API/read models | `test_signal_store.py` (76), `test_signal_routes.py` (109) | `signal_store.py` (97), `signal_routes.py` (63) | IMPLEMENTED |
| S06 | Discover UI + explicit `ResearchQueued` handoff | `test_signal_handoff.py` (69) | `signal_handoff.py` (71) | IMPLEMENTED — event has no consumer until E04 (self-scoped, resolved by E04) |

## E04 — Product-Blind Research and Company 360
Spec: `docs/gtm-transformation/epics/EPIC_04_PRODUCT_BLIND_RESEARCH_AND_COMPANY_360.md`

| Sprint | Objective | Test (lines) | App (lines) | Class. |
|---|---|---|---|---|
| S01 | ResearchCase/Claim/Evidence contracts + completeness policy | `test_research_policy.py` (146) | `research_policy.py` (125) | IMPLEMENTED |
| S02 | Queue/ownership/SLA/blockers/resume | `test_research_queue.py` (114), `test_research_case_store.py` (89) | `research_queue.py` (104), `research_case_store.py` (95) | IMPLEMENTED |
| S03 | Orchestration passes with budget/checkpoints | `test_research_orchestration.py` (90) | `research_orchestration.py` (97) | IMPLEMENTED |
| S04 | Contradiction/falsifier/side-story bounded workflows | `test_research_redteam.py` (141) | `research_redteam.py` (131) | IMPLEMENTED |
| S05 | Company 360 read model + provenance UI | `test_company360_view.py` (170), `test_claim_store.py`, `test_evidence_store.py` | `company360_view.py` (68), `claim_store.py` (70), `evidence_store.py` (62) | IMPLEMENTED |
| S06 | Review/accept/reopen/stale lifecycle | `test_research_review.py` (132) | `research_review.py` (134) | IMPLEMENTED — reviewer≠owner check is identity-only, no role system (self-scoped) |
| S07 | Contamination/coverage/factuality evals | `test_research_evals.py` (126) | `research_evals.py` (113) | IMPLEMENTED |

Cross-epic note: E03's `ResearchQueued` event now has E04's `ResearchCase` as
its intended reader, but no automated process yet turns the event into a
case record — explicitly named as still-open follow-on work in E04's own
acceptance record, not hidden.

## E05 — Demand as a First-Class Object
Spec: `docs/gtm-transformation/epics/EPIC_05_DEMAND_AS_FIRST_CLASS_OBJECT.md`

| Sprint | Objective | Test (lines) | App (lines) | Class. |
|---|---|---|---|---|
| S01 | Demand schema v1 + mapping from profiles/use cases | `test_demand_mapping.py` (118) | `demand_mapping.py` (60) | IMPLEMENTED |
| S02 | Lifecycle + qualification checklist/gates | `test_demand_lifecycle.py` (147) | `demand_lifecycle.py` (123) | IMPLEMENTED |
| S03 | Claim/Evidence links, confidence, contradiction | `test_demand_evidence.py` (135) | `demand_evidence.py` (83) | IMPLEMENTED — confidence reads a convenience field, not evidence-store lookup (self-scoped) |
| S04 | Demand queue/API/read model, optimistic edit | `test_demand_store.py` (116), `test_demand_routes.py` (184) | `demand_store.py` (147), `demand_routes.py` (113) | IMPLEMENTED |
| S05 | Demand UI + account dossier + resolvers | `test_demand_resolver.py` (53) | `demand_resolver.py` (44) | IMPLEMENTED |
| S06 | Legacy artifact migration/reconciliation | `test_demand_migrator.py` (140) | `demand_migrator.py` (174) | IMPLEMENTED — migrated `company_entity_id` uses a legacy-derived hash, not yet reconciled with E02's canonical entity id (self-scoped) |

## E06 — Product Intelligence and Immutable Snapshots
Spec: `docs/gtm-transformation/epics/EPIC_06_PRODUCT_INTELLIGENCE_AND_IMMUTABLE_SNAPSHOTS.md`

| Sprint | Objective | Test (lines) | App (lines) | Class. |
|---|---|---|---|---|
| S01 | Product/Version/Snapshot/Evidence schemas | `test_product_policy.py` (108) | `product_policy.py` (64) | IMPLEMENTED |
| S02 | Draft/review/publish/supersede workflow + RBAC | `test_product_workflow.py` (154) | `product_workflow.py` (138) | IMPLEMENTED — RBAC is a string check, no HTTP publish route (self-scoped, see below) |
| S03 | Snapshot hash, immutability, stale propagation | `test_product_snapshot_store.py` (112) | `product_snapshot_store.py` (89) | IMPLEMENTED |
| S04 | Catalog ownership/subscription per ADR-008 | `test_product_visibility.py` (78) | `product_visibility.py` (54) | IMPLEMENTED |
| S05 | API/search/diff/read models | `test_product_store.py`, `test_product_diff.py` (52), `test_product_routes.py` (136) | `product_store.py` (61), `product_diff.py` (35), `product_routes.py` (88) | PARTIAL | Full-text `product_search.py` descoped to diff/read-model contract only; self-declared, but does not match the sprint's own objective line ("API/search/diff/read models") literally |
| S06 | UI library/version diff/publish + legacy migration | `test_product_migrator.py` (182) | `product_migrator.py` (209) | IMPLEMENTED |

Note: this is the **one sprint marked PARTIAL rather than IMPLEMENTED** on a
strict reading — the Epic's own acceptance record calls the same fact a
"known limitation" rather than a gap, but the objective line explicitly says
"search" and no `product_search.py` exists; there is no HTTP publish route
either (`product_routes.py` is read-only, confirmed by grep — no
`POST .../publish` handler).

## E07 — Explainable Product Fit
Spec: `docs/gtm-transformation/epics/EPIC_07_EXPLAINABLE_PRODUCT_FIT.md`

| Sprint | Objective | Test (lines) | App (lines) | Class. |
|---|---|---|---|---|
| S01 | FitAssessment schema + input version locking | `test_fit_policy.py` (51) | `fit_policy.py` (51) | IMPLEMENTED |
| S02 | Hard gates/blockers/resolvers policy engine | `test_fit_gates.py` (94) | `fit_gates.py` (84) | IMPLEMENTED — gate evaluation itself is caller-supplied, not an automated evaluator (self-scoped) |
| S03 | Explainable scoring/coverage/gaps/alternatives | `test_fit_scoring.py` (91) | `fit_scoring.py` (103) | IMPLEMENTED |
| S04 | Review/decision/override/stale lifecycle | `test_fit_lifecycle.py` (170) | `fit_lifecycle.py` (144) | IMPLEMENTED |
| S05 | API queue/detail/compare read models | `test_fit_store.py` (90), `test_fit_routes.py` (128) | `fit_store.py` (132), `fit_routes.py` (112) | IMPLEMENTED — correction to a first-pass note: `fit_routes.py` actually has `POST /fit-assessments` and `PATCH /fit-assessments/{id}` (verified by grep), unlike E06/E08/E09/E10's GET-only route files; Fit is the one Epic with a real HTTP write path already |
| S06 | Fit workbench UI + E2E Demand→Fit | `test_fit_targeting_gate.py` (158) | `fit_targeting_gate.py` (28) | IMPLEMENTED |

## E08 — Buying Committee and Target Plans
Spec: `docs/gtm-transformation/epics/EPIC_08_BUYING_COMMITTEE_AND_TARGET_PLANS.md`

| Sprint | Objective | Test (lines) | App (lines) | Class. |
|---|---|---|---|---|
| S01 | TargetPlan/StakeholderRole/Influence schemas | `test_target_plan_policy.py` (111) | `target_plan_policy.py` (74) | IMPLEMENTED |
| S02 | Currentness/authority/warm-path evidence policies | `test_target_currentness.py` (85) | `target_currentness.py` (45) | IMPLEMENTED |
| S03 | Plan builder + validation workflow | `test_target_plan_workflow.py` (136) | `target_plan_workflow.py` (117) | IMPLEMENTED |
| S04 | Buying-committee graph/read model | `test_buying_committee_view.py` (71) | `buying_committee_view.py` (48) | IMPLEMENTED |
| S05 | API people↔target-plan + privacy controls | `test_target_plan_store.py` (75), `test_target_plan_routes.py` (112) | `target_plan_store.py` (101), `target_plan_routes.py` (78) | IMPLEMENTED — read-only (list/get/stakeholders/committee-graph); write path is Python-API-only (self-scoped, matches "API" wording loosely; grep confirms no POST/PATCH handler) |
| S06 | Targets/map/order UI + E2E Fit→Targets | `test_reach_gate.py` (101) | `reach_gate.py` (25) | IMPLEMENTED |

## E09 — Reach Execution Queue
Spec: `docs/gtm-transformation/epics/EPIC_09_REACH_EXECUTION_QUEUE.md`

| Sprint | Objective | Test (lines) | App (lines) | Class. |
|---|---|---|---|---|
| S01 | Sequence/Step/Task/Touchpoint schemas + channel policy | `test_reach_channel_policy.py` (63) | `reach_channel_policy.py` (62) | IMPLEMENTED |
| S02 | Message evidence binding, templates, approval | `test_reach_message_policy.py` (85) | `reach_message_policy.py` (61) | IMPLEMENTED |
| S03 | Execution queue: priorities, SLA, pause/cancel | `test_reach_queue.py` (146) | `reach_queue.py` (124) | IMPLEMENTED |
| S04 | Local scheduler, quotas, time windows | `test_reach_scheduler.py` (89) | `reach_scheduler.py` (67) | IMPLEMENTED — windows/quotas are process-local, no persisted store (self-scoped) |
| S05 | API: Sequences, Tasks, Touchpoints | `test_reach_store.py` (104), `test_reach_routes.py` (138) | `reach_store.py` (122), `reach_routes.py` (87) | IMPLEMENTED — read-only, write is Python-API-only (self-scoped) |
| S06 | My-day/Reach-queue/preview/approve UI + E2E | `test_reach_execution.py` (134) | `reach_execution.py` (75) | IMPLEMENTED |
| S07 | First allowed channel adapter or manual-send export | `test_reach_channel_adapter.py` (74) | `reach_channel_adapter.py` (71) | IMPLEMENTED — email adapter only; phone/manual covered via `build_manual_export` (self-scoped) |

## E10 — Engagement and Conversation Loop
Spec: `docs/gtm-transformation/epics/EPIC_10_ENGAGEMENT_AND_CONVERSATION_LOOP.md`

| Sprint | Objective | Test (lines) | App (lines) | Class. |
|---|---|---|---|---|
| S01 | Conversation/EngagementEvent/Objection schemas | `test_engagement_policy.py` (103) | `engagement_policy.py` (84) | IMPLEMENTED |
| S02 | Manual/import ingestion, dedup, touchpoint correlation | `test_engagement_ingestion.py` (93) | `engagement_ingestion.py` (94) | IMPLEMENTED |
| S03 | Classification, confidence, human review | `test_engagement_classification.py` (97) | `engagement_classification.py` (67) | IMPLEMENTED — confidence score is caller-supplied, not model-computed (self-scoped) |
| S04 | Inbox / follow-up / stop-sequence / next action | `test_engagement_inbox.py` (118) | `engagement_inbox.py` (79) | IMPLEMENTED |
| S05 | Engagement UI + E2E reply→follow-up/opportunity proposal | `test_engagement_opportunity.py` (30), `test_engagement_store.py` (85), `test_engagement_routes.py` (117), `test_engagement_e2e.py` (101) | `engagement_opportunity.py` (23), `engagement_store.py` (110), `engagement_routes.py` (74) | IMPLEMENTED — `propose_opportunity` returns a proposal record only, no TargetPlan/FitAssessment mutation or dedicated store yet (self-scoped); routes are read-only |

## E11 — Opportunity, Proof, Deal and Expansion
**Spec authority: UNKNOWN / absent.** There is no
`docs/gtm-transformation/epics/EPIC_11_*.md` and — unlike every other Epic
00–10, 12 and 13 — **no `docs/governance/EPIC_11_ACCEPTANCE.md` exists
either.** The only governance record is the six sprint-log STOP files
themselves (`docs/governance/sprint-log/E11-S0[1-6]_STOP.md`) plus one
passing mention in `docs/gtm-transformation/12_PROGRAM_ROADMAP.md` ("E11 |
Opportunity, proof, deal et land & scale | 6 | E10") and gap row G13 in
`01_AS_IS_AUDIT_AND_GAP_MAP.md`. Classification below is therefore against
each sprint's **own stated stop condition** (the only written acceptance
criterion that exists), not against an Epic-level spec — per the task's own
classification discipline, this counts as UNKNOWN at the *documentation*
level even though the *code* is directly verified. See
`DOCUMENTATION_DRIFT.md` and the final report for why this is flagged as the
most significant finding.

| Sprint | Objective (from STOP) | Test (lines) | App (lines) | Class. |
|---|---|---|---|---|
| S01 | Canonical Lead/Opportunity/Proof/Deal/Expansion contracts | `test_opportunity_contracts.py` (68) | (contracts, no dedicated module beyond stores below) | IMPLEMENTED (code/tests verified); spec-doc authority UNKNOWN |
| S02 | Explicit qualification/conversion/Opportunity-stage lifecycle | `test_opportunity_lifecycle.py` (76) | `opportunity_policy.py` (129) | IMPLEMENTED; spec-doc authority UNKNOWN |
| S03 | Bounded, provenance-linked Discovery notes + append-only commercial log | `test_opportunity_notes.py` (51) | `opportunity_notes.py` (62) | IMPLEMENTED; spec-doc authority UNKNOWN |
| S04 | Proof design, outcomes, success metrics | `test_proof_policy.py` (35) | `proof_policy.py` (43) | IMPLEMENTED; spec-doc authority UNKNOWN |
| S05 | Stable workspace-scoped Pipeline reads | `test_opportunity_store.py` (45) | `opportunity_store.py` (72), `opportunity_routes.py` (35) | IMPLEMENTED; spec-doc authority UNKNOWN |
| S06 | Loss reasons, won-only expansion, outcome-linked learning event | `test_commercial_outcomes.py` (40) | `commercial_outcomes.py` (27) | IMPLEMENTED; spec-doc authority UNKNOWN |

## E12 — GTM Experience Replatform
Spec authority: `docs/governance/ADR-010_GTM_FRONTEND_REPLATFORM.md` (E12's
decision record — no separate epics/ spec doc; task brief correctly
anticipated this). Acceptance: `docs/governance/EPIC_12_ACCEPTANCE.md`.

| Sprint | Objective | Test (lines) | Class. |
|---|---|---|---|
| S01 | Frontend-stack decision by measured migration cost | ADR-010 itself (measured baseline table) | IMPLEMENTED |
| S02 | GTM shell, workspace-safe deep links, route-owned context | `test_gtm_router_contract.py` (21) | IMPLEMENTED |
| S03 | Home/Discover/Research render real workspace-scoped queues | `test_gtm_upstream_spaces.py` (20) | **IMPLEMENTED as of this closeout sprint** — was PARTIAL when this audit was written: Home and Discover were real, but Research called `GET /api/v1/workspaces/{ws}/research-cases`, which no backend route registered anywhere in `app/` (only Company 360 was exposed, despite `app/research_case_store.py`'s `list_cases`/`get_case` already existing, fully tested at the store level, and unused). The guarding test only string-matched the endpoint name in frontend source, so it passed despite the route being missing. **Fixed in this same closeout pass**: `app/research_routes.py` now exposes `GET /research-cases` and `GET /research-cases/{research_case_id}` over the existing store functions (same auth/pagination/IDOR shape as `signal_routes.py`), with 7 new route-level tests added to `tests/test_research_routes.py` (TDD: written first, confirmed failing against the old route file, then made to pass). `tests/test_gtm_upstream_spaces.py` was also strengthened to fire a real unauthenticated request at every `gtm-spaces.js` endpoint and assert 401/403 (route exists) rather than 404 (route missing) — the exact regression class the old string-match test could not catch; confirmed this new test fails against the pre-fix route file and passes after. |
| S04 | Fit/Targets/Reach read v1 APIs, gates shown as pass/blocked | `test_gtm_decision_spaces.py` (18) | IMPLEMENTED |
| S05 | Engagement/Pipeline/Insights boundary | `test_gtm_downstream_spaces.py` (19) | IMPLEMENTED |
| S06 | Telemetry, accessibility, mobile, `?legacy=1` rollback | `test_gtm_shell_quality.py` (30) — read in full this session; asserts `gtm:navigation` telemetry event, `aria-current`, `focus-visible`, 720px media query, 44px touch targets, and that legacy panels exist but are absent from primary nav | IMPLEMENTED |

Note: the frontend contract test files are genuinely short (18–30 lines)
because they assert against static `app.js`/`router.js`/`index.html`/
`styles.css` text content rather than a rendered DOM (no browser test
runner in the unit-test suite) — read in full to confirm they are real
assertions, not stubs. Deeper behavioral coverage of the same routes is
carried by the 3 Playwright E2E journeys (`tests/e2e/*.spec.ts`), gated
separately by `scripts/run_e2e_gate.py` in CI (confirmed green, see
`IMPLEMENTATION_BASELINE.md`).

## E13 — Insights, Cost and Governed Learning
Spec authority: **no dedicated spec doc or ADR** — only
`docs/governance/EPIC_13_ACCEPTANCE.md` and the five
`docs/governance/EPIC_13_S0[1-5]_STOP.md` files (different location/naming
convention than every prior Epic's `docs/governance/sprint-log/` STOP
files — itself a minor drift, see `DOCUMENTATION_DRIFT.md`). Classified
against each STOP file's own stop condition (read in full this session).

| Sprint | Objective | Test (lines) | App (lines) | Class. |
|---|---|---|---|---|
| S01 | Metric catalog: source/unit/aggregation/value field; explicit cohort boundaries | `test_insights_metrics.py` (45) | `insights_metrics.py` (78) | IMPLEMENTED |
| S02 | Reproducible funnel/quality/cost event projections, reconciliation | `test_insights_projection.py` (44) | `insights_projection.py` (61) | IMPLEMENTED |
| S03 | Audited LearningProposal lifecycle, no auto-mutation | `test_learning_proposals.py` (56) | `learning_proposals.py` (108) | IMPLEMENTED |
| S04 | Baseline/canary experiment evaluation, drift rollback | `test_learning_experiments.py` (34) | `learning_experiments.py` (62) | IMPLEMENTED |
| S05 | Workspace-scoped Insights API + actionable privacy-aware UI | `test_insights_routes.py` (59), `test_insights_frontend.py` (28) | `insights_routes.py` (75) + `app/frontend/gtm-spaces.js` `renderInsights()` (read in full) | IMPLEMENTED |

---

## Overall status count

**79 sprints total**: **77 IMPLEMENTED** (against their own stop condition;
several carry explicit, self-declared, narrow deferrals that do not change
the classification), **1 PARTIAL** (E06-S05 — "search" in the objective line
with no `product_search.py` built), and **1 flagged UNKNOWN at the
documentation-authority level while its code is IMPLEMENTED** (all 6 E11
sprints, collectively, for lack of any Epic-level spec doc or acceptance
record at the time this audit was written — now closed, see
`docs/governance/EPIC_11_ACCEPTANCE.md`, authored retroactively from the
six STOP files in this same closeout pass). No sprint was classified
NOT_IMPLEMENTED or REGRESSED: nothing found claims completion while lacking
a real, substantive, passing test.

**Post-audit fix**: E12-S03 was found PARTIAL by this audit — Research
called a backend route (`/research-cases`) that did not exist anywhere in
`app/` — and was fixed in the same closeout pass (see the E12 section
above and `docs/audit/post-epic/DOCUMENTATION_DRIFT.md` item 8). Reclassified
IMPLEMENTED above to reflect the fix; this paragraph is the historical
record of what the audit actually found before the fix.

Cross-cutting, self-documented gaps that recur across many epics without
changing any single sprint's classification: no HTTP write route yet for
product publish (E06), target-plan create/patch (E08), reach create/patch
(E09), or engagement events (E10) — all Python-API-only by design so far;
and `feat/prospection-principes-todo` remains unmerged (now archived as a
tag, not a live branch — see `OPEN_BRANCH_AND_PR_MAP.md`).
