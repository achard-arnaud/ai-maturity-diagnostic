# STOP — Epic 11 / Sprint S03

## Objective

Add bounded, provenance-linked Discovery notes and an append-only commercial
decision log. Stop condition: **"notes bornées"**.

## Outputs

- Discovery notes are limited to 4,000 characters, source-linked and require
  `commercial_reviewer` or `admin` access.
- Commercial decisions are attributed, source-linked and require
  `commercial_decider` or `admin` access.
- Neither record type mutates Demand, Fit, TargetPlan or Engagement inputs.

## Evidence

`python -m unittest tests.test_opportunity_notes -v`

## Next

Sprint S04 defines Proof design, outcomes and success metrics.
