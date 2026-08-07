# Fit scoring

Score each dimension from 0 to 5 only after the gates.

| Dimension | Weight |
|---|---:|
| Problem fit | 20 |
| Strategic relevance | 15 |
| Capability-gap fit | 15 |
| Urgency and timing | 10 |
| Technical fit | 10 |
| Organizational fit | 10 |
| Sponsor and terrain access | 10 |
| Proofability | 5 |
| Evidence confidence | 5 |

Calculate:

```text
weighted score = sum(dimension score / 5 * dimension weight)
```

Interpret only after gate consequences:

- 80–100: strong conditional fit;
- 65–79: plausible fit requiring validation;
- 45–64: weak, nurture, or alternative likely better;
- below 45: poor fit.

Explain each dimension with account claim IDs and product claim or gate IDs. Recalculate sensitivity after changing the two most decision-relevant unknowns. Use `null` when structural disqualification makes a score misleading.
