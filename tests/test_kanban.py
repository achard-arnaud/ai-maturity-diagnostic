from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import yaml

from app.kanban import CANONICAL_STAGES, build_board


def dump(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def _column(board: dict, stage: str) -> list[dict]:
    return next(col["cards"] for col in board["columns"] if col["stage"] == stage)


class KanbanBoardTests(unittest.TestCase):
    def test_empty_repo_produces_empty_but_valid_board(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            board = build_board(Path(tmp))
            stages = [col["stage"] for col in board["columns"]]
            self.assertEqual(list(CANONICAL_STAGES), stages)
            for col in board["columns"]:
                self.assertEqual([], col["cards"])

    def test_early_qualification_study_lands_in_matching_column(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            study = root / "studies/acme"
            dump(
                study / "00_manifest.yaml",
                {"study_id": "acme-1", "company": "Acme", "company_id": "C1", "product_snapshots": [{"offer_id": "OFFER-1", "path": "inputs/x.yaml"}]},
            )
            dump(
                study / "05_enterprise_demand_profile.yaml",
                {"evidence_claims": [{"claim_id": "E1"}], "capability_gaps": [{"claim_id": "G1"}], "confidence": "medium"},
            )
            dump(study / "06_product_fit_matrix.yaml", {"matches": [], "decision": None})

            board = build_board(root)
            matching_cards = _column(board, "matching")
            self.assertEqual({"qualification", "follow_up"}, {c["source"] for c in matching_cards})
            card = next(c for c in matching_cards if c["source"] == "qualification")
            self.assertEqual("acme-1", card["study_id"])
            self.assertEqual("C1", card["company_id"])
            self.assertEqual("Acme", card["title"])
            self.assertTrue(card["actions"])
            for stage in ("demand", "product_snapshot", "contact_targeting", "reach", "pilot", "completed"):
                self.assertEqual([], _column(board, stage))

    def test_matching_invalid_folds_into_matching_column(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            study = root / "studies/acme"
            dump(
                study / "00_manifest.yaml",
                {"study_id": "acme-1", "company": "Acme", "company_id": "C1", "product_snapshots": [{"offer_id": "OFFER-1", "path": "inputs/x.yaml"}]},
            )
            dump(
                study / "05_enterprise_demand_profile.yaml",
                {"evidence_claims": [{"claim_id": "E1"}], "capability_gaps": [{"claim_id": "G1"}], "confidence": "medium"},
            )
            dump(
                study / "06_product_fit_matrix.yaml",
                {
                    "recommended_offer_id": "OFFER-1",
                    "decision": "pursue",
                    "matches": [{"offer_id": "OFFER-1", "decision": "pursue", "hard_gates": [{"id": "GATE-1", "status": "FAIL", "severity": "blocker"}]}],
                },
            )
            board = build_board(root)
            matching_cards = _column(board, "matching")
            self.assertTrue(all(c["study_id"] == "acme-1" for c in matching_cards))
            self.assertIn("qualification", {c["source"] for c in matching_cards})

    def _seed_positive_fit_study(self, root: Path, *, targets: bool = True) -> Path:
        study = root / "studies/acme"
        dump(
            study / "00_manifest.yaml",
            {"study_id": "acme-1", "company": "Acme", "company_id": "C1", "product_snapshots": [{"offer_id": "OFFER-1", "path": "inputs/x.yaml"}]},
        )
        dump(
            study / "05_enterprise_demand_profile.yaml",
            {"evidence_claims": [{"claim_id": "E1"}], "capability_gaps": [{"claim_id": "G1"}], "confidence": "medium"},
        )
        dump(
            study / "06_product_fit_matrix.yaml",
            {"recommended_offer_id": "OFFER-1", "decision": "validate", "matches": [{"offer_id": "OFFER-1", "decision": "validate", "hard_gates": []}]},
        )
        if targets:
            dump(
                study / "06b_contact_targets.yaml",
                {"study_id": "acme-1", "company_id": "C1", "offer_id": "OFFER-1", "targets": [{"person_id": "P1"}]},
            )
        return study

    def test_study_with_active_reach_preview_appears_in_reach_column(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._seed_positive_fit_study(root)
            board = build_board(root)
            reach_cards = _column(board, "reach")
            sources = {(card["study_id"], card["source"]) for card in reach_cards}
            self.assertIn(("acme-1", "reach"), sources)

    def test_completed_reach_artifact_moves_to_pilot_column(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            study = self._seed_positive_fit_study(root)
            dump(study / "06c_reach_strategy.yaml", {"stakeholders": [{"person_id": "P1", "status": "ready"}], "blockers": []})
            board = build_board(root)
            pilot_sources = {(card["study_id"], card["source"]) for card in _column(board, "pilot")}
            self.assertIn(("acme-1", "reach"), pilot_sources)

    def test_nudging_inventory_appears_in_cross_sell_column(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            study = root / "studies/acme"
            dump(
                study / "05b_use_case_inventory.yaml",
                {
                    "study_id": "acme-1",
                    "company": "Acme",
                    "inventory_version": "1",
                    "use_cases": [
                        {"use_case_id": "UC1", "maturity": "active", "repeatability": "high"},
                    ],
                },
            )
            board = build_board(root)
            cross_sell_cards = _column(board, "cross_sell")
            self.assertEqual(1, len(cross_sell_cards))
            self.assertEqual("acme-1", cross_sell_cards[0]["study_id"])
            self.assertEqual("nudging", cross_sell_cards[0]["source"])

    def test_follow_up_item_appears_in_matching_column(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            study = root / "studies/acme"
            dump(
                study / "00_manifest.yaml",
                {"study_id": "acme-1", "company": "Acme", "company_id": "C1", "product_snapshots": [{"offer_id": "OFFER-1", "path": "inputs/x.yaml"}]},
            )
            dump(
                study / "05_enterprise_demand_profile.yaml",
                {"evidence_claims": [{"claim_id": "E1"}], "capability_gaps": [{"claim_id": "G1"}], "confidence": "medium"},
            )
            dump(study / "06_product_fit_matrix.yaml", {"matches": [], "decision": None})

            board = build_board(root)
            matching_cards = _column(board, "matching")
            sources = {card["source"] for card in matching_cards}
            self.assertIn("qualification", sources)
            self.assertIn("follow_up", sources)


if __name__ == "__main__":
    unittest.main()
