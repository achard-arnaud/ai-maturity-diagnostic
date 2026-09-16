from __future__ import annotations

import unittest
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

from app.opportunity_notes import CommercialAccessError, CommercialNoteError, create_discovery_note, record_commercial_decision, validate_note_opportunity_workspace

ROOT = Path(__file__).resolve().parents[1]
TIME = "2026-09-17T00:00:00+00:00"


class DiscoveryNoteTests(unittest.TestCase):
    def test_note_is_bounded_sourced_and_schema_valid(self) -> None:
        note = create_discovery_note(discovery_note_id="note-1", workspace_id="ws-a", opportunity_id="opp-1", conversation_id="conv-1", author_id="a", actor_role="commercial_reviewer", occurred_at=TIME, summary="Customer confirmed the discovery agenda.", evidence_refs=["event-1"], created_at=TIME)
        schema = yaml.safe_load((ROOT / "contracts/discovery_note_v1.schema.yaml").read_text(encoding="utf-8"))
        Draft202012Validator(schema).validate(note)

    def test_note_requires_authorized_role_and_provenance(self) -> None:
        with self.assertRaises(CommercialAccessError):
            create_discovery_note(discovery_note_id="n", workspace_id="ws", opportunity_id="o", conversation_id="c", author_id="a", actor_role="viewer", occurred_at=TIME, summary="x", evidence_refs=["e"], created_at=TIME)
        with self.assertRaisesRegex(CommercialNoteError, "evidence"):
            create_discovery_note(discovery_note_id="n", workspace_id="ws", opportunity_id="o", conversation_id="c", author_id="a", actor_role="admin", occurred_at=TIME, summary="x", evidence_refs=[], created_at=TIME)

    def test_note_cannot_become_unbounded_transcript(self) -> None:
        with self.assertRaisesRegex(CommercialNoteError, "4000"):
            create_discovery_note(discovery_note_id="n", workspace_id="ws", opportunity_id="o", conversation_id="c", author_id="a", actor_role="admin", occurred_at=TIME, summary="x" * 4001, evidence_refs=["e"], created_at=TIME)


class CommercialDecisionTests(unittest.TestCase):
    def test_decision_is_attributed_sourced_and_schema_valid(self) -> None:
        record = record_commercial_decision(commercial_decision_id="decision-1", workspace_id="ws-a", opportunity_id="opp-1", decision="advance", rationale="Discovery evidence supports a proof design.", evidence_refs=["note-1"], decided_by="owner", actor_role="commercial_decider", decided_at=TIME)
        schema = yaml.safe_load((ROOT / "contracts/commercial_decision_v1.schema.yaml").read_text(encoding="utf-8"))
        Draft202012Validator(schema).validate(record)

    def test_decision_requires_decider_role_and_valid_vocab(self) -> None:
        with self.assertRaises(CommercialAccessError):
            record_commercial_decision(commercial_decision_id="d", workspace_id="ws", opportunity_id="o", decision="advance", rationale="x", evidence_refs=["e"], decided_by="a", actor_role="commercial_reviewer", decided_at=TIME)
        with self.assertRaisesRegex(CommercialNoteError, "unknown"):
            record_commercial_decision(commercial_decision_id="d", workspace_id="ws", opportunity_id="o", decision="override", rationale="x", evidence_refs=["e"], decided_by="a", actor_role="admin", decided_at=TIME)

    def test_note_cannot_cross_workspace_or_opportunity(self) -> None:
        note = {"workspace_id": "ws-a", "opportunity_id": "opp-1"}
        with self.assertRaisesRegex(CommercialNoteError, "same workspace"):
            validate_note_opportunity_workspace(note, {"workspace_id": "ws-b", "opportunity_id": "opp-1"})


if __name__ == "__main__":
    unittest.main()
