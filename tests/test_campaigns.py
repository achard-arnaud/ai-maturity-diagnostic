from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import yaml

from app import network_index
from app.campaigns import launch_prospecting_campaign, list_campaigns, mark_campaign_sent, prepare_cross_sell
from app.core import ControlPlaneError


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(item, ensure_ascii=False) + "\n" for item in records), encoding="utf-8")


def dump_yaml(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def _seed_network_index(root: Path) -> None:
    data_root = root / "data" / "private" / "network"
    write_jsonl(
        data_root / "people.jsonl",
        [
            {
                "person_id": "PERS-1",
                "display_name": "Alice Martin",
                "normalized_name": "alice martin",
                "seed_company_id": "COMP-1",
                "identity_confidence": "high",
                "role_hypotheses": ["economic_sponsor"],
                "status": "active",
                "last_updated": "2026-08-01",
                "stale_after_months": 6,
            },
            {
                "person_id": "PERS-2",
                "display_name": "Bob Durand",
                "normalized_name": "bob durand",
                "seed_company_id": "COMP-1",
                "identity_confidence": "medium",
                "role_hypotheses": ["veto_player"],
                "status": "seeded",
                "last_updated": "2026-08-01",
                "stale_after_months": 6,
            },
        ],
    )
    write_jsonl(
        data_root / "companies.jsonl",
        [
            {
                "company_id": "COMP-1",
                "canonical_name": "EDF",
                "normalized_name": "edf",
                "status": "active",
                "icb_mapping": {"sector": {"code": "651010"}},
                "last_updated": "2026-08-01",
                "stale_after_months": 6,
            }
        ],
    )
    index_path = data_root / "network_index.sqlite"
    network_index.rebuild(data_root, index_path)


class LaunchProspectingCampaignTests(unittest.TestCase):
    def test_text_filter_persists_campaign_with_matching_target_count(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed_network_index(root)
            record = launch_prospecting_campaign(
                root, name="AI Leaders", criteria={"entity": "people", "text": "alice"}, actor="rep@acme.com"
            )
            self.assertEqual(1, record["target_count"])
            self.assertEqual("draft", record["status"])
            self.assertEqual("rep@acme.com", record["actor"])
            self.assertTrue(record["campaign_id"])
            stored = list_campaigns(root)
            self.assertEqual(1, len(stored))
            self.assertEqual(record["campaign_id"], stored[0]["campaign_id"])

    def test_status_filter_infers_people_and_persists_target_count(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed_network_index(root)
            record = launch_prospecting_campaign(
                root, name="Active contacts", criteria={"entity": "people", "status": "active"}, actor="rep@acme.com"
            )
            self.assertEqual(1, record["target_count"])

    def test_empty_match_criteria_still_persists_campaign_with_zero_target_count(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed_network_index(root)
            record = launch_prospecting_campaign(
                root, name="Nobody", criteria={"entity": "people", "text": "nonexistent-name"}, actor="rep@acme.com"
            )
            self.assertEqual(0, record["target_count"])
            self.assertEqual("draft", record["status"])
            stored = list_campaigns(root)
            self.assertEqual(1, len(stored))
            self.assertEqual(0, stored[0]["target_count"])

    def test_company_criteria_via_sector(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed_network_index(root)
            record = launch_prospecting_campaign(
                root, name="Utilities", criteria={"sector": "651010"}, actor="rep@acme.com"
            )
            self.assertEqual("companies", record["entity"])
            self.assertEqual(1, record["target_count"])

    def test_ambiguous_criteria_without_entity_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed_network_index(root)
            with self.assertRaises(ControlPlaneError):
                launch_prospecting_campaign(root, name="Ambiguous", criteria={"text": "alice"}, actor="rep@acme.com")

    def test_missing_actor_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed_network_index(root)
            with self.assertRaises(ControlPlaneError):
                launch_prospecting_campaign(root, name="X", criteria={"entity": "people"}, actor="")


class MarkCampaignSentTests(unittest.TestCase):
    def test_transitions_draft_to_sent_and_records_actor(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed_network_index(root)
            record = launch_prospecting_campaign(
                root, name="AI Leaders", criteria={"entity": "people", "text": "alice"}, actor="rep@acme.com"
            )
            updated = mark_campaign_sent(root, record["campaign_id"], actor="ops@acme.com")
            self.assertEqual("sent", updated["status"])
            self.assertEqual("ops@acme.com", updated["sent_by"])
            self.assertTrue(updated["sent_at"])
            stored = list_campaigns(root)
            self.assertEqual(1, len(stored))
            self.assertEqual("sent", stored[0]["status"])

    def test_calling_twice_is_idempotent_first_call_wins(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed_network_index(root)
            record = launch_prospecting_campaign(
                root, name="AI Leaders", criteria={"entity": "people", "text": "alice"}, actor="rep@acme.com"
            )
            first = mark_campaign_sent(root, record["campaign_id"], actor="ops@acme.com")
            second = mark_campaign_sent(root, record["campaign_id"], actor="someone-else@acme.com")
            self.assertEqual(first, second)
            self.assertEqual("ops@acme.com", second["sent_by"])

    def test_unknown_campaign_id_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaises(ControlPlaneError):
                mark_campaign_sent(root, "CAMP-does-not-exist", actor="ops@acme.com")

    def test_missing_actor_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _seed_network_index(root)
            record = launch_prospecting_campaign(
                root, name="AI Leaders", criteria={"entity": "people", "text": "alice"}, actor="rep@acme.com"
            )
            with self.assertRaises(ControlPlaneError):
                mark_campaign_sent(root, record["campaign_id"], actor="")

    def test_non_draft_non_sent_status_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._seed_cross_sell_event(root)
            with self.assertRaises(ControlPlaneError):
                mark_campaign_sent(root, "XSELL-1", actor="ops@acme.com")

    def _seed_cross_sell_event(self, root: Path) -> None:
        write_jsonl(
            root / "data/private/network/campaigns.jsonl",
            [{"campaign_id": "XSELL-1", "kind": "cross_sell_prep", "status": "recorded"}],
        )


class PrepareCrossSellTests(unittest.TestCase):
    def _seed_cross_sell_inventory(self, root: Path) -> None:
        dump_yaml(
            root / "studies/acme/05b_use_case_inventory.yaml",
            {
                "study_id": "acme-1",
                "company": "Acme",
                "inventory_version": "1",
                "use_cases": [
                    {
                        "use_case_id": "UC1",
                        "maturity": "active",
                        "outcome_family": "support_deflection",
                        "feedback": [{"note": "well received"}],
                    },
                    {
                        "use_case_id": "UC2",
                        "maturity": "active",
                        "outcome_family": "support_deflection",
                        "feedback": [{"note": "also well received"}],
                    },
                ],
            },
        )

    def test_cross_sell_prep_calls_through_to_nudging_and_records_event(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._seed_cross_sell_inventory(root)
            result = prepare_cross_sell(root, study_id="acme-1", actor="rep@acme.com")
            self.assertEqual("acme-1", result["nudging"]["study_id"])
            self.assertEqual(1, len(result["nudging"]["nudges"]))
            self.assertEqual("cross_sell_package", result["nudging"]["nudges"][0]["mode"])
            event = result["event"]
            self.assertEqual("cross_sell_prep", event["kind"])
            self.assertEqual("acme-1", event["study_id"])
            self.assertEqual(1, event["nudge_count"])
            stored = list_campaigns(root)
            self.assertEqual(1, len(stored))
            self.assertEqual(event["campaign_id"], stored[0]["campaign_id"])

    def test_missing_study_id_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaises(ControlPlaneError):
                prepare_cross_sell(root, study_id="", actor="rep@acme.com")


if __name__ == "__main__":
    unittest.main()
