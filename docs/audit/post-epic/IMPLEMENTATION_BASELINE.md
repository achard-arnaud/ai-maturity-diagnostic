# Implementation Baseline — verified 2026-09-17

Ground truth reconstructed directly from `origin` (GitHub API + `git`), not
from the cadrage pack. The cadrage pack's assumption that main/dev were stuck
at end-of-E11 with PR #65 (E12) open and no E13 branch is **wrong** — E11,
E12 and E13 are all merged, no PR is open, and CI on the resulting `main`
head is green (verified via the GitHub API, not assumed).

## HEAD state

- `origin/main` == `origin/dev` == `7a8a6180a5c4589d1d9983758333451ab314973e`
  ("Merge pull request #66 from
  achard-arnaud/epic/13-insights-cost-governed-learning — Release Epic 13 —
  Insights, Cost and Governed Learning", authored by `achard-arnaud`,
  2026-09-17T08:11:06Z).
- `54cbd29fe54e1731720341ebbaf4e2e4ddca0c6b` (merge of PR #65, Epic 12) is the
  first parent of `7a8a618`, i.e. `main`'s history is
  `... -> 54cbd29 (E12) -> 7a8a618 (E13)`.
- `git list_pull_requests(state=open)` (re-verified with
  `mcp__github__list_pull_requests`, `state=all`, top 30) returns **zero**
  open PRs. The 30 most recent are all `state=closed`.

## Merged release PRs (via `mcp__github__list_pull_requests`, `state=all`)

| PR | Title | Base | Head | Merge commit on `main` |
|---|---|---|---|---|
| #64 | Release Epic 11 — Opportunity, Proof, Deal and Expansion | main | epic/11-opportunity-proof-deal-expansion | `59007c4058091f2854303b6501fa0b30b7b8c63f` |
| #65 | Release Epic 12 — GTM Experience Replatform | main | epic/12-gtm-experience-replatform | `54cbd29fe54e1731720341ebbaf4e2e4ddca0c6b` |
| #66 | Release Epic 13 — Insights, Cost and Governed Learning | main | epic/13-insights-cost-governed-learning | `7a8a6180a5c4589d1d9983758333451ab314973e` |

(Note: the GitHub API's `merged` boolean field on these three came back
`false` while `merged_at` is populated and `state` is `closed` — an API-field
inconsistency in this listing endpoint, not evidence of an unmerged PR. `git
log --first-parent main` and the presence of each merge commit exactly where
expected settles it: all three are merged.)

Below #64, PRs #37–#63 are the E01–E10 sprint-batch and per-epic-acceptance
PRs (each epic shipped as a `dev`-targeted sprint-batch PR plus a
`main`-targeted release PR); all closed/merged, consistent with the sprint
logs.

## Remote branches (`git ls-remote --heads origin`)

| Branch | SHA | Status |
|---|---|---|
| `main` | `7a8a618` | current |
| `dev` | `7a8a618` | identical to `main` (not ahead, not behind) |
| `epic/11-opportunity-proof-deal-expansion` | `28113f6` | merged into main (PR #64); not deleted post-merge |
| `epic/12-gtm-experience-replatform` | `0929450` | merged into main (PR #65); not deleted post-merge |
| `epic/13-insights-cost-governed-learning` | `f1179f1` | merged into main (PR #66); not deleted post-merge |
| `claude/peaceful-wozniak-8yqv32` | `5900674` (as pushed for PR #63) | the recurring sprint/acceptance-record working branch reused across many PRs (#38–#63); currently sitting at the tip used for PR #63 (E10 acceptance doc), itself merged |

No branch is ahead of `main`/`dev`; nothing here needs an integration
decision. `epic/11`, `epic/12`, `epic/13` and `claude/peaceful-wozniak-8yqv32`
are stale-but-harmless (fully merged) and are housekeeping candidates for
deletion, not release blockers. See `OPEN_BRANCH_AND_PR_MAP.md` for the full
disposition table.

## Archived pre-GTM branches (tags under `archive/pre-gtm-cleanup-2026-09-16/*`)

34 tag refs (17 distinct branches, each with a `^{}` dereference entry) exist
under this prefix — i.e. 17 branches that predate the E00–E13 GTM programme
were converted to tags and their live branches removed, on 2026-09-16, before
E00 started:

`agent-advanced-research-public-first`, `agent-merge-majeur-agentic-market-mapping`,
`agent-skills-bi-application-nice`, `agent-update-readme-v0-4`,
`agent-v0-5-productized-diagnostic`, `agent-v0-6-demand-matching-nudging`,
`agent-v0-7-value-chain-reach-graph`, `agent-v07-release-hotfix`,
`agent-v08-foundation-design`, `agent-v08-workspace-ux-refinement`,
`agent-v09-canonical-entity-two-pager`, `chatgpt-connection-test`,
`claude-gifted-johnson-qxh9nx`, `docs-benchmark-red-team-handoff`,
`docs-red-team-side-story-spec-deferred`, `epic-01-platform-transaction-execution`,
`feat-prospection-principes-todo`.

Important correction to the task brief: `feat/prospection-principes-todo` is
**not currently a live remote branch**. `git ls-remote --heads origin` does
not list it; it exists only as the archive tag
`archive/pre-gtm-cleanup-2026-09-16/feat-prospection-principes-todo`
(`20a4bbc`). `docs/governance/SUPERSESSION_REGISTRY.md` and multiple Epic
acceptance records (00, 02, 06, 07, 08, 09, 10) still describe it in the
present tense as "retained on branch — not merged," which was accurate at
the time each was written but is now stale relative to the branch-cleanup
event that archived it as a tag. The underlying decision (don't merge; it
fails the package validator) is unaffected — only the branch's continued
live existence is not. See `DOCUMENTATION_DRIFT.md`.

## CI setup

- `.github/workflows/qa.yml` is the enforced source of truth (two jobs:
  `release-check` running `python scripts/check_release.py`, and `e2e-gate`
  running Playwright via `python scripts/run_e2e_gate.py`). Triggers: every
  PR, and pushes to `main`, `dev`, `agent/**`, `sprint/**`, `epic/**`,
  `claude/**`.
- `.gitlab-ci.yml` mirrors it (`release-check` + `e2e-gate` stages) and says
  so in its own comment ("GitHub Actions (.github/workflows/qa.yml) is the
  enforced source of truth for the E2E gate; this mirrors it for GitLab").
  No evidence a GitLab runner has ever executed it from this environment;
  every Epic's own acceptance record says the same ("GitLab `e2e-gate` mirror
  unverified against a live runner").

## Actual CI status on `main`@`7a8a618` (verified, not assumed)

Checked via `mcp__github__actions_list` (`list_workflow_runs`, branch=main)
and `mcp__github__actions_list` (`list_workflow_jobs`, run 35198329115):

- Workflow run **35198329115** ("QA"), triggered by the PR #66 merge commit
  push to `main`, **head_sha = `7a8a6180a5c4589d1d9983758333451ab314973e`**
  (exactly the commit in question) — **status: completed, conclusion:
  success**.
- Both jobs in that run are individually green:
  - `release-check`: completed / success (all steps succeeded, including
    "Run release gate").
  - `e2e-gate`: completed / success (Playwright install, app start and "Run
    E2E gate" step all succeeded; failure-artifact upload step correctly
    `skipped` since nothing failed).
- The prior four runs on `main` (E12 merge `54cbd29`, E11 merge `59007c4`,
  the E08 release commit `b877 89b`, and one PR #61/E09 merge that shows
  **conclusion: failure**) were also inspected; the E09 merge-commit run
  failing is historical (superseded by later green commits) and does not
  affect the current HEAD's status.

**Conclusion: CI on the current `main`/`dev` head is empirically green**,
confirmed live from GitHub, not inferred from the merge having happened.

## Independent local reproduction (this session)

`scripts/check_release.py` was actually executed in this worktree (not just
read) after building a throwaway venv (`python3 -m venv` + `pip install -e
'.[docs,dev]'` — the pre-existing system Python had a broken `cryptography`
install that blocked in-place installs, so a venv was used instead):

```
PASS: ruff lint
PASS: package validator
PASS: LinkedIn deferred-design validator
PASS: unit and integration tests with app coverage
PASS: app line coverage >=80%
PASS: YAML/JSON parsing and JSON Schema meta-validation
PASS: local Markdown links
PASS: private-key and absolute-home-path scan
PASS: DOCX example configuration
PASS: DOCX example generation
SKIP: private network validator (private data not present in clone)
RESULT: 0 release error(s)
```

`python -m unittest discover -s tests -v`: **1149 tests, all passed (1
skipped)**, in 10.4s. `coverage report`: **91% line coverage** on `app/`
(branch coverage on; TOTAL 6720 statements / 450 missed), well above the 80%
gate. This is a real, reproduced-in-this-session result, not a claim taken
on faith from the sprint logs.

The E2E gate (`scripts/run_e2e_gate.py`, Playwright) was **not** run locally
in this session (would require installing Playwright + a Chromium browser,
which was judged out of scope given the already-confirmed green GitHub
Actions result for the exact same commit). Its outcome above is taken from
the verified GitHub Actions run, not assumed.
