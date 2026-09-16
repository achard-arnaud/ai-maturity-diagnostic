# STOP — Epic 11 / Sprint S04

## Objective

Define proof design, outcomes and success metrics. Stop condition: **"preuve
avant claim client"**.

## Outputs

- A proof requires at least one measurable target and a falsifier before it
  can run.
- An outcome is `met`, `not_met` or `inconclusive`; missing observation is
  never treated as success.
- Only a `met` outcome with evidence may support a client claim.

## Evidence

`python -m unittest tests.test_proof_policy -v`
