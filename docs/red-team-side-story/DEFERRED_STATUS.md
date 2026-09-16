# Red-Team / Issue / Side-Story spec — DEFERRED

**Status: TODO — not implemented. Do not implement from this spec without re-reading this file first.**

## What this is

`spec/*.md` is an externally-authored (GPT-assisted) BMAD/SDLC proposal for
three layered mechanisms on top of `ai-maturity-diagnostic`:

- **System Red-Team** (technical): bounded falsification of a decision/run,
  one repair + one verify max, feeds a loopback event.
- **Issue / CounterPerspective / SideStory** (business): a transversal
  registry for objections, contradictions, unknowns, and a storytelling
  composition layer (side stories) used in fit notes, outreach and
  reactivation — explicitly never a source of new evidence.
- **Dreaming / Loopback** (learning loop): aggregates red-team findings and
  outcomes into candidate system deltas, promoted only by a human gate.

It is well-structured (storage-agnostic, contract-first, explicit ADRs,
PR sequencing with shadow-mode rollout) and the concepts (red-teaming a
decision, an issue-first-then-story pipeline, a governed learning loop) are
judged genuinely valuable and differentiating for this project's maturity
story.

## Why it is deferred, not implemented

Reviewed against the actual codebase (see conversation this branch came
from): the project has **no completed real E2E business cycle yet** (no
hand-run demand → fit → reach → outreach → follow-up pass has been
executed end to end by its first real user). Building 5 epics / ~10 new
contracts / 8 PRs / a 4-tier dreaming engine now would repeat the exact
mistake already identified and corrected once on the storage/Baserow
question: designing a platform ahead of a demonstrated need. The Dreaming
mechanism specifically *requires* real run history to learn from — there
is none yet.

Separately, a narrower slice of this spec (a minimal Issue/red-team
concept, scoped tight) is being evaluated for real in a **separate**
throwaway branch against existing test fixtures, on a strict "push only if
it measurably improves the fixtures, kill if complexity grows faster than
functional value" rule. That evaluation is independent of this deferred
branch: this branch exists only to preserve the full spec text without
committing to any of it, and without letting it rot as an orphaned upload.

## Review gate — when to come back to this

Re-open this spec (read it fresh, not from memory) only when **one full
real end-to-end business cycle has been run** by an actual user of the
platform (demand/fit signal → qualification → reach/wedge → outreach →
at least one follow-up or reactivation decision), so that:

- there is at least one real `Outcome` to reason about;
- at least one real recurring friction (a repeated objection, a stale
  follow-up, a fit false-positive) can be pointed to as the reason a
  specific piece of this spec is now justified;
- the narrow-slice evaluation above (if it landed) has already absorbed
  whatever part of this spec turned out to be cheap and clearly useful,
  so this review only has to decide on what's left.

Do not implement any epic from `08_BMAD_FULL_SDLC_IMPLEMENTATION.md`
speculatively. If re-opened, re-run only Phase A1/A2 (current-state audit)
first, and re-derive the epic priority from what the audit finds at that
time, not from this spec's own suggested sequencing, which predates any
real usage.
