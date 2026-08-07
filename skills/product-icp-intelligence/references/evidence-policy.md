# Product evidence policy

## Evidence classes

- Grade direct product documentation, a live system, or a transcript showing a capability as `P1` or `P2` depending on completeness.
- Grade product-owner direction as `U1`.
- Grade external market research as `W1`.
- Grade an unsupported assumption as `N0`.

Record `epistemic_status` independently from `evidence_grade`.

```yaml
statement: "Astraforge provides controlled agent execution"
epistemic_status: inference
evidence_grade: P2
```

Do not claim exact technologies, certifications, SLAs, pricing, savings, customer outcomes, or deployed environments without direct primary evidence. Preserve contrary evidence and explicit unknowns.

Only the owner skill or explicit human validation may strengthen a product claim. Increment the product profile version when a strengthened or weakened claim changes fit decisions.
