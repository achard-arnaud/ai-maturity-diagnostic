# Traceability Matrix

Sprint E00-S05 deliverable. Maps each requirement this Epic owns to the
contract/artifact that states it and the test/check that verifies it stays
true. Rows are added by future Sprints/Epics as they land; this is not a
one-off report, it's a living index — keep it current in the same PR that
changes the underlying contract or test.

| Requirement | Source | Contract / artifact | Verified by |
|---|---|---|---|
| CI checks required on PR + push to `main` | `13_STOP_GO_RELEASE_PLAYBOOK.md` | `.github/workflows/qa.yml`, `.gitlab-ci.yml` | Both pipelines' `release-check` job |
| CI checks required on push to `dev`/`sprint/**`/`epic/**` | `13_STOP_GO_RELEASE_PLAYBOOK.md`, audit gap G02 | `.github/workflows/qa.yml` `on.push.branches` | Manual: a push to `dev` after E00-S03 triggers `release-check` (verify on next push) |
| `dev` leads/matches `main` as the Sprint-branch integration base | `13_STOP_GO_RELEASE_PLAYBOOK.md` branching model | `docs/governance/baseline/E00-S01_baseline.yaml` (finding), E00-S03 merge commit | `git log origin/dev..origin/main` empty after E00-S03 merges |
| Release gate covers lint, packaging, schema validation, privacy scan, coverage ≥80% | `10_LEARNING_LOOP_OBSERVABILITY_AND_QA.md` test pyramid | `scripts/check_release.py` | Its own `RESULT: 0 release error(s)` output, run in CI on every PR/push |
| E2E journeys are reproducible and gated on real regressions | Epic 00 S04 stop condition ("E2E reproductible") | `scripts/run_e2e_gate.py`, `tests/e2e/*.spec.ts` | `e2e-gate` CI job; local run logged in PR #33's test plan (15/29 passed, 0 unexpected failures) |
| A Sprint PR carries a Stop&Go handoff | `13_STOP_GO_RELEASE_PLAYBOOK.md` Sprint gate item 8 | `docs/governance/sprint-log/*.md` | Manual review at PR time; `docs/governance/templates/SPRINT_HANDOFF_TEMPLATE.md` gives the required sections |
| PRD/ADR supersession is explicit, not implicit | Audit gap G01 | `docs/governance/SUPERSESSION_REGISTRY.md` | Manual review; kept current whenever a PRD/ADR is added or a branch is dispositioned |
| Legacy `/api/*` routes are a known, temporary compatibility surface, not the target shape | `06_ROUTE_CONTEXT_AND_API_MODEL.md` | `docs/governance/baseline/E00-S01_baseline.yaml` (`tests_and_routes_inventory`) | Re-run the baseline's route inventory before Epic 12 (replatform) to check for drift |
| A minted dev session actually authenticates against a freshly started app | Needed for S04's E2E gate to run at all | `scripts/dev_login.py` (`--db` default) | `scripts/run_e2e_gate.py`'s own successful auth step (its `mint_storage_state()` + a passing non-GAP authenticated test is proof) |
| Catalog ownership is shared-core plus explicit workspace overlays | E01-S01, ADR-008 | `contracts/catalog_ownership.schema.yaml` | `tests/test_catalog_ownership_policy.py` |
| Canonical file mutations are atomic, root-scoped and version-aware | E01-S02 | `app/artifact_store.py` | `tests/test_artifact_store.py` plus legacy writer suites |
| Platform events are append-only, hash-chained, correlated and idempotent | E01-S03 | `app/event_journal.py`, `app/execution_context.py` | `tests/test_event_journal.py` |
| Runs can checkpoint, fail, resume or cancel without fabricating completion | E01-S04 | `app/run_manager.py` | `tests/test_run_manager.py` |
| AI/tool execution respects explicit budgets, cache identity and bounded retry | E01-S05 | `app/execution_policy.py` | `tests/test_execution_policy.py` |
| Legacy workspace migration is dry-run-first, hash-verified and reversible | E01-S06 | `app/workspace_migrator.py`, `scripts/migrate_workspace.py` | `tests/test_workspace_migrator.py` |

## Epic 00 acceptance checklist

Per `docs/gtm-transformation/epics/EPIC_00_GOVERNANCE_BASELINE_AND_DELIVERY.md`:

- [x] S01: HEAD/branches/PRD/ADR/tests/routes inventoried; baseline versioned (`docs/governance/baseline/E00-S01_baseline.yaml`).
- [x] S02: glossary/bounded-context vocabulary reconciled (no renaming needed); supersession registry adopted; all three flagged branches dispositioned.
- [x] S03: CI triggers extended; `dev`/`main` drift closed.
- [x] S04: E2E journeys wired into a real, reproducible, regression-gated CI job.
- [x] S05: this traceability matrix + the Sprint/Epic/handoff templates below.
- [x] Epic acceptance: witness PRs to `dev` (#32, #33) passed the gates; baseline/limitations published in `docs/governance/EPIC_00_ACCEPTANCE.md`. The witness release to `main` is the PR that carries this commit.

## Known limitations carried forward (not blocking Epic 00 acceptance)

- `feat/prospection-principes-todo` remains unmerged (package-validator failures); owned by a future skill-authoring sprint, not Epic 00.
- `docs/gtm-transformation/`'s own Epics 01-13 are unstarted; this Epic only establishes the governance baseline they build on.
- The GitLab `e2e-gate` mirror job is unverified against a live GitLab runner (no GitLab CI access from this environment) — only the GitHub Actions job has been observed running for real.
