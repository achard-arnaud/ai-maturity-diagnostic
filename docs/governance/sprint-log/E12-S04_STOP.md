# STOP — Epic 12 / Sprint S04

Fit, Targets and Reach now read their workspace-scoped v1 APIs in the GTM
shell. Fit gates are rendered explicitly as pass/blocked badges; the client
does not infer or override them.

Evidence: `python -m unittest tests.test_gtm_decision_spaces -v`.
