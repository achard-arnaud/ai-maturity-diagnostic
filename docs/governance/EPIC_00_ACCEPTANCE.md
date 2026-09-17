# Epic 00 — Governance, Baseline and Delivery — Acceptance Record

Per `13_STOP_GO_RELEASE_PLAYBOOK.md`'s Epic gate.

## Sprints closed

| Sprint | PR | Shipped |
|---|---|---|
| S01 | [#32](https://github.com/achard-arnaud/ai-maturity-diagnostic/pull/32) | GTM North Star corpus versioned at `docs/gtm-transformation/`; machine-readable baseline of `main@5468e57` (`docs/governance/baseline/E00-S01_baseline.yaml`); Stop&Go handoff. Found and fixed a real bug along the way (`scripts/build_sector_rollups.py` non-deterministic glob order) by porting an existing upstream fix. |
| S02 | [#33](https://github.com/achard-arnaud/ai-maturity-diagnostic/pull/33) | `docs/governance/SUPERSESSION_REGISTRY.md`: PRD v0.5-v0.8 lineage, ADR list, and dispositions for the three branches S01 flagged. README version-header fix. `scripts/dev_login.py` default-path bug fix. |
| S03 | #33 | `dev` brought to parity with `main` (was 39 commits behind); CI push triggers extended to `dev`/`sprint/**`/`epic/**`/`claude/**`. |
| S04 | #33 | `scripts/run_e2e_gate.py`: the 3 dormant Playwright journeys now run for real in CI, gated on non-GAP regressions only (per `tests/e2e/README.md`'s living-spec design). Found and fixed a second real bug during this same PR: `playwright.config.ts`'s hardcoded sandbox-only Chromium path, which made the gate fail 100% of the time on the actual GitHub Actions runner until fixed. |
| S05 | #33 | `docs/governance/TRACEABILITY_MATRIX.md` and the Sprint/Epic handoff templates under `docs/governance/templates/`. |

## Gate checklist

- [x] All 5 Sprints accepted. One deferred item recorded explicitly (not a Sprint gap): `feat/prospection-principes-todo` stays unmerged, now archived as tag `archive/pre-gtm-cleanup-2026-09-16/feat-prospection-principes-todo` rather than a live branch — see Supersession Registry.
- [x] Full release gate (`scripts/check_release.py`) green on `dev` at `e34187a` (this Epic's final commit before the `main` release): 0 errors, ruff/package/LinkedIn-design/tests/coverage(≥80%)/schema/markdown-links/privacy/DOCX checks all PASS.
- [x] E2E gate (`scripts/run_e2e_gate.py`) run for real against `dev` at `e34187a`: 16/29 passed, 0 regressions among non-GAP tests. (Also green twice in GitHub Actions CI on the S02-S05 PR, after the two real bugs above were found and fixed — the first CI runs on this Epic were red, correctly, and driven to green rather than worked around.)
- [x] Audit invariants this Epic touches (evidence-first documentation authority, no business-logic mutation without a stated requirement) re-checked: no `app/` business logic changed except the two concrete bug fixes named above, both required to make the gates this Epic owns actually work.
- [ ] Migration/rollback rehearsal: not applicable — this Epic touched no persisted business data, only docs, CI config, and two script defaults.
- [x] `docs/governance/SUPERSESSION_REGISTRY.md` and `docs/governance/TRACEABILITY_MATRIX.md` are current as of this record.
- [x] Release notes and known limitations: see below.

## Known limitations (owned by later Epics/Sprints, not blocking this Epic's acceptance)

- `feat/prospection-principes-todo` remains unmerged, now archived as tag `archive/pre-gtm-cleanup-2026-09-16/feat-prospection-principes-todo` rather than a live branch: fails the package validator (`SKILL.md` >500 lines, missing `agents/openai.yaml`, unsupported frontmatter key `status`). Left for a dedicated skill-authoring sprint.
- The GitLab `e2e-gate` mirror job (`.gitlab-ci.yml`) has not been observed running on a live GitLab runner from this environment — only the GitHub Actions job is empirically verified.
- `docs/gtm-transformation/`'s Epics 01-13 are entirely unstarted; this Epic only establishes the governance baseline (CI, branch hygiene, documentary authority) they build on.
- Legacy `/api/*` and `/admin/*` routes remain the only API surface (per the S01 baseline's route inventory) — the target `/api/v1/workspaces/{workspace_id}/...` shape from `06_ROUTE_CONTEXT_AND_API_MODEL.md` does not exist yet; that's Epic 01+ work, not Epic 00's.
- Seven `GAP:`-titled E2E assertions now pass (listed in each Sprint's PR test plan) — their GAP markers should be retired in whichever frontend sprint owns that UI area, not as part of this Epic.

## Go/No-Go

**Go.** All gate items above are green or explicitly and narrowly deferred with a named owner; no open blocker remains for Epic 00 specifically. Decision made autonomously per explicit operator instruction (continue through Epic 00's Sprints, merge progressively to `dev`, and open the `main` release without an intermediate check-in) — see this repository's `claude/peaceful-wozniak-8yqv32` session history for the full working record (PRs #32 and #33).
