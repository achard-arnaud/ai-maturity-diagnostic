# STOP — Epic 11 / Sprint S05

## Objective

Expose stable workspace-scoped Pipeline reads. Stop condition: **"projections
stables"**.

## Outputs

- Atomic Opportunity persistence with deterministic list pagination.
- IDOR-safe `GET /opportunities`, detail and Pipeline-board endpoints.
- The board contains every canonical stage (including empty stages), sorted
  deterministically, and is only a projection of Opportunity records.

## Evidence

`python -m unittest tests.test_opportunity_store -v`
