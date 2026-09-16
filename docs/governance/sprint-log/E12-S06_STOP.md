# STOP — Epic 12 / Sprint S06

The GTM shell emits navigation telemetry, marks the active space with
`aria-current`, restores visible keyboard focus, and provides a 44px-touch
mobile layout. `?legacy=1` is the one-release rollback flag; legacy panels
remain present but are removed from primary navigation.

Evidence: `python -m unittest tests.test_gtm_shell_quality -v` plus the full
release gate.
