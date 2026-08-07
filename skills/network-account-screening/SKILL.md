---
name: network-account-screening
description: Prioritize companies in a private contact network for research using access coverage, seniority signals, AI and data proximity, delivery proximity, role diversity, and classification readiness. Use for theoretical network ICP tiers, research queues, or deciding which accounts to investigate first. Do not claim demonstrated demand, product fit, maturity, budget, urgency, or authority from this screening score.
---

# Network Account Screening

## Responsibility

Create a product-agnostic research prior from the contact network. Keep it distinct from the observed enterprise demand profile and every product ICP.

Read [scoring-model.md](references/scoring-model.md) before interpreting scores.

## Procedure

1. Load canonical companies and relationships.
2. Count access and role-family signals without treating titles as authority.
3. Score only research attractiveness and likely discovery coverage.
4. Assign tier `A | B | C | D` and confidence.
5. Preserve the standard limitations in every record.
6. Feed tiers A and B into `network-study-orchestration`.

Run:

```bash
python scripts/screen_network_accounts.py
```

Write `data/private/network/account_screening.jsonl`.
