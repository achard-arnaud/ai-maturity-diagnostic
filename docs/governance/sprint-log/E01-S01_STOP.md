# STOP — Epic 01 / Sprint S01

## Objective

Decide product catalog ownership through an ADR and executable architecture fixture.

## State

- Branch `epic/01-platform-transaction-execution`, based on Epic 00 release `2ec0ea2`.
- Tag `epic-01-s01-catalog-ownership`; integration base eventually `dev`.

## Outputs

- ADR-008 selects shared-core plus explicit workspace overlays.
- Contract and test prohibit silent shadowing and preserve immutable fit snapshots.

## Evidence

`test_catalog_ownership_contract_matches_adr ... ok`.

## Remaining

Projection implementation belongs to Epic 06.

## Commands to resume

```bash
git switch epic/01-platform-transaction-execution
python -m unittest tests.test_catalog_ownership_policy -v
```

## Risks / notes

Default workspace keeps the root catalog until the projection migration is deliberately implemented.
