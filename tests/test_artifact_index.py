from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from app.artifact_archive_store import archive_artifact
from app.artifact_index import ArtifactNotFound, ArtifactPolicyError, get_artifact, list_artifacts
from app.artifact_policy import load_artifact_schema
from app.claim_store import put_claim
from app.demand_store import create_demand
from app.demand_policy import known
from app.evidence_store import put_evidence
from app.fit_store import create_fit
from app.learning_proposals import LearningProposalStore
from app.opportunity_store import put_opportunity
from app.reach_store import put_sequence
from app.research_case_store import put_case
from app.signal_store import put_signal
from app.target_plan_store import put_plan, put_stakeholder


def _signal(signal_id: str, workspace_id: str, company_entity_id: str = "entity_1") -> dict:
    return {
        "signal_id": signal_id, "workspace_id": workspace_id,
        "source": {"kind": "public", "ref": "https://example.com/x"},
        "observed_at": "2026-06-01T00:00:00+00:00", "status": "new",
        "company_entity_id": company_entity_id, "dedup_key": f"key-{signal_id}",
        "freshness": {"stale_after_days": 30},
        "provenance": {"source_refs": ["ref"], "epistemic_status": "hypothesis", "evidence_grade": "U1"},
    }


def _evidence(evidence_id: str, workspace_id: str, entity_refs: list[str]) -> dict:
    return {
        "evidence_id": evidence_id, "workspace_id": workspace_id,
        "source": {"kind": "public", "ref": "https://example.com/x"},
        "locator": "https://example.com/x", "evidence_type": "observation",
        "dated_at": "2026-06-01T00:00:00+00:00", "excerpt": "an excerpt",
        "hash": "h1", "license": "public", "entity_refs": entity_refs,
        "evidence_grade": "U1",
    }


def _case(research_case_id: str, workspace_id: str, company_entity_id: str = "entity_1") -> dict:
    return {
        "research_case_id": research_case_id, "workspace_id": workspace_id,
        "company_entity_id": company_entity_id, "status": "open", "owner": "alice@example.com",
        "created_at": "2026-06-01T00:00:00+00:00", "updated_at": "2026-06-01T00:00:00+00:00",
        "origin_signal_id": None, "blockers": [],
    }


def _claim(claim_id: str, workspace_id: str, research_case_id: str, company_entity_id: str = "entity_1") -> dict:
    return {
        "claim_id": claim_id, "workspace_id": workspace_id, "research_case_id": research_case_id,
        "company_entity_id": company_entity_id, "statement": "a statement", "claim_type": "fact",
        "evidence_ids": [], "derived_from_claim_ids": [], "status": "active",
        "contradicted_by_claim_ids": [],
    }


def _demand(demand_id: str, workspace_id: str, company_entity_id: str = "entity_1") -> dict:
    return {
        "demand_id": demand_id, "workspace_id": workspace_id, "company_entity_id": company_entity_id,
        "status": "observed", "problem": known("manual onboarding"),
        "population": {"known": False, "value": None}, "impact": {"known": False, "value": None},
        "urgency": {"known": False, "value": None}, "initiative": {"known": False, "value": None},
        "sponsor": {"known": False, "value": None}, "budget": {"known": False, "value": None},
        "timing": {"known": False, "value": None}, "claim_ids": [], "origin_profile_ref": None,
        "created_at": "2026-06-01T00:00:00+00:00", "updated_at": "2026-06-01T00:00:00+00:00",
    }


def _fit(fit_assessment_id: str, workspace_id: str, demand_id: str = "d1") -> dict:
    return {
        "fit_assessment_id": fit_assessment_id, "workspace_id": workspace_id,
        "input_lock": {"demand_id": demand_id, "demand_version": 1, "product_snapshot_id": "snap1", "input_hash": "h1"},
        "status": "draft", "gates": [], "coverage": None, "gaps": [], "alternatives": [],
        "counter_evidence": [], "score": None, "verdict": None,
        "created_at": "2026-06-01T00:00:00+00:00", "updated_at": None,
    }


def _plan(target_plan_id: str, workspace_id: str, company_entity_id: str = "entity_1") -> dict:
    return {
        "target_plan_id": target_plan_id, "workspace_id": workspace_id, "company_entity_id": company_entity_id,
        "fit_assessment_id": "fa1", "status": "active", "created_at": "2026-06-01T00:00:00+00:00", "updated_at": None,
    }


def _stakeholder(stakeholder_role_id: str, target_plan_id: str, person_entity_id: str = "person_1") -> dict:
    return {
        "stakeholder_role_id": stakeholder_role_id, "target_plan_id": target_plan_id,
        "person_entity_id": person_entity_id, "role": "sponsor", "title": "VP",
        "status": "active", "assigned_at": "2026-06-01T00:00:00+00:00", "assigned_by": "alice",
        "supersedes_stakeholder_role_id": None,
    }


def _sequence(sequence_id: str, workspace_id: str, target_plan_id: str, stakeholder_role_id: str) -> dict:
    return {
        "sequence_id": sequence_id, "workspace_id": workspace_id, "target_plan_id": target_plan_id,
        "stakeholder_role_id": stakeholder_role_id, "status": "draft", "created_at": "2026-06-01T00:00:00+00:00",
        "updated_at": None,
    }


def _opportunity(opportunity_id: str, workspace_id: str) -> dict:
    return {
        "opportunity_id": opportunity_id, "workspace_id": workspace_id, "lead_id": "lead-1",
        "demand_id": "d1", "fit_assessment_id": "fa1", "target_plan_id": "tp1",
        "status": "draft", "created_at": "2026-06-01T00:00:00+00:00", "updated_at": None,
    }


class SeededIndex:
    def __init__(self, root: Path, workspace_id: str = "ws-a") -> None:
        self.root = root
        self.workspace_id = workspace_id
        put_signal(root, workspace_id, _signal("signal_1", workspace_id))
        put_evidence(root, workspace_id, _evidence("evidence_1", workspace_id, ["entity_1"]))
        put_case(root, workspace_id, _case("rc1", workspace_id))
        put_claim(root, workspace_id, _claim("claim_1", workspace_id, "rc1"))
        create_demand(root, workspace_id, _demand("d1", workspace_id))
        create_fit(root, workspace_id, _fit("fa1", workspace_id))
        put_plan(root, workspace_id, _plan("tp1", workspace_id))
        put_stakeholder(root, workspace_id, _stakeholder("sr1", "tp1"))
        put_sequence(root, workspace_id, _sequence("seq1", workspace_id, "tp1", "sr1"))
        put_opportunity(root, workspace_id, _opportunity("opp1", workspace_id))
        LearningProposalStore(root, workspace_id).create(
            origin="retrospective", target_kind="rule", target_ref="rule-1",
            hypothesis="a hypothesis", evidence_refs=["evidence_1"], actor_id="alice@example.com",
            proposal_id="lp_1",
        )


class ListArtifactsTests(unittest.TestCase):
    def test_lists_every_seeded_kind(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            SeededIndex(root)
            page = list_artifacts(root, "ws-a", limit=100)
            kinds = {a["kind"] for a in page.items}
            self.assertEqual(
                {
                    "signal", "evidence", "research_case", "claim", "demand", "fit_assessment",
                    "target_plan", "stakeholder_role", "sequence", "opportunity", "learning_proposal",
                },
                kinds,
            )
            schema = load_artifact_schema()
            for artifact in page.items:
                Draft202012Validator(schema).validate(artifact)

    def test_filter_by_kind(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            SeededIndex(root)
            page = list_artifacts(root, "ws-a", kind="fit_assessment", limit=100)
            self.assertEqual(1, len(page.items))
            self.assertEqual("fit_assessment", page.items[0]["kind"])

    def test_unknown_kind_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ArtifactPolicyError):
                list_artifacts(Path(tmp), "ws-a", kind="not_a_kind")

    def test_filter_by_related_to(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            SeededIndex(root)
            page = list_artifacts(root, "ws-a", related_to="entity_1", limit=100)
            kinds = {a["kind"] for a in page.items}
            # signal, evidence, research_case, claim, demand are all
            # related to entity_1 in the fixture.
            self.assertIn("research_case", kinds)
            self.assertIn("demand", kinds)
            self.assertNotIn("sequence", kinds)  # unrelated to entity_1

    def test_workspace_isolation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            SeededIndex(root, "ws-a")
            page = list_artifacts(root, "ws-b", limit=100)
            self.assertEqual([], page.items)

    def test_deterministic_ordering_and_pagination(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            SeededIndex(root)
            full = list_artifacts(root, "ws-a", limit=100).items
            first_page = list_artifacts(root, "ws-a", limit=3)
            self.assertEqual(3, len(first_page.items))
            self.assertIsNotNone(first_page.next_cursor)
            second_page = list_artifacts(root, "ws-a", limit=100, cursor=first_page.next_cursor)
            self.assertEqual(full[3:], second_page.items)
            self.assertEqual(full[:3], first_page.items)

    def test_status_filter_excludes_archived_by_default_only_when_asked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            SeededIndex(root)
            all_active = list_artifacts(root, "ws-a", status="active", limit=100)
            self.assertTrue(all(a["status"] == "active" for a in all_active.items))
            archive_artifact(root, "ws-a", "artifact:signal:signal_1", actor="alice", archived_at="2026-06-02T00:00:00+00:00")
            active_after = list_artifacts(root, "ws-a", status="active", limit=100)
            self.assertNotIn("artifact:signal:signal_1", [a["artifact_id"] for a in active_after.items])
            archived_only = list_artifacts(root, "ws-a", status="archived", limit=100)
            self.assertEqual(["artifact:signal:signal_1"], [a["artifact_id"] for a in archived_only.items])


class GetArtifactTests(unittest.TestCase):
    def test_point_lookup_by_kind_and_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            SeededIndex(root)
            artifact = get_artifact(root, "ws-a", "artifact:fit_assessment:fa1")
            self.assertEqual("fit_assessment", artifact["kind"])

    def test_unknown_artifact_id_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            SeededIndex(root)
            with self.assertRaises(ArtifactNotFound):
                get_artifact(root, "ws-a", "artifact:fit_assessment:does-not-exist")

    def test_malformed_artifact_id_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ArtifactNotFound):
                get_artifact(Path(tmp), "ws-a", "not-an-artifact-id")

    def test_cross_workspace_lookup_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            SeededIndex(root, "ws-a")
            with self.assertRaises(ArtifactNotFound):
                get_artifact(root, "ws-b", "artifact:fit_assessment:fa1")

    def test_reflects_archive_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            SeededIndex(root)
            archive_artifact(root, "ws-a", "artifact:fit_assessment:fa1", actor="alice", archived_at="2026-06-02T00:00:00+00:00")
            artifact = get_artifact(root, "ws-a", "artifact:fit_assessment:fa1")
            self.assertEqual("archived", artifact["status"])


if __name__ == "__main__":
    unittest.main()
