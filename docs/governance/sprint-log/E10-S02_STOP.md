# STOP — Epic 10 / Sprint S02

## Objective

Manual/import ingestion, dedup and touchpoint correlation. Stop
condition: "events idempotents" -- re-ingesting the same raw record
must never create a second EngagementEvent.

## Outputs

- `app/engagement_ingestion.py`:
  - `ingest_engagement_event(...)`: the sole ingestion entry point --
    looks up `source_ref` among already-stored events first; a match
    is returned as-is (`created=False`), never re-created.
  - `ingest_batch(records, existing_events)`: ingests a batch (e.g. one
    import file), checking each record against both prior storage and
    records already processed earlier in the same batch -- a batch
    with the same `source_ref` twice still yields exactly one created
    event.
  - `correlate_touchpoint(channel, occurred_at, candidate_touchpoints)`:
    best-effort correlation to the most recently sent Touchpoint on
    the same channel, sent at or before the event's `occurred_at`;
    returns `None` (never a guess) when no candidate qualifies.
- `tests/test_engagement_ingestion.py`: 12 tests -- first ingest
  creates, re-ingesting the same `source_ref` is a no-op, a different
  `source_ref` creates a new event, in-batch duplicate `source_ref`
  yields one creation, batch against prior existing events is
  idempotent, distinct records all created, and the gold case: a full
  re-import of an already-landed file creates nothing new. Correlation
  tests: picks the most recent matching-channel sent touchpoint,
  ignores a different channel, ignores a not-yet-sent touchpoint,
  ignores a touchpoint sent after the event, and returns `None` with no
  candidates.

## Evidence

`python -m unittest tests.test_engagement_ingestion -v`: 12/12 pass.
Full `python scripts/check_release.py`: 0 errors.
