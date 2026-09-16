from __future__ import annotations

import unittest

from app.reach_message_policy import (
    CitationError,
    MessageAuthorizationError,
    approve_message,
    draft_message,
    validate_citations,
)


def _claim(claim_id: str, statement: str, status: str = "active") -> dict:
    return {"claim_id": claim_id, "statement": statement, "status": status}


class ValidateCitationsTests(unittest.TestCase):
    def test_no_citations_is_valid(self) -> None:
        validate_citations([], {})  # should not raise

    def test_valid_citation_quoting_exact_claim_text(self) -> None:
        citations = [{"claim_id": "c1", "quoted_text": "raised a Series B"}]
        claims = {"c1": _claim("c1", "the company raised a Series B in 2025")}
        validate_citations(citations, claims)  # should not raise

    def test_citation_to_unknown_claim_rejected(self) -> None:
        citations = [{"claim_id": "missing", "quoted_text": "anything"}]
        with self.assertRaises(CitationError):
            validate_citations(citations, {})

    def test_citation_to_superseded_claim_rejected(self) -> None:
        citations = [{"claim_id": "c1", "quoted_text": "raised a Series B"}]
        claims = {"c1": _claim("c1", "the company raised a Series B in 2025", status="superseded")}
        with self.assertRaises(CitationError):
            validate_citations(citations, claims)

    def test_citation_quoting_text_not_in_claim_is_rejected(self) -> None:
        # Gold case: the citation embellishes beyond what the claim
        # actually states -- must be rejected, never silently accepted.
        citations = [{"claim_id": "c1", "quoted_text": "raised a massive Series C round"}]
        claims = {"c1": _claim("c1", "the company raised a Series B in 2025")}
        with self.assertRaises(CitationError):
            validate_citations(citations, claims)

    def test_multiple_citations_all_validated(self) -> None:
        citations = [
            {"claim_id": "c1", "quoted_text": "Series B"},
            {"claim_id": "c2", "quoted_text": "no CRM integration"},
        ]
        claims = {
            "c1": _claim("c1", "raised a Series B in 2025"),
            "c2": _claim("c2", "no CRM integration exists today"),
        }
        validate_citations(citations, claims)  # should not raise


class ApproveMessageTests(unittest.TestCase):
    def test_approve_requires_reviewer_role(self) -> None:
        message = draft_message(content="Hi there", citations=[])
        with self.assertRaises(MessageAuthorizationError):
            approve_message(message, claims_by_id={}, actor_role="standard_user")

    def test_approve_succeeds_with_valid_citations_and_role(self) -> None:
        citations = [{"claim_id": "c1", "quoted_text": "Series B"}]
        claims = {"c1": _claim("c1", "raised a Series B in 2025")}
        message = draft_message(content="Congrats on your Series B!", citations=citations)
        approved = approve_message(message, claims_by_id=claims, actor_role="reach_reviewer")
        self.assertEqual("approved", approved["status"])

    def test_approve_rejects_invalid_citation_even_with_correct_role(self) -> None:
        citations = [{"claim_id": "c1", "quoted_text": "raised a huge Series Z"}]
        claims = {"c1": _claim("c1", "raised a Series B in 2025")}
        message = draft_message(content="Congrats!", citations=citations)
        with self.assertRaises(CitationError):
            approve_message(message, claims_by_id=claims, actor_role="reach_reviewer")

    def test_approve_with_no_citations_is_allowed(self) -> None:
        message = draft_message(content="Just checking in.", citations=[])
        approved = approve_message(message, claims_by_id={}, actor_role="reach_reviewer")
        self.assertEqual("approved", approved["status"])


if __name__ == "__main__":
    unittest.main()
