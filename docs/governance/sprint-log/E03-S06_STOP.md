# STOP — Epic 03 / Sprint S06

## Objective

UI Discover et handoff explicite ResearchQueued. Stop condition: "ancien
screening accessible" (old screening remains accessible), tested via
signal→queue E2E.

## Outputs

- `app/signal_handoff.py`: `queue_research(root, signal, requested_by)`.
  Per the lifecycle doc's handoff rule (a Signal never reaches Demand/Fit
  directly), this appends a `ResearchQueued` event to Epic 01's
  `EventJournal` — it does **not** create a `ResearchCase` object (that's
  Epic 04's, not yet built). Requires `status == "linked"` (reviewed and
  connected to a company) and a non-empty `requested_by`; the handoff
  payload itself is run through `assert_no_demand_fields` too. Idempotent
  via the journal's own idempotency-key mechanism (double-queueing the
  same signal returns the same event, doesn't duplicate it).
- `POST /api/v1/workspaces/{workspace_id}/signals/{signal_id}/queue-research`
  added to `app/signal_routes.py`.
- `tests/test_signal_handoff.py`: 6 tests (linked signal queues,
  unlinked/reviewed-not-linked rejected, missing requester rejected,
  event lands in the journal, idempotent double-queue).
- Two E2E tests added to `tests/test_signal_routes.py`: an unreviewed
  ("new") signal is rejected (400) through the real route, and a linked
  signal is queued (200, `ResearchQueued` in the response) — this is the
  Sprint's "signal→queue" E2E gate.

## "Ancien screening accessible"

No legacy screening code (`app/network_index.find_potential_duplicates`,
`skills/network-account-screening`, `contracts/account_screening.schema.yaml`,
the `/api/network/duplicates` route, etc.) was touched anywhere in Epic 03
S01-S06. Verified by re-running the pre-existing legacy network suite
(35 tests, same set re-checked at the end of Epic 02) — still 35/35,
unchanged.

## Evidence

`python -m unittest tests.test_signal_handoff tests.test_signal_routes -v`:
15/15 pass.

## Epic 03 status

All 6 Sprints closed. Epic acceptance (a sourced signal can be reviewed,
linked to a company, rejected/expired, or converted to a `ResearchQueued`
handoff without creating a `Demand`/`Fit`) is verified across S01-S06's
tests: S01's schema structurally excludes demand fields; S04's screening
score is structurally guarded against ever looking fit-shaped; S06's
handoff only reaches a `ResearchQueued` event, never a `Demand` object
(which doesn't exist in this codebase yet — Epic 05).
