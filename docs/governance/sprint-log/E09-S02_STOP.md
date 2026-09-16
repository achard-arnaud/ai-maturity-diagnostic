# STOP — Epic 09 / Sprint S02

## Objective

Message evidence binding, templates et approval. Stop condition:
"claims sourcés" (claims are sourced) -- a message may cite zero or
more Claims (Epic 04), but every citation it does carry must name an
existing, currently *active* claim and quote that claim's own
`statement` verbatim -- never a paraphrase or an embellishment.

## Outputs

- `app/reach_message_policy.py`:
  - `REVIEW_ROLE = "reach_reviewer"`.
  - `draft_message(content, citations)`: creates a message in
    `status="draft"`, never pre-approved.
  - `validate_citations(citations, claims_by_id)`: the sole choke point
    -- raises `CitationError` if a citation references an unknown
    claim, a non-`active` claim (e.g. superseded), or a `quoted_text`
    that is not a verbatim substring of the claim's `statement`. Zero
    citations is always valid.
  - `approve_message(message, claims_by_id, actor_role)`: RBAC-gated to
    `reach_reviewer`; even with the correct role, an invalid citation
    still blocks approval (no role can bypass sourcing) -- calls
    `validate_citations` before setting `status="approved"`.
- `tests/test_reach_message_policy.py`: 10 tests -- no-citations valid,
  valid verbatim citation, unknown-claim rejected, superseded-claim
  rejected, the embellishment gold case (quoted text goes beyond what
  the claim actually states) rejected, multiple citations all
  validated, approval requires reviewer role, approval succeeds with
  valid citations and role, approval rejects an invalid citation even
  with the correct role, approval with no citations is allowed.

## Evidence

`python -m unittest tests.test_reach_message_policy -v`: 10/10 pass.
Full `python scripts/check_release.py`: 0 errors.
