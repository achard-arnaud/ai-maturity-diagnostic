# STOP — Epic 06 / Sprint S01

## Objective

Product/Version/Snapshot/Evidence schemas. Stop condition: "semantics
figées" (frozen semantics) -- schema/N-1 tests.

## Outputs

- `contracts/product_v1.schema.yaml`: `CanonicalProductV1`. Bare durable
  identity only -- no content field. `owner_scope` encodes ADR-008's
  shared-core-vs-workspace-overlay model (`kind: shared` with
  `workspace_id: null`, or `kind: workspace` with `workspace_id` set).
- `contracts/product_version_v1.schema.yaml`: `CanonicalProductVersionV1`.
  The mutable draft lifecycle object -- `status`
  (draft/in_review/published/superseded/archived), monotonically
  increasing `version_number` (never reused), and `published_snapshot_id`
  (set only once published).
- `contracts/product_snapshot_v1.schema.yaml`: `CanonicalProductSnapshotV1`.
  The one immutable, hashed, published artifact a version ever produces:
  `content` (name/description/exclusions/hard_gates/capabilities),
  `content_hash` (sha256 of the canonical content), `evidence_ids`
  (Epic 04 `CanonicalEvidenceV1` ids grounding the content -- reused, not
  duplicated), `supersedes_snapshot_id`. Structurally carries no
  fit/score field -- Fit (Epic 07) references a snapshot_id, never the
  reverse. Evidence never counts toward product truth by itself
  (this Epic's own invariant), it only grounds already-stated claims.
- `app/product_policy.py`:
  - `can_transition_version`: the version state machine
    (`draft <-> in_review -> published -> superseded`; `archived` and
    `superseded` are terminal).
  - `compute_content_hash`: deterministic sha256 over sorted-key JSON --
    same content always hashes identically regardless of key order.
  - `assert_snapshot_immutable(existing_snapshot, new_content)`: raises
    `SnapshotImmutabilityError` the instant new content would change what
    a given `snapshot_id` already publishes -- a snapshot can only be
    superseded by a *new* snapshot_id from a new ProductVersion, never
    edited in place.
  - `next_version_number`: monotonic, never reuses an archived version's
    number.
- `tests/test_product_policy.py`: 16 tests -- the version transition
  table (including the two terminal states); hash determinism (same
  content same hash regardless of key order, different content different
  hash); immutability (identical content accepted, changed content
  rejected); the Sprint's own N-1 gold case
  (`test_n_minus_1_snapshot_is_unaffected_by_a_new_publish`: publishing
  v2's snapshot never touches v1's already-published hash); version
  numbering (first is 1, next is one past the highest ever assigned, an
  archived version's number is never reused).

## Evidence

`python -m unittest tests.test_product_policy -v`: 16/16 pass.
Full `python scripts/check_release.py`: 0 errors.
