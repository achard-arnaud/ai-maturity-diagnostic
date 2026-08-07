# Source policy

## Priority

1. Use primary corporate sources: filings, annual reports, investor materials, official strategy, leadership pages, engineering documentation, and job postings.
2. Use primary external sources: regulators, procurement records, and official partner announcements.
3. Use reliable press and specialist publications for corroboration or challenge.
4. Use community, employee, and customer sources only as directional evidence.

## Required source and claim metadata

Capture:

- stable source and claim IDs;
- source type and URL or path;
- publication, event, observation, and consultation dates when distinct;
- exact excerpt or precise support;
- `epistemic_status`: `fact | inference | hypothesis | unknown`;
- `evidence_grade`: `P1 | P2 | U1 | W1 | N0`;
- confidence and rationale;
- contradiction links.

## Evidence grades

- `P1`: direct primary evidence supporting the claim.
- `P2`: partial primary evidence requiring reconstruction.
- `U1`: owner or user-provided fact or direction.
- `W1`: secondary web evidence.
- `N0`: not evidenced or unknown.

Never upgrade `P2`, `U1`, or `W1` to `P1` without new direct primary evidence. Preserve counter-evidence and access limitations. Write `Non établi` when support is insufficient.
