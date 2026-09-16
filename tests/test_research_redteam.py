from __future__ import annotations

import unittest

from app.research_redteam import (
    SideStoryError,
    dismiss_side_story,
    find_contradictions,
    open_side_story,
    resolve_side_story,
    run_redteam_checklist,
)


def _side_story(**kwargs) -> dict:
    base = open_side_story(
        "c1",
        "Is the headcount figure actually current?",
        owner="alice",
        opened_at="2026-01-01T00:00:00+00:00",
        side_story_id="ss1",
        research_case_id="rc1",
    )
    base.update(kwargs)
    return base


class OpenSideStoryTests(unittest.TestCase):
    def test_open_requires_owner(self) -> None:
        with self.assertRaises(SideStoryError):
            open_side_story(
                "c1", "q", owner="", opened_at="2026-01-01T00:00:00+00:00",
                side_story_id="ss1", research_case_id="rc1",
            )

    def test_open_side_story_is_open_and_bound_to_parent(self) -> None:
        story = _side_story()
        self.assertEqual("open", story["status"])
        self.assertEqual("c1", story["parent_claim_id"])


class ResolveSideStoryTests(unittest.TestCase):
    def test_resolution_claim_must_reconnect_via_supersedes(self) -> None:
        story = _side_story()
        resolution = {"claim_id": "c2", "supersedes_claim_id": "c1", "derived_from_claim_ids": []}
        resolved = resolve_side_story(story, resolution, resolved_at="2026-01-05T00:00:00+00:00")
        self.assertEqual("resolved", resolved["status"])
        self.assertEqual("c2", resolved["resolution_claim_id"])

    def test_resolution_claim_may_reconnect_via_derived_from(self) -> None:
        story = _side_story()
        resolution = {"claim_id": "c2", "supersedes_claim_id": None, "derived_from_claim_ids": ["c1"]}
        resolved = resolve_side_story(story, resolution, resolved_at="2026-01-05T00:00:00+00:00")
        self.assertEqual("resolved", resolved["status"])

    def test_disconnected_resolution_claim_rejected(self) -> None:
        story = _side_story()
        resolution = {"claim_id": "c2", "supersedes_claim_id": None, "derived_from_claim_ids": []}
        with self.assertRaises(SideStoryError):
            resolve_side_story(story, resolution, resolved_at="2026-01-05T00:00:00+00:00")

    def test_resolution_claim_pointing_at_a_different_trunk_rejected(self) -> None:
        story = _side_story()
        resolution = {"claim_id": "c2", "supersedes_claim_id": "some-other-claim", "derived_from_claim_ids": []}
        with self.assertRaises(SideStoryError):
            resolve_side_story(story, resolution, resolved_at="2026-01-05T00:00:00+00:00")

    def test_cannot_resolve_an_already_closed_side_story(self) -> None:
        story = _side_story(status="dismissed")
        resolution = {"claim_id": "c2", "supersedes_claim_id": "c1", "derived_from_claim_ids": []}
        with self.assertRaises(SideStoryError):
            resolve_side_story(story, resolution, resolved_at="2026-01-05T00:00:00+00:00")


class DismissSideStoryTests(unittest.TestCase):
    def test_dismiss_requires_reason(self) -> None:
        story = _side_story()
        with self.assertRaises(SideStoryError):
            dismiss_side_story(story, "", dismissed_at="2026-01-05T00:00:00+00:00")

    def test_dismiss_with_reason_succeeds(self) -> None:
        story = _side_story()
        dismissed = dismiss_side_story(story, "not material", dismissed_at="2026-01-05T00:00:00+00:00")
        self.assertEqual("dismissed", dismissed["status"])
        self.assertEqual("not material", dismissed["dismissal_reason"])


class ContradictionTests(unittest.TestCase):
    def test_active_claims_contradicting_each_other_are_paired(self) -> None:
        claims = [
            {"claim_id": "c1", "status": "active", "contradicted_by_claim_ids": ["c2"]},
            {"claim_id": "c2", "status": "active", "contradicted_by_claim_ids": []},
        ]
        pairs = find_contradictions(claims)
        self.assertIn(("c1", "c2"), pairs)

    def test_superseded_claim_contradiction_is_ignored(self) -> None:
        claims = [
            {"claim_id": "c1", "status": "superseded", "contradicted_by_claim_ids": ["c2"]},
            {"claim_id": "c2", "status": "active", "contradicted_by_claim_ids": []},
        ]
        self.assertEqual([], find_contradictions(claims))


class RedTeamGoldCases(unittest.TestCase):
    """Gold cases from 08_EVIDENCE_DECISION_AND_GATES.md's red-team checklist."""

    def test_claim_with_contesting_evidence_is_flagged(self) -> None:
        claim = {"claim_id": "c1"}
        evidence_by_id = {"e1": {"contests_claim_ids": ["c1"]}}
        checklist = run_redteam_checklist(claim, evidence_by_id=evidence_by_id, side_stories=[])
        self.assertTrue(checklist.has_contradictory_evidence)

    def test_claim_with_no_contesting_evidence_is_clean(self) -> None:
        claim = {"claim_id": "c1"}
        evidence_by_id = {"e1": {"contests_claim_ids": []}}
        checklist = run_redteam_checklist(claim, evidence_by_id=evidence_by_id, side_stories=[])
        self.assertFalse(checklist.has_contradictory_evidence)

    def test_open_side_story_marks_unresolved_dependency(self) -> None:
        claim = {"claim_id": "c1"}
        story = _side_story()
        checklist = run_redteam_checklist(claim, evidence_by_id={}, side_stories=[story])
        self.assertTrue(checklist.has_open_side_story)
        self.assertTrue(checklist.has_unresolved_dependency)

    def test_resolved_side_story_does_not_mark_unresolved_dependency(self) -> None:
        claim = {"claim_id": "c1"}
        story = _side_story(status="resolved")
        checklist = run_redteam_checklist(claim, evidence_by_id={}, side_stories=[story])
        self.assertFalse(checklist.has_unresolved_dependency)

    def test_side_story_on_a_different_claim_is_not_counted(self) -> None:
        claim = {"claim_id": "c1"}
        story = _side_story(parent_claim_id="c999")
        checklist = run_redteam_checklist(claim, evidence_by_id={}, side_stories=[story])
        self.assertFalse(checklist.has_open_side_story)


if __name__ == "__main__":
    unittest.main()
