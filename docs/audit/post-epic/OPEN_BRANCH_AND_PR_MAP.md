# Open Branch and PR Map — verified 2026-09-17

Sources: `git ls-remote --heads origin`, `git ls-remote --tags origin`,
`mcp__github__list_branches`, `mcp__github__list_pull_requests` (state=all).

## Open pull requests

**Re-verified: zero.** `mcp__github__list_pull_requests(state=all,
perPage=30)` returns the 30 most recent PRs (#37–#66), every one
`state=closed`. No `state=open` PR exists. This confirms the cadrage pack's
"PR #65 still open" premise is stale — #65 (E12) and #66 (E13) are both
closed with merge commits present on `main`.

## Remote branches (6 total)

| Branch | Tip SHA | Disposition |
|---|---|---|
| `main` | `7a8a618` | Current release head (== `dev`) |
| `dev` | `7a8a618` | Identical to `main`; not ahead or behind |
| `epic/11-opportunity-proof-deal-expansion` | `28113f6` | **Merged** into `main` via PR #64 (merge commit `59007c4` is `main`'s ancestor). Stale, not deleted post-merge. Safe to delete; no unique commits remain unmerged. |
| `epic/12-gtm-experience-replatform` | `0929450` | **Merged** into `main` via PR #65 (merge commit `54cbd29`). Stale, not deleted post-merge. Safe to delete. |
| `epic/13-insights-cost-governed-learning` | `f1179f1` | **Merged** into `main` via PR #66 (merge commit `7a8a618`, current HEAD). Stale, not deleted post-merge. Safe to delete. |
| `claude/peaceful-wozniak-8yqv32` | (last used at `5900674` for PR #63) | Recurring working branch reused across ~26 PRs (#38 through #63: every "acceptance record" doc PR and several sprint-batch PRs). All of those PRs are merged. Stale relative to `dev`/`main`. Safe to delete once no further PR is planned from it. |

**Triage verdict: none of the 4 non-`main`/`dev` branches need content
review or a merge/retain/defer/reject decision** — all are already fully
merged; the only action needed is branch-deletion housekeeping (not done by
this Phase-1 task, per instructions to only write files).

## `feat/prospection-principes-todo` — the deliberately-unmerged branch

This is **not currently a live remote branch**. It does not appear in
`git ls-remote --heads origin` or `mcp__github__list_branches`. It exists
only as an **archive tag**:
`refs/tags/archive/pre-gtm-cleanup-2026-09-16/feat-prospection-principes-todo`
(commit `20a4bbc15e19ff5698db92c61d2a584097c99d84`).

Per `docs/governance/SUPERSESSION_REGISTRY.md` (written at E00-S02, before
the E00-S01 baseline's branch-cleanup event tagged-and-removed it):
- **Disposition: "Retain on branch — not merged."**
- **Rationale**: adds `skills/prospection-principes/` (status: `todo`).
  Merging it makes `scripts/check_release.py` fail — the package validator
  rejects it because `SKILL.md` exceeds the 500-line limit, it is missing
  `agents/openai.yaml`, and it uses an unsupported frontmatter key `status`.
  Left unmerged intentionally: "not merging a red change is preferred over
  merging it 'as incubating' and weakening the gate."
- Nine separate Epic acceptance records (E00, E02, E03, E04, E05, E06, E07,
  E08, E09, E10) each carry forward the identical one-line "still unmerged"
  note as a known limitation, none attempting or claiming to fix it — this
  is the correct, consistent behavior the task description anticipated
  ("a package-validator failure, not something to fix here").
- **Drift found**: because the branch was later converted to an archive tag
  (as part of the same 2026-09-16 cleanup that archived 16 other pre-GTM
  branches — see `IMPLEMENTATION_BASELINE.md`), every one of those nine
  acceptance records' present-tense wording ("remains unmerged," "retained
  on branch") is now slightly stale: the *decision* (don't merge; it's
  validator-red) still holds, but the branch itself no longer exists in
  live form, only as a tag. This is cosmetic, not a functional gap — the
  skill's content is unreachable either way — but is listed precisely in
  `DOCUMENTATION_DRIFT.md`.

## Archived branches-as-tags (`archive/pre-gtm-cleanup-2026-09-16/*`)

17 branches, pre-dating the E00–E13 GTM programme, were converted to tags on
2026-09-16 rather than deleted outright (34 tag refs = 17 annotated tags,
each with a `^{}` dereference to its commit):

```
agent-advanced-research-public-first
agent-merge-majeur-agentic-market-mapping
agent-skills-bi-application-nice
agent-update-readme-v0-4
agent-v0-5-productized-diagnostic
agent-v0-6-demand-matching-nudging
agent-v0-7-value-chain-reach-graph
agent-v07-release-hotfix
agent-v08-foundation-design
agent-v08-workspace-ux-refinement
agent-v09-canonical-entity-two-pager
chatgpt-connection-test
claude-gifted-johnson-qxh9nx
docs-benchmark-red-team-handoff
docs-red-team-side-story-spec-deferred
epic-01-platform-transaction-execution
feat-prospection-principes-todo
```

Three of these (`docs-benchmark-red-team-handoff`,
`docs-red-team-side-story-spec-deferred`, `feat-prospection-principes-todo`)
map directly to the three branches `docs/governance/SUPERSESSION_REGISTRY.md`
gave an explicit disposition for at E00-S02 (no-op/close, merged-as-defer,
retain-unmerged respectively) — consistent with what the registry says,
just archived-as-tag rather than left as a live branch afterward. The other
14 tags (pre-v0.4-through-v0.9 agent branches, plus one archived early
`epic-01-platform-transaction-execution` branch) predate the governance
registry's scope entirely and require no further disposition — they are
already fully superseded by the shipped `main` history and preserved purely
as historical record.

## Summary

- 0 open PRs (re-verified).
- 0 branches need a merge/retain/defer/reject decision — everything live is
  either the release head or already-merged.
- 1 named deliberately-unmerged item (`feat/prospection-principes-todo`)
  exists only as an archive tag now, not a live branch — decision unchanged,
  documentation wording about it is stale (see `DOCUMENTATION_DRIFT.md`).
