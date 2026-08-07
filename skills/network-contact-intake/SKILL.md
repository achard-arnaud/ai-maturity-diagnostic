---
name: network-contact-intake
description: Import and normalize a private contact file into canonical people, companies, and person-company relationships. Use when the user adds a network list, contact export, attendee file, or CRM-like table and wants entity IDs, deduplication, role hypotheses, provenance, privacy controls, or propagation to company records. Do not infer company demand, ICB truth, product fit, or buying authority.
---

# Network Contact Intake

## Responsibility

Create stable network objects from a private input batch while preserving the raw file and uncertainty about identity, role currency, and authority.

Read [privacy-and-resolution-policy.md](references/privacy-and-resolution-policy.md) before importing personally identifiable data.

## Procedure

1. Verify the input columns and record an immutable batch checksum.
2. Normalize text without discarding the original values.
3. Seed a provisional person ID from normalized name plus supplied company; create stable company and relationship IDs.
4. Merge only exact normalized name-and-company seeds; flag every person identity for validation.
5. Treat job titles as user-provided facts but current employment and influence as unverified.
6. Infer generic role hypotheses without assigning budget or authority.
7. Write the private canonical registries and batch manifest.
8. Run `python scripts/validate_network.py` after ICB mapping and screening.

Use:

```bash
python scripts/import_contacts.py <contacts.tsv> --batch-date <YYYY-MM-DD>
```

## Outputs

Write under `data/private/`:

- `intake_batches/<batch_id>/manifest.yaml` and immutable raw snapshot;
- `network/people.jsonl`;
- `network/companies.jsonl`;
- `network/relationships.jsonl`.

Never copy names into public reports or treat the import date as proof that a role is current.

The employer-scoped person key is transitional. A future verified LinkedIn URL or other provider identity is an external alias used by an explicit resolution/merge process; it never becomes `person_id` directly.
