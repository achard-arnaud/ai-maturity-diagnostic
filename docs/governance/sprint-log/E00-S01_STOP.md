# STOP — Epic 00 / Sprint S01

## Objective

Inventorier HEAD, branches, PRD/ADR/tests/routes ; produire une baseline
machine-readable. (Sprint plan, `docs/gtm-transformation/epics/EPIC_00_GOVERNANCE_BASELINE_AND_DELIVERY.md`.)

## State

- Sprint branch: `claude/peaceful-wozniak-8yqv32`, forked from `origin/dev` (commit `b5726c6`).
- Base branch for the PR: `dev`, per the target branching model (`13_STOP_GO_RELEASE_PLAYBOOK.md`).
- Audited revision described by the baseline: `main@5468e57` (matches the corpus's stated audit revision).
- Docs-only addition, plus one ported one-line fix (see "CI" below) — no new
  application behavior, no scope change to this Sprint's inventory objective.

## Outputs

- `docs/gtm-transformation/` — the 14-document North Star corpus (00–13) plus
  `epics/EPIC_00_GOVERNANCE_BASELINE_AND_DELIVERY.md`, committed as reference
  material so it survives beyond this chat session and can be cited by path.
- `docs/governance/baseline/E00-S01_baseline.yaml` — machine-readable
  inventory: runtime, CI/release-gate reproduction (reproduced locally,
  0 errors, 88% coverage), branch topology, PRD/ADR/doc inventory, route
  inventory, confirmed gaps (G01, G02, G14) with fresh evidence, and open
  decisions for S02/S03.
- `docs/governance/sprint-log/E00-S01_STOP.md` — this handoff.

## Evidence gathered this sprint (beyond what the audit doc could reproduce)

- `scripts/check_release.py` reproduced successfully on `main@5468e57`
  (jsonschema is a core dependency; the audit's inability to run it was an
  environment-install gap, not a repo defect). Result: 0 errors, coverage 88%
  (`app` line coverage, branch coverage on).
- `origin/dev` is a **strict ancestor** of `main`, 39 commits behind, 0 commits
  ahead — it is stale, not a leading integration branch.
- All ~64 API routes in `app/server.py` / `app/authruntime/app.py` are flat
  legacy `/api/*` or `/admin/*`; none use the target
  `/api/v1/workspaces/{workspace_id}/...` shape from
  `06_ROUTE_CONTEXT_AND_API_MODEL.md`.
- Playwright is configured (3 journeys) but wired into neither
  `scripts/check_release.py` nor either CI pipeline — confirmed dormant.
- `README.md` title says `v0.4` while its body already documents a `v0.9` CRM
  section (git history) — a concrete, previously undocumented instance of the
  version-drift gap (G01).

## CI

The first `release-check` run on this PR (base `dev`) failed on
`test_rollup_ingests_company_use_case_evidence`
(`AssertionError: 'UC-1' != 'UC-3'`). Root cause: `scripts/build_sector_rollups.py`
iterated `studies_root.glob(...)` in unsorted filesystem readdir order — the test
data passed locally (creation order happened to match) but not on the CI
runner. This was **not caused by this PR** (no `app/`/`scripts/`/`tests/`
files were touched by the original commit) and is not a flake either: it
reproduced identically on a re-run. `git log origin/dev..origin/main --
scripts/build_sector_rollups.py` showed the fix already exists and is
merged on `main` (commit `c3dad49`, "fix: sort study manifest glob for
deterministic sector rollups") — `main@5468e57`'s own CI run
(35092966945) is green with it. Ported the same one-line `sorted(...)`
fix into this branch (`dev` doesn't have it yet) rather than widening the
PR further; verified locally (isolated test + full 84-test suite, twice).

## Remaining (deferred, not blocking this Sprint's stop condition)

- S02: adopt glossary/bounded-context vocabulary, and rule on the
  supersession registry for PRD v0.5–v0.8 and the unmerged
  `docs/red-team-side-story-spec-deferred`, `docs/benchmark-red-team-handoff`,
  `feat/prospection-principes-todo` branches (merge/retain/defer/reject each).
- S03: extend CI triggers to `dev`/`sprint/**`/`epic/**`; decide whether
  `dev` is fast-forwarded/rebuilt from `main` first so it can actually serve
  as the Sprint-branch integration target going forward.
- S04: wire the 3 Playwright journeys into a real, tagged E2E gate.
- S05: requirements→contracts→tests traceability matrix and Sprint/Epic/handoff
  templates.

## Commands to resume

```bash
git clone https://github.com/achard-arnaud/ai-maturity-diagnostic.git
cd ai-maturity-diagnostic
git checkout claude/peaceful-wozniak-8yqv32
python -m pip install -e '.[docs,dev]'
python scripts/check_release.py   # reproduces the green gate on main; run from a main checkout to see full app coverage
```

## Risks / notes

- The sprint branch name (`claude/peaceful-wozniak-8yqv32`) follows the
  session's execution-harness convention rather than the corpus's own
  `sprint/E00-S01_name` naming; this mismatch is itself a finding for S03
  (CI trigger patterns must match whatever naming is actually enforced).
- `dev` being stale means a PR opened against it will show only this
  Sprint's docs-only diff, which is correct for S01 but means `dev` still
  does not reflect `main`'s current app state — do not treat `dev` as
  authoritative for app code until S03 resolves this.
