# STOP — Epic 09 / Sprint S07

## Objective

Adaptateur premier canal autorisé ou manual-send export. Stop
condition: "LinkedIn write toujours interdit sans ADR" (LinkedIn write
is always forbidden without an ADR).

## Outputs

- `app/reach_channel_adapter.py`:
  - `EmailAdapter`: the first authorized channel adapter. Delegates to
    S06's already-audited `send_touchpoint` -- adds no bypass of its
    own, and refuses a non-email touchpoint.
  - `build_manual_export(touchpoint)`: for `phone`/`manual` channels
    only -- produces a `ManualExportRecord` a human executes by hand;
    it never itself marks the touchpoint sent (a later explicit
    `send_touchpoint` call still does that once the human confirms).
    Refuses `email` and `linkedin` channels, and any non-`prepared`
    touchpoint.
  - `get_adapter(channel)`: the sole adapter lookup point -- always
    re-checks `assert_channel_authorized_to_send` first, so asking for
    `linkedin` raises the same `ChannelNotAuthorizedError` as the
    channel-policy layer (Epic 09 S01), never a bare `KeyError`; no
    adapter is ever registered for `linkedin` in `_ADAPTERS`, keeping
    the categorical prohibition enforced at this layer too, not just
    documented.
- `tests/test_reach_channel_adapter.py`: 11 tests -- email adapter
  sends and refuses a non-email touchpoint; `get_adapter` returns the
  email adapter, raises `ChannelNotAuthorizedError` for `linkedin` (the
  gold case), and raises plainly for an authorized-but-unadapted
  channel (`phone`); manual export builds for phone/manual, refuses
  email/linkedin and a non-prepared touchpoint, and never marks the
  touchpoint sent as a side effect.

## Evidence

`python -m unittest tests.test_reach_channel_adapter -v`: 11/11 pass.
Full `python scripts/check_release.py`: 0 errors (including the
LinkedIn deferred-design validator, unaffected since no LinkedIn write
path is ever introduced).

## Epic 09 status

All 7 sprints closed: S01 Sequence/Step/Task/Touchpoint schemas and
channel policy (no implicit send); S02 message evidence binding and
approval (sourced citations, verbatim, active claims only); S03
execution queue with duplicate-free retries and pause/cancel cascade;
S04 local scheduler with quotas/time windows and explicit degraded
mode; S05 API read model (workspace-scoped, IDOR-safe, bounded
pagination); S06 the prepare->approve->send loop and the my-day queue,
proven end to end from an authorized reach gate; S07 the first
authorized channel adapter (email) plus a manual-send export for
phone/manual, with LinkedIn write still categorically unavailable
without a dedicated ADR at both the policy and adapter layers.
