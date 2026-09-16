from __future__ import annotations

import unittest

from app.demand_resolver import resolve_qualification_blocker
from app.demand_policy import known, unknown


def _demand(**kwargs) -> dict:
    base = {
        "demand_id": "d1",
        "workspace_id": "ws-a",
        "company_entity_id": "entity_1",
        "status": "qualifying",
        "problem": known("manual onboarding"),
        "population": unknown(),
        "impact": unknown(),
        "urgency": unknown(),
        "initiative": unknown(),
        "sponsor": known("VP Sales"),
        "budget": unknown(),
        "timing": unknown(),
        "claim_ids": [],
        "origin_profile_ref": None,
        "created_at": "2026-01-01T00:00:00+00:00",
        "updated_at": "2026-01-01T00:00:00+00:00",
    }
    base.update(kwargs)
    return base


class ResolverTests(unittest.TestCase):
    def test_passing_checklist_returns_none(self) -> None:
        self.assertIsNone(resolve_qualification_blocker(_demand()))

    def test_failing_checklist_returns_full_contract(self) -> None:
        contract = resolve_qualification_blocker(_demand(problem=unknown()))
        self.assertIsNotNone(contract)
        self.assertIn("problem", contract.why_blocked)
        self.assertTrue(contract.required_state_or_evidence)
        self.assertEqual("demand_owner", contract.owner_capability)
        self.assertTrue(contract.cta)
        self.assertTrue(contract.postcondition)
        self.assertTrue(contract.cost_estimate)
        self.assertIsNone(contract.expiry)

    def test_missing_buying_signal_is_named_in_contract(self) -> None:
        contract = resolve_qualification_blocker(_demand(sponsor=unknown()))
        self.assertIn("buying signal", contract.why_blocked)


if __name__ == "__main__":
    unittest.main()
