from __future__ import annotations

import unittest

from app.demand_mapping import map_from_enterprise_profile
from app.demand_policy import DemandContaminationError, assert_no_product_fields, count_unknowns, is_complete


def _profile(**kwargs) -> dict:
    base = {
        "schema_version": "0.2",
        "study_id": "acme-20260101",
        "company": "Acme",
        "evidence_claims": [{"claim_id": "E1", "statement": "manual process for onboarding", "evidence_status": "hypothesis"}],
        "capability_gaps": [],
        "buying_context": {"sponsors": [], "terrain_owners": [], "veto_players": [], "timing_signals": []},
        "constraints": {"technical": [], "organizational": [], "regulatory": []},
        "unknowns": [],
        "confidence": "low",
    }
    base.update(kwargs)
    return base


def _map(profile: dict) -> dict:
    return map_from_enterprise_profile(
        profile,
        demand_id="d1",
        workspace_id="ws-a",
        company_entity_id="entity_1",
        origin_profile_ref="studies/acme-20260101/05_enterprise_demand_profile.yaml",
        created_at="2026-01-01T00:00:00+00:00",
        updated_at="2026-01-01T00:00:00+00:00",
    )


class MappingParityTests(unittest.TestCase):
    def test_problem_statement_is_carried_over_verbatim(self) -> None:
        demand = _map(_profile())
        self.assertTrue(demand["problem"]["known"])
        self.assertEqual("manual process for onboarding", demand["problem"]["value"])

    def test_missing_problem_statement_is_unknown(self) -> None:
        demand = _map(_profile(evidence_claims=[]))
        self.assertFalse(demand["problem"]["known"])
        self.assertIsNone(demand["problem"]["value"])

    def test_capability_gaps_map_to_impact(self) -> None:
        demand = _map(_profile(capability_gaps=["no CRM integration", "manual reporting"]))
        self.assertTrue(demand["impact"]["known"])
        self.assertIn("no CRM integration", demand["impact"]["value"])

    def test_empty_capability_gaps_is_unknown_impact(self) -> None:
        demand = _map(_profile(capability_gaps=[]))
        self.assertFalse(demand["impact"]["known"])

    def test_sponsors_map_to_sponsor_field(self) -> None:
        profile = _profile(buying_context={"sponsors": ["VP Sales"], "terrain_owners": [], "veto_players": [], "timing_signals": []})
        demand = _map(profile)
        self.assertTrue(demand["sponsor"]["known"])
        self.assertIn("VP Sales", demand["sponsor"]["value"])

    def test_timing_signals_map_to_timing_field(self) -> None:
        profile = _profile(buying_context={"sponsors": [], "terrain_owners": [], "veto_players": [], "timing_signals": ["renewal in Q3"]})
        demand = _map(profile)
        self.assertTrue(demand["timing"]["known"])
        self.assertIn("renewal in Q3", demand["timing"]["value"])

    def test_fields_with_no_legacy_source_are_explicit_unknowns(self) -> None:
        demand = _map(_profile())
        for field in ("population", "urgency", "initiative", "budget"):
            self.assertFalse(demand[field]["known"], f"{field} should be an explicit unknown")
            self.assertIsNone(demand[field]["value"])

    def test_origin_profile_ref_is_preserved(self) -> None:
        demand = _map(_profile())
        self.assertEqual("studies/acme-20260101/05_enterprise_demand_profile.yaml", demand["origin_profile_ref"])

    def test_status_starts_observed(self) -> None:
        demand = _map(_profile())
        self.assertEqual("observed", demand["status"])


class DemandPolicyTests(unittest.TestCase):
    def test_no_contamination_passes(self) -> None:
        demand = _map(_profile())
        assert_no_product_fields(demand)  # should not raise

    def test_contaminated_value_is_flagged(self) -> None:
        demand = _map(_profile())
        demand["problem"]["value"] = "great fit for our product catalog"
        with self.assertRaises(DemandContaminationError):
            assert_no_product_fields(demand)

    def test_is_complete_requires_known_problem(self) -> None:
        complete = _map(_profile())
        self.assertTrue(is_complete(complete))
        incomplete = _map(_profile(evidence_claims=[]))
        self.assertFalse(is_complete(incomplete))

    def test_count_unknowns(self) -> None:
        # Default profile has no capability_gaps/sponsors/timing_signals,
        # so only "problem" is known -- the other 7 dimensions unknown.
        demand = _map(_profile())
        self.assertEqual(7, count_unknowns(demand))

    def test_count_unknowns_drops_as_fields_become_known(self) -> None:
        profile = _profile(
            capability_gaps=["no CRM integration"],
            buying_context={"sponsors": ["VP Sales"], "terrain_owners": [], "veto_players": [], "timing_signals": ["renewal in Q3"]},
        )
        demand = _map(profile)
        # problem, impact, sponsor, timing known -> 4 remaining unknowns.
        self.assertEqual(4, count_unknowns(demand))


if __name__ == "__main__":
    unittest.main()
