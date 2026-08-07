---
name: person-opportunity-targeting
description: Select and rank private network contacts only after an existing company-product fit decision. Use when a qualified study has a recommended offer and the user wants likely sponsor, terrain-owner, technical-sponsor, or veto contacts, persona overlap, validation priorities, or a person-company-product target list. Do not research the company, change product fit, or infer buying authority from a title.
---

# Person Opportunity Targeting

## Responsibility

Overlay private person records on an existing account × product match. Do not recompute the match.

Read [persona-targeting-policy.md](references/persona-targeting-policy.md) before ranking contacts.

## Required inputs

- study manifest linked by `company_id`;
- `06_product_fit_matrix.yaml` whose top-level decision equals the selected `PURSUE` or `VALIDATE` match, with no failed blocker/critical gate and a canonical weighted score;
- selected immutable product snapshot;
- private person-company relationships.

## Procedure

1. Load the selected offer personas from its snapshot.
2. Load only relationships for the linked company.
3. Compare generic role hypotheses and title patterns with sponsor, terrain, and veto personas.
4. Rank targets while preserving current-role uncertainty and require a dated observation for a `current` role.
5. State validation required before outreach.
6. Write `06b_contact_targets.yaml` using opaque person IDs.

Run:

```bash
python scripts/target_study_contacts.py <study_dir>
```
