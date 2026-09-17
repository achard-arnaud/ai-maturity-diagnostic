# Epic 15 — S01: CRUD Capability Matrix

Status: gate deliverable, per `EPIC_15_CRUD_RETRIEVAL_AND_ARTIFACT_LIBRARY.md`'s
S01 ("For every canonical object classify CREATE/UPDATE/ARCHIVE/DELETE/
RESTORE/IMMUTABLE/WORKFLOW_ONLY/HUMAN_DECISION_ONLY. Reject 'CRUD
everywhere'."). Built directly on
`docs/research/next-wave/CRUD_SEARCH_ARTIFACT_GAP.md` (CLAUDE_01
Workstream D), re-verified against the current `app/*_routes.py` state
(P0 and Epic 14 landed write routes on some objects the gap doc predates).

Baseline: `main == dev` at Epic 14 closeout (`9414d73`).

## Legend

- **CREATE / UPDATE / ARCHIVE / DELETE / RESTORE**: a general-purpose
  HTTP verb is the right shape for this object.
- **IMMUTABLE**: written once; a correction is a new record
  (`supersedes`/`superseded_by`), never an in-place edit.
- **WORKFLOW_ONLY**: mutation is real and needed, but only through a
  small set of named state transitions (never a generic PATCH of
  arbitrary fields) -- the object's own policy module is the source of
  truth for which transitions are legal.
- **HUMAN_DECISION_ONLY**: an append-only record of something a human
  asserted (a note, a decision); never algorithmically generated or
  edited after the fact.

## 1. Matrix

| Object | Classification | HTTP today | This Epic's scope |
|---|---|---|---|
| Company / Person (`company_v1`, `person_v1`) | CREATE, UPDATE | CREATE on legacy surface only (`POST /api/network/*`); no UPDATE anywhere | **Out of scope** (not named in S05's priority list; legacy create already exists and a v1 UPDATE route is a bigger, separate CRM-shaped decision the architecture owner hasn't asked for here) |
| Signal (`signal_v1`) | WORKFLOW_ONLY (`app.signal_policy.can_transition`) | Read-only + one-way `queue-research` handoff; **no review transition route** (`new -> reviewed`) exists at all | **In scope, narrow**: a review-transition route is a hard prerequisite for ResearchCase lifecycle (S05) to be reachable by an actual HTTP caller instead of a direct store write |
| Evidence (`evidence_v1`) | IMMUTABLE | Read via Epic 14's evidence flows only; no direct list/get route | Out of scope for write (immutable by design); a `GET` read route is S03/S04's job (artifact index), not a new write verb |
| ResearchCase (`research_case_v1`) | WORKFLOW_ONLY (`app.research_policy.can_transition_case`) | Read-only; case creation and status transitions are Python-only | **In scope** (S05 names this explicitly) |
| Claim (`claim.schema.yaml`) | WORKFLOW_ONLY (creation gated by `app.research_policy.validate_claim_lineage`; no in-place edit of an accepted claim) | No HTTP route at all (`app.claim_store` has no importer) | **In scope**, bound to an open ResearchCase (S05) |
| Demand (`demand_v1`) | CREATE, UPDATE | Full CREATE+UPDATE with `expected_version` (Epic 05/06) | Already done; **out of scope** |
| Product / ProductSnapshot (`product_v1`, `product_snapshot_v1`) | Product: CREATE/UPDATE (deferred); ProductSnapshot: IMMUTABLE | Read-only; publish is Python-only (`app.product_workflow`) | **Out of scope** (not named in S05; Product's mutable-parent write path is a separate, larger product-catalog-ownership decision already covered by ADR-008, not this Epic's to reopen) |
| FitAssessment (`fit_assessment_v1`) | CREATE, UPDATE | Full CREATE+UPDATE with `expected_version` (Epic 07) | Already done; **out of scope** |
| TargetPlan (`target_plan_v1`) | CREATE | No write route at all (`app.target_plan_store.put_plan` unwired) | **In scope** (S05 names this explicitly) |
| StakeholderRole (`stakeholder_role_v1`) | CREATE, WORKFLOW_ONLY (status active/inactive, `supersedes_stakeholder_role_id` chain) | Read-only (`put_stakeholder` unwired); Epic 14 S06 added one narrow write (`acquire-linkedin`) that creates evidence/identity-mapping, not a stakeholder itself | **In scope**, alongside TargetPlan |
| ExternalIdentityMapping (`external_identity_mapping`) | WORKFLOW_ONLY (`candidate` only from acquisition; `validated`/`rejected` needs a separate human step) | Write path added in Epic 14 S06 (candidate-only); no route to move a mapping past `candidate` | **Out of scope for this Epic** (validating a mapping is a role-validation-workflow decision, not an artifact/CRUD concern; flagged, not built, to avoid scope creep matching Epic 14 S06's own boundary) |
| Sequence / Step / Task / Touchpoint (`sequence_v1`, `step_v1`, `task_v1`, `touchpoint_v1`) | Sequence/Step/Task: CREATE; Touchpoint: CREATE + WORKFLOW_ONLY send transition (`app.reach_channel_policy`) | Read-only; `app.reach_store`'s `put_sequence/put_step/put_task/put_touchpoint` all exist, fully unwired | **In scope** (S05's "Reach/Sequence controls"; the channel-send policy already exists and is fully tested, only routing was missing) |
| EngagementEvent / Conversation / Objection | CREATE (ingestion-shaped, not user-authored) | Read-only; ingestion is Python-only (`app.engagement_ingestion`) | **Out of scope** (not named in S05; engagement ingestion is a connector/import concern, not a user-facing CRUD gap) |
| Opportunity / Deal | WORKFLOW_ONLY (opportunity stage progression is downstream of Fit/Reach, not this Epic's to redesign) | Read-only | Opportunity itself: **out of scope**. Its notes/decisions: see next row |
| DiscoveryNote / CommercialDecision (`discovery_note_v1`, `commercial_decision_v1`) | HUMAN_DECISION_ONLY | Pure, tested, **unwired** functions exist (`app.opportunity_notes.create_discovery_note` / `record_commercial_decision`) with no store and no route | **In scope** (S05 names "Opportunity notes/decisions persistence" -- this is that exact gap) |
| LearningProposal | WORKFLOW_ONLY | Already fully wired (`app.insights_routes`: create + transition), Epic 13 | Already done; **out of scope** |
| Artifact (cross-object discovery record) | New, index-only; never itself domain truth | Does not exist | **In scope**: S02 (contract) + S03 (index) + S04 (search) + "safe artifact archive" is an index-level visibility flag, reversible, never a canonical-object mutation |

## 2. What "safe artifact archive" (S05) means

Per the Epic's own "Don't": *"let the library mutate domain truth."* An
artifact-index entry can be marked `archived` (hidden from default
listing) and `restored`, but this **only ever changes the index's own
metadata record** (`app.artifact_index`, S03) -- it never touches the
canonical object the artifact points to, and never cascades a status
change onto Demand/Fit/ResearchCase/etc. A restore is always safe because
nothing but discoverability was ever changed.

## 3. Rejected: CRUD everywhere

Explicitly **not** built this Epic, with reasons:

- Company/Person UPDATE, Product mutable-parent write path, Opportunity
  stage-progression writes, EngagementEvent/Conversation authoring,
  ExternalIdentityMapping validation -- none are named in S05's priority
  list; each is either a separate, larger architectural decision (Product:
  ADR-008; identity validation: a role-validation workflow that doesn't
  exist yet) or has no demonstrated active-job need surfaced in the gap
  analysis.
- No object gets a generic hard DELETE. Per the gap analysis, nothing in
  this codebase's history treats delete as a requirement it deferred --
  archive/restore (index-level, per §2) covers the actual need
  ("stop showing me this") without an irreversible action anyone asked for.
- No new document store, full-text engine, or vector index. S03/S04 build
  a rebuildable index over the *existing* canonical stores (same
  `ArtifactStore`-backed JSONL convention already used by
  evidence/signal/research_case/claim/demand/fit/target_plan/reach), never
  a second source of truth.

## 4. Sprint mapping

- **S02**: Artifact metadata contract (`contracts/artifact_v1.schema.yaml` + `app.artifact_policy`).
- **S03**: `app.artifact_index` -- rebuild from the stores listed in §3, enumerate/filter/paginate/related-to-object/related-to-run/latest/all-versions.
- **S04**: search/discovery API over the index (`/api/v1/workspaces/{id}/artifacts`), workspace-isolated, bounded, deterministic ordering.
- **S05**: the priority mutations from §1's "In scope" rows -- Signal review transition, ResearchCase lifecycle transitions, Claim creation, TargetPlan + StakeholderRole creation, Sequence/Step/Task/Touchpoint creation + send action, DiscoveryNote/CommercialDecision persistence, artifact archive/restore.
- **S06**: Company 360 expansion to aggregate Fit/TargetPlan/Reach/Engagement/Opportunity (currently only Signal+ResearchCase+Demand).
- **S07**: Artifact Library UI is Antigravity's (per the Epic header, "UI V1: Antigravity only" is not stated for E15, but S07 itself splits "Antigravity: list/grid... / Claude: real APIs, permissions, loading/error/accessibility/deep links" -- Claude's half is already delivered by S03/S04's APIs; no separate work item beyond making sure error/permission shapes are consistent, verified in S08's NRT).
- **S08**: NRT/recovery -- cross-workspace, index rebuild, archive semantics, conflict handling, deep links, Company 360 consistency.
