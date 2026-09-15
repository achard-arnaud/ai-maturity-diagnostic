from __future__ import annotations

import re
import tempfile
import unittest
from pathlib import Path

import yaml

from app.kanban import CANONICAL_STAGES, _QUALIFICATION_STAGE_ALIASES, build_board

_QUALIFICATION_SOURCE = Path(__file__).resolve().parent.parent / "app" / "qualification.py"


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

    def test_kanban_covers_every_qualification_stage_literal(self) -> None:
        """C1 (red-team-spec): _QUALIFICATION_STAGE_ALIASES is a hand-maintained
        table reconciling QualificationCockpit's stage vocabulary with kanban's
        CANONICAL_STAGES. Nothing else lints it against qualification.py's actual
        stage values, so it can silently go stale if a new stage literal is
        introduced upstream. This test extracts every string assigned to the
        local `stage` variable in app/qualification.py's stage-assignment logic
        (the same `stage, next_skill, next_action, ... = "..."` tuple-assignment
        pattern used throughout that function) and asserts each one is either a
        CANONICAL_STAGES member outright or has an alias in
        _QUALIFICATION_STAGE_ALIASES that maps it into one. It fails loudly
        (rather than just silently defaulting to "demand" via
        `_qualification_stage`) the moment a new stage literal appears in
        qualification.py without a matching kanban update.
        """
        source = _QUALIFICATION_SOURCE.read_text(encoding="utf-8")
        # Matches each `stage, next_skill, ... = "demand", ...` (or a ternary like
        # `stage, ... = "matching" if not fit_violation else "matching_invalid", ...`)
        # line individually, then pulls every quoted string literal out of just
        # that line's right-hand side, so unrelated `else "..."` expressions
        # elsewhere in the file are never picked up.
        stage_literals: set[str] = set()
        for line in source.splitlines():
            if not re.match(r"\s*stage,.*=", line):
                continue
            rhs = line.split("=", 1)[1]
            # `stage` is always the first name on the left, so its value is the
            # first comma-separated expression on the right (a plain literal, or
            # a `"a" if cond else "b"` ternary) -- take only that first slot's
            # literal(s), not every literal in the whole tuple assignment.
            first_slot = rhs.split(",", 1)[0]
            stage_literals.update(re.findall(r'"([^"]+)"', first_slot))
        self.assertTrue(stage_literals, "expected to find at least one stage literal in app/qualification.py")
        uncovered = sorted(
            literal
            for literal in stage_literals
            if literal not in CANONICAL_STAGES and literal not in _QUALIFICATION_STAGE_ALIASES
        )
        self.assertEqual(
            [],
            uncovered,
            "qualification.py stage literal(s) not covered by kanban's CANONICAL_STAGES "
            f"or _QUALIFICATION_STAGE_ALIASES: {uncovered!r} -- update app/kanban.py",
        )


if __name__ == "__main__":
    unittest.main()
