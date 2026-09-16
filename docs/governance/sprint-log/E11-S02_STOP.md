# STOP — Epic 11 / Sprint S02

## Objective

Make qualification, conversion and Opportunity stages explicit. The stop
condition is **"aucun stage skip"**: a transition is adjacent and has all of
its declared exit criteria, or it is refused.

## Outputs

- Qualification requires a `PURSUE` fit, an active TargetPlan and a
  `meeting_booked` EngagementEvent.
- Conversion is distinct from qualification and does not create an
  Opportunity implicitly.
- `draft → discovery → proof → proposal → won/lost` is the sole transition
  graph; every destination has named exit criteria.

## Evidence

`python -m unittest tests.test_opportunity_lifecycle -v`

## Next

Sprint S03 will attach bounded discovery and decision records to this
lifecycle without altering upstream evidence.
