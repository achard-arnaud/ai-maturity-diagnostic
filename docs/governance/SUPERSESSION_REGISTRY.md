# Supersession Registry

Sprint E00-S02 deliverable (`docs/gtm-transformation/epics/EPIC_00_GOVERNANCE_BASELINE_AND_DELIVERY.md`).
Resolves audit gap G01 (PRD/ADR stacking with no supersession record) and the
three unmerged branches the E00-S01 baseline flagged as open decisions.

Authority order (per `docs/gtm-transformation/README.md`, unchanged by this
registry): contracts/tests on `HEAD` > accepted ADRs > `docs/gtm-transformation/`
target models > older PRDs > mockups.

## PRD lineage (docs/PRD_*.md)

These are genuinely incremental, not duplicate specs — each documents the
delta introduced by one control-plane version and explicitly says it does not
replace the prior version's boundaries. No content is deleted here; status is
recorded so a reader knows which is the current contract.

| Document | Status | Note |
|---|---|---|
| `PRD_productized_diagnostic_v0_5.md` | Historical | Superseded in effect by v0.6-v0.9; kept as the record of the original control-plane decision. |
| `PRD_control_plane_v0_6.md` | Historical | Superseded in effect by v0.7-v0.9. |
| `PRD_control_plane_v0_7.md` | Historical | Superseded in effect by v0.8/v0.9. |
| `PRD_runtime_foundation_v0_8.md` | **Active** | Describes the currently-implemented auth/multi-workspace runtime (`app/authruntime/`); still the reference for that layer. |
| `PRD_linkedin_qualification_plugin_v0_1.md` | Active (deferred capability) | Describes an opt-in, not-yet-activated plugin; status unchanged by this registry. |
| README.md v0.9 CRM section | **Active**, current-latest | Not a separate PRD file; the CRM sprint described there is the latest layer. Fixed a stale header in this same Sprint (README title said v0.4 while the body already documented v0.9 — see E00-S01 baseline finding). |

Going forward, product/architecture direction is governed by
`docs/gtm-transformation/` (see its own README for authority order), which
supersedes all of the above as the target model — without invalidating them
as historical record of what was actually decided and shipped at each step.

## ADRs (docs/ADR-*.md)

All active; none contradicted or reversed by another. Recorded here only to
confirm the registry considered them, not because any status changed:

`ADR-004-web-control-plane-boundary`, `ADR-005-demand-use-case-nudging-boundaries`,
`ADR-006-uc-graph-reach-blocker-resolution`, `ADR-007-multi-workspace-auth-runtime`,
`ADR_linkedin_external_adapter`.

## Unmerged branches — disposition

Per `07_WORKFLOW_HANDOFF_AND_ARTIFACT_MODEL.md`: side stories are branches
linked to the trunk with an explicit merge/retain/defer/reject decision.

| Branch | Disposition | Rationale |
|---|---|---|
| `docs/benchmark-red-team-handoff` | **No-op / close** | Diff against `main` is empty — its content is already present on `main`. Nothing to merge; branch closed as redundant. |
| `docs/red-team-side-story-spec-deferred` | **Merged as defer** | Adds `docs/red-team-side-story/DEFERRED_STATUS.md` + `spec/*.md`: a well-structured, externally-authored red-team/issue/side-story/dreaming proposal, self-labeled `Status: TODO — not implemented` in its own `DEFERRED_STATUS.md`, explicitly reasoned as premature (no completed real E2E business cycle yet to learn from). Docs-only, no conflict with the existing `docs/red-team-side-story/{current-state-map,moscow-next-sprints,trigger-journey-audit}.md` on `main`. Merged as reference material; remains non-actionable until a real run history exists, per its own status file — this registry does not change that status. Verified: `scripts/check_release.py` stays green after this merge (docs-only). |
| `feat/prospection-principes-todo` | **Retain, unmerged — now archived as a tag, not a live branch** | Adds `skills/prospection-principes/` (status: `todo`). Directly relevant to the prospection-module direction flagged for post-Epic-00 work, but merging it makes `scripts/check_release.py` **fail**: the package validator rejects it (`SKILL.md` exceeds the 500-line limit, missing `agents/openai.yaml`, and an unsupported frontmatter key `status`). This is exactly why it was left unmerged — it is not validator-clean yet. As of the post-E13 closeout audit (2026-09-17) this content no longer lives on a live branch: a 2026-09-16 branch cleanup converted it to tag `archive/pre-gtm-cleanup-2026-09-16/feat-prospection-principes-todo`. The underlying decision is unaffected — a future skill-authoring sprint should still fix it (trim `SKILL.md`, add the missing agent manifest, and either drop the `status` key or extend the package validator's accepted frontmatter schema to support incubating skills) and merge only once green, working from the tag rather than a branch. Not merging a red change is preferred over merging it "as incubating" and weakening the gate. |

## Vocabulary alignment (02_DOMAIN_AND_TRUTH_MODEL.md)

The existing `AGENTS.md` v0.3 vocabulary (network / enterprise / product /
commercial / learning, hard gates, product-blind research) already matches
the corpus's bounded-context model in spirit; no renaming was needed to
reconcile them. `AGENTS.md` is left as the contract-of-record for agents
working the current runtime; `docs/gtm-transformation/02_DOMAIN_AND_TRUTH_MODEL.md`
is the forward-looking target vocabulary for the objects this Epic and later
Epics introduce (Demand, ProductSnapshot, FitAssessment, etc., most of which
don't exist as first-class objects yet — see Epic 05-08).
