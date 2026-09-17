# Epic 03 — Signal-Based Discover — Acceptance Record

Per `13_STOP_GO_RELEASE_PLAYBOOK.md`'s Epic gate.

## Sprints closed

| Sprint | Shipped |
|---|---|
| S01 | `contracts/signal_v1.schema.yaml` + `app/signal_policy.py`: schema structurally excludes every demand-only field; dedup key; freshness/expiry; lifecycle state machine. |
| S02 | `app/signal_ingestion.py`: public/manual/import adapters, no live network call ("core sans intégration"). |
| S03 | `app/signal_lists.py`: deterministic SavedSearch matching; versioned List/SmartList/Watchlist. |
| S04 | `app/signal_screening.py`: explicable research-priority score; hard exclusions absolute; structurally guarded against ever being fit-shaped. |
| S05 | `app/signal_store.py` + `app/signal_routes.py`: `/api/v1/workspaces/{workspace_id}/signals` read model, stable sort, real IDOR tests. |
| S06 | `app/signal_handoff.py`: explicit `ResearchQueued` handoff into Epic 01's EventJournal; never a `Demand`/`Fit`. |

All six shipped in one PR to `dev`: [#41](https://github.com/achard-arnaud/ai-maturity-diagnostic/pull/41).

## Gate checklist

- [x] All 6 Sprints accepted; no new deferred item created by this Epic
      beyond what Epic 00/02 already carry.
- [x] Full release gate green on `dev` at `6986900`, re-verified fresh
      after the merge.
- [x] E2E gate green on PR #41's CI (release-check + e2e-gate both
      green across both duplicate CI runs).
- [x] Audit invariants this Epic owns re-checked: **signal ≠ demand**
      enforced at three independent layers — the schema itself
      (`additionalProperties: false`, no demand-only field can validate),
      a runtime guard (`assert_no_demand_fields`, called by every
      ingestion adapter and the handoff payload), and structurally at the
      score layer (a gold-set-style test walks the score type's fields
      and every factor name for fit/offer-shaped language). The S06
      handoff can only ever reach a `ResearchQueued` event, never a
      `Demand`/`Fit` object (neither exists in this codebase yet).
- [x] Migration/rollback: not applicable — this Epic introduced a new,
      additive object (Signal) with no legacy artifact to migrate from;
      the signal store is append/upsert-only via `ArtifactStore`.
- [x] Legacy screening explicitly verified untouched: the pre-existing
      35-test legacy network suite re-run after all 6 sprints, still
      35/35, unchanged — no file under
      `app/network_writer.py`/`network_index.py`/`account_view.py`/
      `duplicate_dismissals.py` or `skills/network-account-screening/`
      was touched.
- [x] Release notes and known limitations published below.

## Known limitations

- No live public-source fetch or premium connector exists behind
  `ingest_public` — deliberately deferred, per the Epic's own "sources
  premium/connecteurs" line. The adapter's contract (content-in,
  signal-out) is ready for one to be wired in later without changing
  callers.
- `SignalList`/`SavedSearch`/`Watchlist` (S03) have no storage layer yet
  — they're pure, tested functions/dataclasses; persisting them is
  follow-on work for whichever Epic/Sprint needs Discover's UI to
  actually save a user's lists.
- The `ResearchQueued` event (S06) is written to the EventJournal but has
  no consumer yet — Epic 04's `ResearchCase` (not yet built) is the
  intended reader. Until Epic 04 ships, queuing research from a signal
  records the event but nothing acts on it.
- Carried over from Epic 00/02 (not created by this Epic):
  `feat/prospection-principes-todo` unmerged (now archived as tag `archive/pre-gtm-cleanup-2026-09-16/feat-prospection-principes-todo`, not a live branch); GitLab's `e2e-gate`
  mirror unverified against a live runner.

## Go/No-Go

**Go.** All gate items are green or explicitly, narrowly deferred with a
named owner; no open blocker is specific to Epic 03. Decision made
autonomously per the operator's instruction to process Epics 03, 04, 05
iteratively with the same procedure, merging progressively to `dev` and
releasing to `main` at each Epic's acceptance.
