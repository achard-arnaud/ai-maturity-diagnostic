from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import yaml

from app.account_view import get_account_360


def dump_yaml(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(item, ensure_ascii=False) + "\n" for item in records), encoding="utf-8")


class AccountView360Tests(unittest.TestCase):
    def _build_index(self, root: Path, *, with_person: bool = True) -> Path:
        from app import network_index

        network_root = root / "data" / "private" / "network"
        write_jsonl(
            network_root / "companies.jsonl",
            [
                {
                    "company_id": "C1",
                    "canonical_name": "Acme",
                    "normalized_name": "acme",
                    "status": "active",
                    "icb_mapping": {"sector": {"code": "651010"}},
                    "workspace_id": "default",
                    "last_updated": "2026-08-01",
                    "stale_after_months": 6,
                }
            ],
        )
        if with_person:
            write_jsonl(
                network_root / "people.jsonl",
                [
                    {
                        "person_id": "P1",
                        "display_name": "Alice Martin",
                        "normalized_name": "alice martin",
                        "seed_company_id": "C1",
                        "identity_confidence": "high",
                        "role_hypotheses": ["economic_sponsor"],
                        "status": "active",
                        "last_updated": "2026-08-01",
                        "stale_after_months": 6,
                    }
                ],
            )
        index_path = network_root / "network_index.sqlite"
        network_index.rebuild(network_root, index_path)
        return index_path

    def _seed_study(self, root: Path) -> None:
        study = root / "studies/acme"
        snapshot = "inputs/product_snapshots/OFFER-1__v1.yaml"
        dump_yaml(study / "00_manifest.yaml", {
            "study_id": "acme-1", "company_id": "C1", "company": "Acme",
            "product_snapshots": [{"offer_id": "OFFER-1", "path": snapshot}],
        })
        dump_yaml(study / snapshot, {"offer": {"offer_id": "OFFER-1", "profile_version": "v1", "icp": {"personas": {}}}})
        dump_yaml(study / "05_enterprise_demand_profile.yaml", {"company": "Acme", "evidence_claims": [{"claim_id": "E1"}], "capability_gaps": [{"claim_id": "G1"}], "confidence": "high"})
        dump_yaml(study / "06_product_fit_matrix.yaml", {
            "recommended_offer_id": "OFFER-1", "decision": "validate",
            "matches": [{"offer_id": "OFFER-1", "product_profile_version": "v1", "decision": "validate", "hard_gates": []}],
        })
        dump_yaml(study / "06b_contact_targets.yaml", {
            "study_id": "acme-1", "company_id": "C1", "offer_id": "OFFER-1", "fit_decision": "validate",
            "targets": [{"person_id": "P1", "target_id": "T1", "role_hypotheses": ["economic_sponsor"], "persona_matches": [], "target_score": 80, "current_role_status": "current", "required_validations": []}],
        })
        actions_path = root / "studies" / "acme-1" / "06d_blocker_actions.jsonl"
        actions_path.parent.mkdir(parents=True, exist_ok=True)
        actions_path.write_text(json.dumps({"study_id": "acme-1", "step_id": "matching", "action": "cancel", "actor": "a@b.com", "reason": None, "timestamp": "2026-01-01T00:00:00+00:00"}) + "\n", encoding="utf-8")

    def test_full_account_returns_all_sections_populated(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            index_path = self._build_index(root)
            self._seed_study(root)

            result = get_account_360(root, "C1", index_path=index_path)

            self.assertIsNotNone(result)
            self.assertEqual(result["company"]["company_id"], "C1")
            self.assertEqual(len(result["people"]), 1)
            self.assertEqual(result["people"][0]["person_id"], "P1")
            self.assertIsNotNone(result["qualification"])
            self.assertEqual(result["qualification"]["study_id"], "acme-1")
            self.assertIsNotNone(result["reach"])
            self.assertEqual(len(result["recent_actions"]), 1)

    def test_bare_company_returns_empty_sections_without_crashing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            index_path = self._build_index(root, with_person=False)

            result = get_account_360(root, "C1", index_path=index_path)

            self.assertIsNotNone(result)
            self.assertEqual(result["company"]["company_id"], "C1")
            self.assertEqual(result["people"], [])
            self.assertIsNone(result["qualification"])
            self.assertIsNone(result["reach"])
            self.assertEqual(result["recent_actions"], [])

    def test_unknown_company_id_returns_none(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            index_path = self._build_index(root)

            result = get_account_360(root, "UNKNOWN-CO", index_path=index_path)

            self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
