---
name: person-opportunity-targeting
description: Select and rank private network contacts only after an existing company-product fit decision. Use when a qualified study has a recommended offer and the user wants initial sponsor, terrain-owner, technical-sponsor, veto or persona-overlap contact candidates, validation priorities, or a person-company-product target list. Do not research the company, change product fit, infer buying authority from a title, or decide the final first/second outreach wave.
---

# Person Opportunity Targeting

## Responsibility

Overlay private person records on an existing account × product match and create the **candidate contact layer**. Do not recompute the match and do not own the final stakeholder/reach sequence.

Read [persona-targeting-policy.md](references/persona-targeting-policy.md) before ranking contacts.

## Required inputs

- study manifest linked by `company_id`;
- `06_product_fit_matrix.yaml` whose top-level decision equals the selected `PURSUE` or `VALIDATE` match, with no failed blocker/critical gate and a canonical weighted score;
- selected immutable product snapshot;
- private person-company relationships.

## Procedure

1. Load the selected offer personas from its snapshot.
2. Load only relationships for the linked company.
3. Compare generic role hypotheses and title patterns with sponsor, terrain, technical and veto personas.
4. Rank targets while preserving current-role uncertainty and require a dated observation for a `current` role.
5. State validation required before outreach.
6. Write `06b_contact_targets.yaml` using opaque person IDs.
7. Hand the candidates to `iterative-reach-matchmaking` for promoter/prescriber/user/technical/veto role hypotheses, first/second wave sequencing, newsflow timing and coverage-gap resolution.

Run:

```bash
python scripts/target_study_contacts.py <study_dir>
```

## Iterative second-round handoff

This skill may return zero or incomplete target coverage. That is not a reason to infer authority or weaken the fit gates.

Downstream `iterative-reach-matchmaking` can identify a missing stakeholder lane and route back to:

- this skill for current-role validation or newly available private contacts;
- `tech-leadership-org-intelligence` for organization/decision-system expansion;
- human validation when provider/public evidence remains insufficient.

The first/second-wave decision belongs downstream because it can combine target evidence with org context, UC relevance and current newsflow. This skill stays focused on person-company-product eligibility and rank.

## Role-validation routing

When a role is stale or uncertain, follow this sequence:

1. if the host exposes an **approved read-only LinkedIn connector** and the `LI-G*` gates permit it, use that provider first;
2. if the provider is absent, refused, broken, rate-limited or inconclusive, run the public fallback:

```bash
python scripts/advanced_research.py "<personne> <entreprise> <fonction>" --source linkedin --days 730 --limit 8 --pretty
```

3. if the combined evidence still cannot establish role currency or identity, require an approved primary source or human validation.

Do **not** set a relationship to `current`, merge identities, infer authority, or mark outreach `ready` from a public-index result alone. Public discovery must not change company-product fit. The fallback exists to avoid losing useful research when the plugin is unavailable, not to bypass `LI-POL-*`.
