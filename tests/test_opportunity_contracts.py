from __future__ import annotations

import unittest
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator, ValidationError

from app.opportunity_policy import OpportunityLinkError, validate_commercial_chain, validate_opportunity_links

ROOT = Path(__file__).resolve().parents[1]


def _schema(name: str) -> dict:
    return yaml.safe_load((ROOT / "contracts" / f"{name}_v1.schema.yaml").read_text(encoding="utf-8"))


def _records() -> tuple[dict, dict, dict, dict, dict]:
    shared = {"workspace_id": "ws-a", "created_at": "2026-09-17T00:00:00+00:00", "updated_at": None}
    lead = {**shared, "lead_id": "lead-1", "demand_id": "demand-1", "fit_assessment_id": "fit-1", "target_plan_id": "target-1", "source_engagement_event_id": "event-1", "status": "qualified"}
    opportunity = {**shared, "opportunity_id": "opp-1", "lead_id": "lead-1", "demand_id": "demand-1", "fit_assessment_id": "fit-1", "target_plan_id": "target-1", "status": "draft"}
    proof = {**shared, "proof_id": "proof-1", "opportunity_id": "opp-1", "status": "draft"}
    deal = {**shared, "deal_id": "deal-1", "opportunity_id": "opp-1", "proof_id": "proof-1", "status": "draft"}
    expansion = {**shared, "expansion_id": "expansion-1", "deal_id": "deal-1", "status": "identified"}
    return lead, opportunity, proof, deal, expansion


class OpportunitySchemaTests(unittest.TestCase):
    def test_all_commercial_schemas_are_valid(self) -> None:
        for name in ("lead", "opportunity", "proof", "deal", "expansion"):
            Draft202012Validator.check_schema(_schema(name))

    def test_chain_records_validate_against_their_contracts(self) -> None:
        for name, record in zip(("lead", "opportunity", "proof", "deal", "expansion"), _records()):
            Draft202012Validator(_schema(name)).validate(record)

    def test_opportunity_has_no_prospect_shape(self) -> None:
        _lead, opportunity, *_rest = _records()
        opportunity["prospect_id"] = "raw-prospect-1"
        with self.assertRaises(ValidationError):
            Draft202012Validator(_schema("opportunity")).validate(opportunity)


class OpportunityLinkIntegrityTests(unittest.TestCase):
    def test_complete_same_workspace_chain_is_valid(self) -> None:
        validate_commercial_chain(*_records())

    def test_unqualified_lead_cannot_enter_pipeline(self) -> None:
        lead, opportunity, *_rest = _records()
        lead["status"] = "disqualified"
        with self.assertRaisesRegex(OpportunityLinkError, "qualified"):
            validate_opportunity_links(lead, opportunity)

    def test_opportunity_cannot_rewrite_upstream_fit(self) -> None:
        lead, opportunity, *_rest = _records()
        opportunity["fit_assessment_id"] = "fit-other"
        with self.assertRaisesRegex(OpportunityLinkError, "fit_assessment_id"):
            validate_opportunity_links(lead, opportunity)

    def test_cross_workspace_chain_is_rejected(self) -> None:
        lead, opportunity, proof, deal, expansion = _records()
        deal["workspace_id"] = "ws-b"
        with self.assertRaisesRegex(OpportunityLinkError, "workspace"):
            validate_commercial_chain(lead, opportunity, proof, deal, expansion)


if __name__ == "__main__":
    unittest.main()
