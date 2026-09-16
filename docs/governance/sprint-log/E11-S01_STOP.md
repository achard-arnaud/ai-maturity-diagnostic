# STOP — Epic 11 / Sprint S01

## Objective

Introduce canonical Lead, Opportunity, Proof, Deal and Expansion contracts.
The stop condition is **"prospect ≠ opportunity"**: raw prospects have no
Opportunity representation, and an Opportunity preserves the qualified
Lead's Demand/Fit/TargetPlan lineage.

## Outputs

- Five closed JSON-schema contracts under `contracts/`.
- `app.opportunity_policy` validates a same-workspace commercial chain and
  rejects unqualified Lead conversion or rewritten upstream links.
- `tests/test_opportunity_contracts.py` covers schema validity, link
  integrity, upstream lineage and the raw-prospect rejection case.

## Evidence

`python -m unittest tests.test_opportunity_contracts -v`

## Next

Sprint S02 owns transition policy and exit criteria; this sprint deliberately
does not authorize any stage transition.
