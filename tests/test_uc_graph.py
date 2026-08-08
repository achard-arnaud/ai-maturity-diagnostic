from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import yaml

from app.uc_graph import UseCaseGraph


def dump(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


class UseCaseGraphTests(unittest.TestCase):
    def seed_company(self, root: Path, study_name: str, company_id: str, company: str, outcome: str) -> Path:
        study = root / "studies" / study_name
        dump(study / "00_manifest.yaml", {"study_id": study_name, "company_id": company_id, "company": company})
        dump(study / "05b_use_case_inventory.yaml", {
            "study_id": study_name, "company_id": company_id, "company": company, "inventory_version": "1",
            "use_cases": [
                {"use_case_id": "UC-A", "name": "Draft", "outcome_family": outcome, "dependencies": {"depends_on": [], "enables": ["UC-B"]}, "reusable_assets": ["knowledge-base"], "evidence_status": "validated"},
                {"use_case_id": "UC-B", "name": "Review", "outcome_family": outcome, "dependencies": {"depends_on": ["UC-A"], "enables": []}, "reusable_assets": ["knowledge-base"], "evidence_status": "observed"},
            ],
        })
        return study

    def test_company_graph_derives_typed_links_without_new_store(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); study = self.seed_company(root, "acme-1", "C1", "Acme", "response-quality")
            dump(study / "05c_value_chain_causal_map.yaml", {
                "analyses": [{
                    "use_case_id": "UC-A", "evidence_refs": ["E1"],
                    "ishikawa": {"people": [], "process": ["manual handoff"], "technology": [], "data": [], "governance_control": [], "environment_external": []},
                    "adjacent_workflow_hypotheses": [{"label": "Approval", "relation": "downstream", "basis": "observed handoff", "status": "hypothesis", "candidate_use_case_id": None}],
                }, {
                    "use_case_id": "UC-B", "evidence_refs": ["E2"],
                    "ishikawa": {"people": [], "process": ["manual handoff"], "technology": [], "data": [], "governance_control": [], "environment_external": []},
                    "adjacent_workflow_hypotheses": [],
                }],
            })
            graph = UseCaseGraph(root).company("acme-1")
            relations = {edge["relation"] for edge in graph["edges"]}
            self.assertTrue({"enables", "depends_on", "shares_asset", "same_outcome", "causal_neighbor"}.issubset(relations))
            self.assertTrue(any(node["node_type"] == "workflow_hypothesis" for node in graph["nodes"]))
            self.assertTrue(all(edge["demand_proof"] is False for edge in graph["edges"]))
            self.assertEqual("derived_on_read", graph["persistence"])

    def test_sector_similarity_is_low_confidence_hypothesis_not_demand_proof(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.seed_company(root, "acme-1", "C1", "Acme", "response-quality")
            self.seed_company(root, "beta-1", "C2", "Beta", "response-quality")
            jsonl(root / "data/private/network/company_icb_mappings.jsonl", [
                {"company_id": "C1", "mapping_status": "validated", "sector": {"code": "301010", "name": "Banks"}},
                {"company_id": "C2", "mapping_status": "validated", "sector": {"code": "301010", "name": "Banks"}},
            ])
            graph = UseCaseGraph(root).sector("301010")
            self.assertTrue(graph["edges"])
            self.assertTrue(all(edge["relation"] == "similar_pattern" for edge in graph["edges"]))
            self.assertTrue(all(edge["confidence"] == "low" and edge["demand_proof"] is False for edge in graph["edges"]))
            self.assertIn("never prove company demand", graph["warning"])


if __name__ == "__main__":
    unittest.main()
