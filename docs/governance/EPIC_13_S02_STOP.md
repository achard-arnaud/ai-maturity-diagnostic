# Epic 13 S02 stop condition

Funnel, quality and cost are replayed from the same explicit event cohort.
The projection carries a source count and deterministic digest, is invariant to
input ordering, and can be reconciled by a complete rebuild. It declares
`authoritative: false`; source events remain unchanged.
