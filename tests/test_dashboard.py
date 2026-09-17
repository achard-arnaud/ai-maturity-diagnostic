from __future__ import annotations

import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

import yaml

from app.dashboard import FollowUpDashboard, UseCaseHeritage, _age_fields


def dump(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


class DashboardTests(unittest.TestCase):
    def test_follow_up_surfaces_qualification_resolver_before_technical_todo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            study = root / "studies/acme"
            dump(study / "00_manifest.yaml", {"study_id": "acme-1", "company": "Acme", "company_id": "C1", "product_snapshots": []})
            dump(study / "05_enterprise_demand_profile.yaml", {"evidence_claims": [], "capability_gaps": [], "confidence": "low"})
            dump(root / "artifacts/TODO_productization_v0_7.yaml", {"items": [{"id": "T1", "priority": "P2", "status": "open", "area": "quality", "task": "Later technical task"}]})
            rows = FollowUpDashboard(root).items()
            business = next(item for item in rows if item["kind"] == "qualification")
            self.assertEqual("P0", business["priority"])
            self.assertEqual("enterprise-demand-intelligence", business["resolver"]["owner_skill"])
            self.assertEqual("Compléter la demande", business["resolver"]["cta_label"])
            self.assertTrue(any(item["kind"] == "technical_todo" for item in rows))

    def test_age_fields_computes_days_and_stale_flag(self) -> None:
        as_of = date(2026, 9, 15)
        fresh = _age_fields("2026-09-01", 1, as_of=as_of)
        self.assertEqual(14, fresh["days_in_current_state"])
        self.assertFalse(fresh["is_stale"])

        stale = _age_fields("2026-06-01", 1, as_of=as_of)
        self.assertEqual(106, stale["days_in_current_state"])
        self.assertTrue(stale["is_stale"])

    def test_age_fields_handles_missing_timestamp(self) -> None:
        result = _age_fields(None, 1, as_of=date(2026, 9, 15))
        self.assertIsNone(result["days_in_current_state"])
        self.assertFalse(result["is_stale"])

    def test_age_fields_zero_or_negative_threshold_never_stale(self) -> None:
        result = _age_fields("2020-01-01", 0, as_of=date(2026, 9, 15))
        self.assertFalse(result["is_stale"])
        self.assertIsInstance(result["days_in_current_state"], int)

    def test_follow_up_items_carry_days_in_current_state_from_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            study = root / "studies/acme"
            dump(
                study / "00_manifest.yaml",
                {
                    "study_id": "acme-1",
                    "company": "Acme",
                    "company_id": "C1",
                    "product_snapshots": [],
                    "updated_at": "2026-01-01",
                },
            )
            dump(study / "05_enterprise_demand_profile.yaml", {"evidence_claims": [], "capability_gaps": [], "confidence": "low"})
            rows = FollowUpDashboard(root).items(as_of=date(2026, 9, 15))
            qualification = next(item for item in rows if item["kind"] == "qualification")
            self.assertGreater(qualification["days_in_current_state"], 200)
            self.assertTrue(qualification["is_stale"])

    def test_company_heritage_counts_derived_edges(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            study = root / "studies/acme"
            dump(study / "05b_use_case_inventory.yaml", {
                "study_id": "acme-1", "company": "Acme", "inventory_version": "1",
                "use_cases": [
                    {"use_case_id": "UC-1", "name": "Draft", "outcome_family": "quality", "dependencies": {"enables": ["UC-2"], "depends_on": []}, "reusable_assets": []},
                    {"use_case_id": "UC-2", "name": "Review", "outcome_family": "quality", "dependencies": {"enables": [], "depends_on": ["UC-1"]}, "reusable_assets": []},
                ],
            })
            heritage = UseCaseHeritage(root).company("acme-1")
            self.assertEqual(2, heritage["use_case_count"])
            self.assertGreaterEqual(heritage["edge_count"], 2)
            self.assertIn("enables", heritage["relations"])

    def test_sector_heritage_keeps_comparative_warning(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name, cid in (("a", "C1"), ("b", "C2")):
                dump(root / f"studies/{name}/05b_use_case_inventory.yaml", {"study_id": name, "company_id": cid, "company": name.upper(), "use_cases": [{"use_case_id": "UC-1", "name": "X", "outcome_family": "quality"}]})
            jsonl(root / "data/private/network/company_icb_mappings.jsonl", [
                {"company_id": "C1", "mapping_status": "validated", "sector": {"code": "301010"}},
                {"company_id": "C2", "mapping_status": "validated", "sector": {"code": "301010"}},
            ])
            heritage = UseCaseHeritage(root).sector("301010")
            self.assertEqual(2, heritage["company_count"])
            self.assertGreaterEqual(heritage["similarity_hypotheses"], 1)
            self.assertIn("never populates", heritage["warning"])

    def test_for_workspace_default_matches_legacy_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertEqual(FollowUpDashboard.for_workspace("default", repo_root=root).root, root.resolve())
            self.assertEqual(UseCaseHeritage.for_workspace("default", repo_root=root).root, root.resolve())

    def test_for_workspace_named_resolves_under_workspaces_tree(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            expected = (root / "workspaces" / "acme").resolve()
            self.assertEqual(FollowUpDashboard.for_workspace("acme", repo_root=root).root, expected)
            self.assertEqual(UseCaseHeritage.for_workspace("acme", repo_root=root).root, expected)

    def test_non_default_workspace_still_surfaces_shared_backlog_todos(self) -> None:
        # P0 Category B / §3a: artifacts/TODO_*.yaml (project dev backlog,
        # not tenant data) only ever exists at the real repo root -- a fresh
        # workspaces/<id>/ directory has none of its own, so a non-default
        # workspace's follow-up dashboard must still surface it via the
        # shared-root fallback rather than silently dropping every TODO.
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            dump(
                repo_root / "artifacts" / "TODO_release_v0_3.yaml",
                {"updated_at": "2026-08-01", "items": [{"id": "T1", "status": "open", "priority": "P1", "area": "backend", "task": "Ship it"}]},
            )
            dashboard = FollowUpDashboard.for_workspace("acme-ws", repo_root=repo_root)
            self.assertFalse((dashboard.root / "artifacts").exists())
            items = dashboard.items(as_of=date(2026, 8, 7))
            self.assertIn("TODO:T1", {item["id"] for item in items})

    def test_non_default_workspace_still_sees_shared_taxonomy_via_demand_sectors(self) -> None:
        # Same shared-root fallback, exercised through the nested
        # DemandCatalog(...).snapshot() call -- a workspace with a
        # benchmark_edge sector must still surface that sector item even
        # though the ICB taxonomy only exists at the real repo root.
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            dump(
                repo_root / "data" / "taxonomies" / "icb_v5_2026.yaml",
                {
                    "industries": [
                        {
                            "code": "30",
                            "name": "Financials",
                            "supersectors": [
                                {"code": "3010", "name": "Banks", "sectors": [{"code": "301010", "name": "Banks"}]}
                            ],
                        }
                    ]
                },
            )
            dashboard = FollowUpDashboard.for_workspace("acme-ws", repo_root=repo_root)
            for index in (1, 2):
                company_id = f"C{index}"
                study = dashboard.root / "studies" / f"bank-{index}"
                dump(study / "00_manifest.yaml", {"study_id": f"study-{index}", "company_id": company_id, "company": f"Bank {index}", "updated_at": "2026-08-01"})
                dump(study / "05_enterprise_demand_profile.yaml", {"evidence_claims": [{"claim_id": "E1"}], "capability_gaps": [{"claim_id": "G1"}], "confidence": "medium"})
            jsonl(
                dashboard.root / "data/private/network/companies.jsonl",
                [{"company_id": "C1", "canonical_name": "Bank 1"}, {"company_id": "C2", "canonical_name": "Bank 2"}],
            )
            jsonl(
                dashboard.root / "data/private/network/company_icb_mappings.jsonl",
                [
                    {"company_id": "C1", "mapping_status": "validated", "confidence": "high", "sector": {"code": "301010"}},
                    {"company_id": "C2", "mapping_status": "validated", "confidence": "high", "sector": {"code": "301010"}},
                ],
            )
            items = dashboard.items(as_of=date(2026, 8, 7))
            sector_items = [item for item in items if item["kind"] == "sector"]
            self.assertEqual(len(sector_items), 1)
            self.assertEqual(sector_items[0]["state"], "benchmark_edge")


if __name__ == "__main__":
    unittest.main()
