# Hotfix v0.7 — release gate

This hotfix is intentionally narrow. It fixes two blocker/resolver routing regressions discovered by the RC release gate:

1. a blocked company-demand step now reuses the qualification demand resolver;
2. direct Reach resolves fit/contact prerequisites before stakeholder-lane construction, so missing contacts route to `Cibler les contacts` and stale contact handoffs route to recalculation.

No product, evidence, matching or role-authority semantics are changed.
