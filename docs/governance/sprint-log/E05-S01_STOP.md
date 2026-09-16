# STOP — Epic 05 / Sprint S01

## Objective

Demand schema v1 + mapping depuis profils/use cases. Stop condition:
"objet non contaminé" (object not contaminated) -- migration parity
tests.

## Outputs

- `contracts/demand_v1.schema.yaml`: `CanonicalDemandV1`. Per this
  Epic's target state, carries 8 "knowable" dimensions (`problem`,
  `population`, `impact`, `urgency`, `initiative`, `sponsor`, `budget`,
  `timing`), each a `{known: bool, value: string|null}` pair -- an
  unset dimension is a visible, typed unknown (`known: false, value:
  null`), never a silently-omitted field or a guessed default.
  `claim_ids` links to Epic 04's `CanonicalClaimV1` for provenance.
  Structurally carries **no** product/catalog/fit/targeting field
  anywhere -- this Epic's own invariant ("Demand indépendante du
  catalogue ; fit et ciblage interdits dans ce contexte").
- `app/demand_policy.py`: `known(value)`/`unknown()` constructors;
  `assert_no_product_fields(data)` -- a runtime contamination guard
  mirroring Epic 03's `signal_policy.assert_no_demand_fields`, scanning
  both field names and knowable-field values for banned vocabulary;
  `is_complete` (true once `problem` is known -- the one load-bearing
  dimension); `count_unknowns`.
- `app/demand_mapping.py`: `map_from_enterprise_profile(profile, ...)`
  migrates a legacy `05_enterprise_demand_profile.yaml`
  (`app.demand.DemandCatalog`) onto a v1 Demand. Migration parity
  discipline: `evidence_claims[0].statement` -> `problem` verbatim;
  `capability_gaps` -> `impact` (joined, never reworded);
  `buying_context.sponsors` -> `sponsor`; `buying_context.timing_signals`
  -> `timing`. Every dimension with no legacy source (`population`,
  `urgency`, `initiative`, `budget`) stays an explicit unknown -- never
  inferred from adjacent legacy data, mirroring
  `app.demand.create_demand_profile`'s own "honest empty entry, never a
  guess" discipline in the other direction.
- `tests/test_demand_mapping.py`: 14 tests -- parity for each mapped
  dimension (present and absent-legacy-data cases), the four
  no-legacy-source dimensions are always unknown, `origin_profile_ref`
  preserved, initial `status` is `observed`; the contamination guard
  passes clean data and rejects a value carrying banned vocabulary;
  completeness and unknown-count helpers.

## Evidence

`python -m unittest tests.test_demand_mapping -v`: 14/14 pass.
Full `python scripts/check_release.py`: 0 errors.
