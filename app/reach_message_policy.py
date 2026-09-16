"""Epic 09 S02: message evidence binding, templates and approval.

Stop condition: "claims sourcés" (claims are sourced) -- every citation a
message makes to a factual claim must name an existing, currently
*active* Claim (Epic 04), and must quote that claim's own statement
verbatim -- never a paraphrase or an embellishment. A message can carry
zero citations (e.g. a pure scheduling note), but any citation it does
carry must check out exactly.
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence

REVIEW_ROLE = "reach_reviewer"


class ReachMessagePolicyError(Exception):
    pass


class CitationError(ReachMessagePolicyError):
    pass


class MessageAuthorizationError(ReachMessagePolicyError):
    pass


def draft_message(*, content: str, citations: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    return {"content": content, "citations": list(citations), "status": "draft"}


def validate_citations(citations: Sequence[Mapping[str, Any]], claims_by_id: Mapping[str, Mapping[str, Any]]) -> None:
    """Every citation must name an existing, active claim, and its
    quoted_text must appear verbatim in that claim's own statement --
    never invented or embellished beyond what the claim actually says."""
    for citation in citations:
        claim_id = citation["claim_id"]
        claim = claims_by_id.get(claim_id)
        if claim is None:
            raise CitationError(f"citation references unknown claim {claim_id!r}")
        if claim["status"] != "active":
            raise CitationError(f"citation references a non-active claim {claim_id!r} (status={claim['status']!r})")
        quoted_text = citation["quoted_text"]
        if quoted_text not in claim["statement"]:
            raise CitationError(
                f"citation quoted_text {quoted_text!r} is not verbatim in claim {claim_id!r}'s statement -- "
                "a citation can never embellish or paraphrase beyond the sourced claim"
            )


def approve_message(
    message: Mapping[str, Any], *, claims_by_id: Mapping[str, Mapping[str, Any]], actor_role: str | None
) -> dict[str, Any]:
    if actor_role != REVIEW_ROLE:
        raise MessageAuthorizationError(f"approving a message requires the {REVIEW_ROLE!r} role; got {actor_role!r}")
    validate_citations(message["citations"], claims_by_id)
    updated = dict(message)
    updated["status"] = "approved"
    return updated
