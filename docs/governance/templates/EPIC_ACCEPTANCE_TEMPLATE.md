# Epic {NN} — Acceptance Record

Filled in once, at the `dev`→`main` release PR for this Epic. Per
`13_STOP_GO_RELEASE_PLAYBOOK.md`'s Epic gate.

## Sprints closed

<List each Sprint, its PR number into `dev`, and one line on what it shipped.>

## Gate checklist

- [ ] All Sprints obligatoires accepted; any deferred item explicit (link it).
- [ ] Full release gate (`scripts/check_release.py`) green on `dev` at the
      release commit.
- [ ] E2E gate (`scripts/run_e2e_gate.py`) run for real, regressions: none.
- [ ] Audit invariants (evidence-first / product-blind / hard gates /
      currentness / lineage — whichever this Epic touches) re-checked, not
      assumed.
- [ ] Migration and rollback rehearsed, if this Epic touched persisted data.
- [ ] `docs/governance/SUPERSESSION_REGISTRY.md` and
      `docs/governance/TRACEABILITY_MATRIX.md` updated for anything this
      Epic added or dispositioned.
- [ ] Release notes and known limitations published (this file's "Known
      limitations" section, or a linked doc).

## Known limitations

<What is intentionally left undone, and which future Epic/Sprint owns it.>

## Go/No-Go

<Decision, date, who/what made the call (a person, or "all gate items
green, no open blocker" if this was run autonomously).>
