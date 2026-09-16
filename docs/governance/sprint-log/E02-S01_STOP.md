# STOP — Epic 02 / Sprint S01

## Objective

Schémas v1 Person/Company/Relationship/ExternalIdentity. Stop condition:
"contrats figés" (contracts frozen).

## State

- Sprint branch: `claude/peaceful-wozniak-8yqv32`, forked from `origin/main`
  (Epic 01 released, `dev == main` at `5766647`).
- Base branch for the PR: `dev`.

## Outputs

- `docs/ADR-009-canonical-identity-model.md`: the identity-model decision —
  an additive `entity_id` + `legacy_ids` v1 projection, not a rewrite of the
  legacy v0.3 contracts/writers. Explains why (avoids a big-bang rewrite
  across 35 existing tests) and what it fixes (person_id/company_id today
  are deterministic hashes over the identity key, not immutable — a person
  changing employer silently orphans their old ID with no linkage).
- `contracts/{person,company,relationship}_v1.schema.yaml`: new, strict
  JSON-Schema (`$schema` draft/2020-12) contracts with `entity_id`,
  `legacy_ids`, required `workspace_id`, `valid_from`/`valid_to`, and a
  structured `provenance` object.
- `contracts/external_identity_mapping.schema.yaml`: bumped to
  `schema_version: "1.0"` and reused as-is (already models exactly the
  alias relationship Epic 02 needs; had no implementation to break).
- `app/network_identity_v1.py`: schema loader + three pure adapter
  functions (`person_v0_3_to_v1`, `company_v0_3_to_v1`,
  `relationship_v0_3_to_v1`) proving a legacy record maps losslessly
  forward. No legacy writer is touched.
- `tests/test_network_identity_v1.py`: 11 tests — each v1 schema is a
  valid JSON Schema (schema test), each adapter's output validates against
  its v1 schema (property test), no legacy field is lost, and a person
  keeps the same `entity_id` even after their identity-key basis (company)
  changes (the specific gap this Sprint targets).

## Evidence

- `python -m unittest tests.test_network_identity_v1 -v`: 11/11 pass.
- Full `python scripts/check_release.py`: see PR for the run captured
  right before merge (must be 0 errors; new v1 schema files are
  meta-validated by the release gate's own YAML/JSON-Schema check since
  they carry a real `$schema`).

## Remaining (owned by later Sprints)

- S02: temporal currentness policy (`app/network_temporal.py`) reasoning
  over `valid_from`/`valid_to` + `current_status` together.
- S03: identity resolution/dedup proposals — the actual process that
  assigns `entity_id`s and grows `legacy_ids`, building on
  `network_index.find_potential_duplicates` (detection-only today) plus a
  new human-audited, reversible merge record.
- S04: `/api/v1/workspaces/{workspace_id}/{people,companies,relationships}`
  read models over the v1 shape.
- S05: Person 360 / Account 360 composed with visible provenance.
- S06: legacy→v1 migration/backfill/reconciliation (dry-run, hashes,
  parity, rollback) — this is where `entity_id`s actually get assigned to
  every existing legacy record for the first time.

## Commands to resume

```bash
git checkout claude/peaceful-wozniak-8yqv32
python -m pip install -e '.[docs,dev]'
python -m unittest tests.test_network_identity_v1 -v
python scripts/check_release.py
```

## Risks / notes

- No v1 records exist anywhere yet — this Sprint is contracts + adapters
  only, deliberately, per the stop condition ("contrats figés", not "data
  migrated").
- `relationship_v1`'s `relationship_entity_id` reuses the legacy
  `relationship_id` unchanged (relationships aren't dedup targets in this
  Epic — person/company are); flagged here in case a later Sprint decides
  relationships need their own independent entity_id lifecycle too.
