# Privacy and entity-resolution policy

## Handling

- Classify contact batches as confidential.
- Keep raw and normalized person data under `data/private/`.
- Expose opaque person IDs, not names, in shareable study artifacts.
- Preserve source row and checksum for correction and deletion workflows.

## Resolution

- Normalize accents, casing, punctuation, and spacing for comparison.
- Merge punctuation variants of the same company label.
- Do not merge subsidiaries, brands, or business units into a parent without explicit evidence.
- Keep a repeated person name at two companies as two provisional employer-scoped identities until explicitly resolved.
- Treat a verified provider profile URL as an external alias, not as the canonical internal identifier.
- Preserve aliases and prior relationships rather than overwriting them.

## Epistemic boundary

The private file supports that the user supplied a person, title, company, and country. It does not establish:

- that the role is current;
- that the country is headquarters;
- that the person controls budget or a decision;
- that the company has a demonstrated need;
- that outreach is permitted or appropriate.
