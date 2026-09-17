# Epic 09 — Reach Execution Queue — Acceptance Record

Per `13_STOP_GO_RELEASE_PLAYBOOK.md`'s Epic gate.

## Sprints closed

| Sprint | Shipped |
|---|---|
| S01 | `contracts/sequence_v1.schema.yaml`/`step_v1.schema.yaml`/`task_v1.schema.yaml`/`touchpoint_v1.schema.yaml` + `app/reach_channel_policy.py`: no implicit send, LinkedIn write categorically forbidden without an ADR. |
| S02 | `app/reach_message_policy.py`: citations must reference an active claim and quote its statement verbatim; approval gated to `reach_reviewer`, never bypassed by role alone. |
| S03 | `app/reach_queue.py`: deterministic priority ordering, duplicate-free retry, pause/resume, cancel cascading to open work only. |
| S04 | `app/reach_scheduler.py`: quotas + time windows, explicit degraded mode on any refusal, never a silent drop or a forced send. |
| S05 | `app/reach_store.py`/`app/reach_routes.py`: bounded-access API read model for sequences/steps/tasks/touchpoints. |
| S06 | `app/reach_execution.py`: the prepare->approve->send loop and the my-day queue, proven end to end from the Epic 08 reach gate. |
| S07 | `app/reach_channel_adapter.py`: the first authorized channel adapter (email) and a manual-send export for phone/manual; LinkedIn never registered, `get_adapter("linkedin")` raises. |

All 7 shipped in one PR to `dev`: [#59](https://github.com/achard-arnaud/ai-maturity-diagnostic/pull/59).

## Gate checklist

- [x] All 7 Sprints accepted; no new deferred item created by this Epic
      beyond what Epic 00-08 already carry.
- [x] Full release gate green on `dev` after every sprint, re-verified
      fresh after the merge.
- [x] E2E gate green on PR #59's CI (release-check + e2e-gate both green
      across both duplicate CI runs, no re-run needed this time).
- [x] Audit invariants this Epic owns re-checked: **aucun send
      implicite**: `app.reach_channel_policy.assert_no_implicit_creation_as_sent`
      is the sole choke point a Step/Touchpoint's creation path must
      pass through, and it rejects any attempt to create one already
      marked sent; `app.reach_execution.send_touchpoint` is the only
      function that can move a touchpoint to `sent`, always a distinct
      later action with a real `sent_by`. **LinkedIn write toujours
      interdit sans ADR**: enforced at two independent layers --
      `app.reach_channel_policy.CHANNEL_SEND_ALLOWED["linkedin"] = False`
      (proven by `test_linkedin_send_forbidden`) and
      `app.reach_channel_adapter._ADAPTERS` never registers a `linkedin`
      entry, so `get_adapter("linkedin")` raises
      `ChannelNotAuthorizedError` rather than silently returning nothing
      usable. **Claims sourcés**: `app.reach_message_policy.validate_citations`
      rejects a citation to an unknown claim, a non-active claim, or any
      `quoted_text` that is not a verbatim substring of the claim's own
      `statement` -- the embellishment gold case is explicitly tested.
      **Retry sans doublon**: `app.reach_queue.retry_step` refuses a
      second in-flight attempt (`prepared`/`sent`) for the same
      `step_id`, proven by dedicated duplicate-retry tests.
- [x] Migration/rollback: not applicable -- this Epic introduces new,
      additive objects (Sequence/Step/Task/Touchpoint) with no legacy
      artifact to migrate from.
- [x] Legacy screening/network suite explicitly re-verified untouched:
      the pre-existing 35-test suite re-run after all 7 sprints, still
      35/35, unchanged.
- [x] Release notes and known limitations published below.

## Known limitations

- `app.reach_store`/`app.reach_routes` do not yet expose a write path
  (create/patch) over HTTP -- S05 shipped read routes only
  (list/get/steps/tasks/touchpoints). Writing sequences, steps, tasks
  and touchpoints is currently Python-API-only (via
  `app.reach_execution`/`app.reach_queue`/`app.reach_message_policy`
  directly); an HTTP write route is deferred, narrow follow-on work,
  same pattern as Epic 06's still-unbuilt product-publish route and
  Epic 08's still-unbuilt target-plan write route.
- `app.reach_channel_adapter` ships a single real adapter (email); phone
  and manual channels are covered only by `build_manual_export` (a
  human executes the touchpoint outside the system, then a separate
  `send_touchpoint` call records it). A dedicated phone-dialer or
  manual-CRM-export integration is deferred, narrow follow-on work.
- `app.reach_scheduler`'s time windows and quotas are process-local,
  in-memory inputs supplied by the caller -- there is no persisted,
  workspace-configurable quota/window store yet; a future Sprint can
  add one without changing `evaluate_schedule`'s contract.
- Carried over from Epic 00-08 (not created by this Epic):
  `feat/prospection-principes-todo` unmerged (now archived as tag `archive/pre-gtm-cleanup-2026-09-16/feat-prospection-principes-todo`, not a live branch); GitLab's `e2e-gate`
  mirror unverified against a live runner; Epic 06's product-publish
  route, Epic 07's `dimension_checks`/`gate_checks` evaluation-skill
  wiring, and Epic 08's target-plan write route all remain unbuilt, as
  documented in their own acceptance records.

## Go/No-Go

**Go.** All gate items are green or explicitly, narrowly deferred with a
named owner; no open blocker is specific to Epic 09. Decision made
autonomously per the operator's instruction to continue the same
iterative sprint-by-sprint procedure through Epics 06-10.
