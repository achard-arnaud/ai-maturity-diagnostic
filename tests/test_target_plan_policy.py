from __future__ import annotations

import unittest

from app.target_plan_policy import (
    RoleCardinalityError,
    TargetPlanPolicyError,
    assign_stakeholder_role,
    supersede_stakeholder_role,
    validate_role_cardinality,
)


def _role(role: str, title: str = "Manager", status: str = "active", stakeholder_role_id: str = "sr1") -> dict:
    return assign_stakeholder_role(
        stakeholder_role_id=stakeholder_role_id, target_plan_id="tp1", person_entity_id="entity_1",
        role=role, title=title, assigned_by="alice", assigned_at="2026-01-01T00:00:00+00:00",
    ) | {"status": status}


class AssignStakeholderRoleTests(unittest.TestCase):
    def test_unknown_role_rejected(self) -> None:
        with self.assertRaises(TargetPlanPolicyError):
            assign_stakeholder_role(
                stakeholder_role_id="sr1", target_plan_id="tp1", person_entity_id="e1",
                role="ceo", title="CEO", assigned_by="alice", assigned_at="2026-01-01T00:00:00+00:00",
            )

    def test_valid_role_assigned(self) -> None:
        role = assign_stakeholder_role(
            stakeholder_role_id="sr1", target_plan_id="tp1", person_entity_id="e1",
            role="sponsor", title="VP Sales", assigned_by="alice", assigned_at="2026-01-01T00:00:00+00:00",
        )
        self.assertEqual("sponsor", role["role"])
        self.assertEqual("active", role["status"])


class RolesAreNotTitlesTests(unittest.TestCase):
    """Stop condition: 'rôles ≠ titres' -- role and title are accepted as
    fully independent inputs; no combination is rejected as
    'inconsistent', because there is no policy tying them together."""

    def test_ceo_title_with_a_non_sponsor_role_is_accepted(self) -> None:
        role = assign_stakeholder_role(
            stakeholder_role_id="sr1", target_plan_id="tp1", person_entity_id="e1",
            role="user", title="CEO", assigned_by="alice", assigned_at="2026-01-01T00:00:00+00:00",
        )
        self.assertEqual("user", role["role"])
        self.assertEqual("CEO", role["title"])

    def test_junior_title_with_sponsor_role_is_accepted(self) -> None:
        role = assign_stakeholder_role(
            stakeholder_role_id="sr1", target_plan_id="tp1", person_entity_id="e1",
            role="sponsor", title="Junior Analyst", assigned_by="alice", assigned_at="2026-01-01T00:00:00+00:00",
        )
        self.assertEqual("sponsor", role["role"])
        self.assertEqual("Junior Analyst", role["title"])

    def test_two_stakeholders_same_title_can_have_different_roles(self) -> None:
        a = assign_stakeholder_role(
            stakeholder_role_id="sr1", target_plan_id="tp1", person_entity_id="e1",
            role="champion", title="Director", assigned_by="alice", assigned_at="2026-01-01T00:00:00+00:00",
        )
        b = assign_stakeholder_role(
            stakeholder_role_id="sr2", target_plan_id="tp1", person_entity_id="e2",
            role="blocker", title="Director", assigned_by="alice", assigned_at="2026-01-01T00:00:00+00:00",
        )
        self.assertNotEqual(a["role"], b["role"])
        self.assertEqual(a["title"], b["title"])


class RoleCardinalityTests(unittest.TestCase):
    def test_first_sponsor_allowed(self) -> None:
        validate_role_cardinality([], "sponsor")  # should not raise

    def test_second_active_sponsor_rejected(self) -> None:
        existing = [_role("sponsor", stakeholder_role_id="sr1")]
        with self.assertRaises(RoleCardinalityError):
            validate_role_cardinality(existing, "sponsor")

    def test_second_champion_rejected(self) -> None:
        existing = [_role("champion", stakeholder_role_id="sr1")]
        with self.assertRaises(RoleCardinalityError):
            validate_role_cardinality(existing, "champion")

    def test_superseded_sponsor_does_not_block_a_new_one(self) -> None:
        existing = [_role("sponsor", status="superseded", stakeholder_role_id="sr1")]
        validate_role_cardinality(existing, "sponsor")  # should not raise

    def test_multiple_active_technique_stakeholders_allowed(self) -> None:
        existing = [_role("technique", stakeholder_role_id="sr1"), _role("technique", stakeholder_role_id="sr2")]
        validate_role_cardinality(existing, "technique")  # should not raise

    def test_multiple_active_blockers_allowed(self) -> None:
        existing = [_role("blocker", stakeholder_role_id="sr1")]
        validate_role_cardinality(existing, "blocker")  # should not raise

    def test_sponsor_cardinality_does_not_block_champion(self) -> None:
        existing = [_role("sponsor", stakeholder_role_id="sr1")]
        validate_role_cardinality(existing, "champion")  # should not raise


class SupersedeTests(unittest.TestCase):
    def test_supersede_flips_status(self) -> None:
        role = _role("sponsor")
        superseded = supersede_stakeholder_role(role)
        self.assertEqual("superseded", superseded["status"])


if __name__ == "__main__":
    unittest.main()
