# ADR-009 — Canonical Identity Model for Person/Company/Relationship (Epic 02 S01)

## Status

Accepted.

## Context

The legacy contracts (`contracts/person.schema.yaml`, `company.schema.yaml`,
`relationship.schema.yaml`, all `schema_version: "0.3"`) generate IDs via
`stable_id(prefix, *values)` (`scripts/network_common.py`): a deterministic
hash over identity-key fields (person: normalized name + seed company;
company: normalized name). This means:

- A person changing employer gets a brand-new `person_id` under the new
  company; the old `person_id` is silently orphaned with no linkage between
  the two. There is no merge trail.
- "Stable" today means "deterministic from the current identity key," not
  "persists across identity-key changes" — the opposite of what Epic 02's
  target state requires ("Personnes, entreprises... possèdent IDs stables").
- Company has an optional, nullable `workspace_id` (1:1, coalesced to
  `"default"` by readers); Person has none, derived transitively.
- Neither contract has a temporal validity interval — only `last_updated` +
  `stale_after_months` (a staleness heuristic) and, on Relationship,
  `current_status` (a state enum) + `observed_at` (a single nullable point).

Rewriting the legacy contracts and their writers (`app/network_writer.py`,
`app/network_index.py`, `scripts/import_contacts.py`) in place would touch
~35 existing tests and every route that reads `/api/network/*`, for a wedge
of behavior (dedup, merge, temporal validity) that Epic 02's own sprint plan
spreads across S01-S06. That is exactly the "big-bang artefacts + API +
frontend dans un même Sprint" the migration playbook
(`docs/gtm-transformation/11_MIGRATION_COMPATIBILITY_AND_ROLLBACK.md`) rules
out.

## Decision

Introduce a **v1 canonical projection** additive to the legacy contracts,
not a replacement:

1. New contracts `contracts/{person,company,relationship}_v1.schema.yaml`
   define an `entity_id` (assigned once, e.g. `ArtifactStore.new_id()`,
   never recomputed from name/company fields) plus a `legacy_ids` array
   linking every legacy `person_id`/`company_id`/`relationship_id` that
   resolves to that canonical identity. A person who changes employer keeps
   the same `entity_id`; the old and new legacy IDs both appear in
   `legacy_ids` once linked by an explicit resolution step (Epic 02 S03).
2. `workspace_id` is **required** on `CanonicalCompanyV1` (not nullable) —
   the v1 projection never needs the `"default"` coalescing the legacy
   reader does.
3. Temporal validity is real: `valid_from`/`valid_to` on all three v1
   contracts, plus `CanonicalRelationshipV1.current_status` interpreted
   together with the interval (a relationship with `valid_to` in the past
   is not current regardless of `current_status` — see
   `app/network_temporal.py`, Epic 02 S02).
4. `merged_into_entity_id` + `status: merged/superseded` replace ad hoc
   deletion for identity resolution (Epic 02 S03): merging never deletes a
   record, it marks the losing side and points at the survivor.
5. Legacy writers (`network_writer.py`, `import_contacts.py`, and the
   `/api/network/*` routes) are **unchanged** by this Sprint. They keep
   writing v0.3 records exactly as today. The v1 projection is built by a
   read-side adapter (Epic 02 S06 does the bulk backfill/reconciliation;
   this Sprint only proves the contract with a schema/property test and an
   N-1 reader test that a v0.3 record can be losslessly mapped forward).
6. `contracts/external_identity_mapping.schema.yaml` already models exactly
   the alias-only relationship Epic 02 needs (`internal_entity_id` +
   `external_subject_ref`, "never replace internal IDs") and has no
   implementation yet, so it is reused as-is for v1 (bumped to
   `schema_version: "1.0"` in this Sprint) rather than duplicated.

## Consequences

- No legacy test breaks in this Sprint: nothing that already reads or
  writes v0.3 records changes.
- Epic 02 S02-S06 build the temporal-currentness policy, the dedup/merge
  resolution flow, the `/api/v1/...` read models, composed 360 views, and
  the legacy→v1 migration/reconciliation on top of these frozen contracts,
  in that order.
- Until S06's migration runs, no v1 records exist yet in any workspace;
  `entity_id`/`legacy_ids` are contracts to build against, not yet
  populated data. This is intentional and matches the Sprint 1 stop
  condition ("contrats figés", not "data migrated").

## Alternatives considered

- **Mutate `person_id`/`company_id` in place to be immutable UUIDs.**
  Rejected: breaks every existing writer/reader and the 35 tests covering
  them in one Sprint, for no test coverage of the new dedup/temporal
  behavior yet — pure risk with no offsetting Sprint 1 benefit.
- **Skip `legacy_ids` and rely on `external_identity_mapping` for the
  legacy↔canonical link too.** Rejected: that contract is explicitly for
  *external* provider identifiers (`x-rules`: "never replace internal
  IDs"); overloading it for internal legacy-ID linkage would blur a
  deliberately narrow contract.
