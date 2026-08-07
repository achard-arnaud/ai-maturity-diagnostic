from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import yaml

from app.workflows import WorkflowPlanner


def dump(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


class ReachWorkflowResolverTests(unittest.TestCase):
    def seed_without_contacts(self, root: Path) -> None:
        study = root / "studies/acme"
        dump(study / "00_manifest.yaml", {
            "study_id": "acme-1",
            "company_id": "C1",
            "company": "Acme",
            "product_snapshots": [{"offer_id": "OFFER-1", "path": "inputs/OFFER-1.yaml"}],
        })
        dump(study / "inputs/OFFER-1.yaml", {"offer": {"offer_id": "OFFER-1", "profile_version": "v1"}})
        dump(study / "05_enterprise_demand_profile.yaml", {
            "company": "Acme",
            "evidence_claims": [{"claim_id": "E1"}],
            "capability_gaps": [{"claim_id": "G1"}],
            "confidence": "high",
        })
        dump(study / "06_product_fit_matrix.yaml", {
            "recommended_offer_id": "OFFER-1",
            "decision": "validate",
            "matches": [{"offer_id": "OFFER-1", "product_profile_version": "v1", "decision": "validate", "hard_gates": []}],
        })

    def test_direct_reach_without_contacts_returns_contact_resolver_not_exception(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.seed_without_contacts(root)
            plan = WorkflowPlanner(root).plan({"kind": "reach", "study_id": "acme-1"})
            reach_step = next(step for step in plan["steps"] if step["id"] == "reach")
            self.assertEqual("blocked", reach_step["status"])
            self.assertEqual("Cibler les contacts", reach_step["resolver"]["cta_label"])
            self.assertEqual("person-opportunity-targeting", reach_step["resolver"]["owner_skill"])
            self.assertEqual("locked", next(step for step in plan["steps"] if step["id"] == "pilot")["status"])

    def test_direct_reach_with_stale_contacts_returns_recalculation_resolver(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.seed_without_contacts(root)
            dump(root / "studies/acme/06b_contact_targets.yaml", {
                "study_id": "old-study",
                "company_id": "C9",
                "offer_id": "OFFER-OLD",
                "targets": [{"person_id": "P1"}],
            })
            plan = WorkflowPlanner(root).plan({"kind": "reach", "study_id": "acme-1"})
            reach_step = next(step for step in plan["steps"] if step["id"] == "reach")
            self.assertEqual("Recalculer les contacts", reach_step["resolver"]["cta_label"])
            self.assertEqual("person-opportunity-targeting", reach_step["resolver"]["owner_skill"])


if __name__ == "__main__":
    unittest.main()
