from __future__ import annotations

import unittest

from app.engagement_opportunity import propose_opportunity


def _event(kind: str) -> dict:
    return {"engagement_event_id": "ee1", "conversation_id": "c1", "kind": kind}


class ProposeOpportunityTests(unittest.TestCase):
    def test_meeting_booked_proposes_an_opportunity(self) -> None:
        proposal = propose_opportunity(_event("meeting_booked"))
        self.assertIsNotNone(proposal)
        self.assertEqual("proposed", proposal["status"])
        self.assertEqual("c1", proposal["conversation_id"])

    def test_replied_proposes_nothing(self) -> None:
        self.assertIsNone(propose_opportunity(_event("replied")))

    def test_opted_out_proposes_nothing(self) -> None:
        self.assertIsNone(propose_opportunity(_event("opted_out")))

    def test_bounced_proposes_nothing(self) -> None:
        self.assertIsNone(propose_opportunity(_event("bounced")))


if __name__ == "__main__":
    unittest.main()
