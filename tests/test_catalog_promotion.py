from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import yaml

from app.catalog import CatalogHarvester
from app.catalog_promotion import (
    get_staged_candidate,
    list_staged_candidates,
    promote_candidate,
    update_offer_sheet,
)
from app.core import ControlPlaneError


def _write_shelves(root: Path) -> None:
    shelves_dir = root / "catalog_sources"
    shelves_dir.mkdir(parents=True, exist_ok=True)
    (shelves_dir / "shelves.yaml").write_text(
        yaml.safe_dump({"shelves": [{"shelf_id": "shelf-1"}]}), encoding="utf-8"
    )


def _write_index(root: Path, offers: list[dict]) -> None:
    (root / "product_catalog").mkdir(parents=True, exist_ok=True)
    (root / "product_catalog" / "index.yaml").write_text(
        yaml.safe_dump({"schema_version": "0.2", "offers": offers}), encoding="utf-8"
    )


def _write_offer(root: Path, offer_id: str, file_name: str, extra: dict | None = None) -> None:
    offer = {
        "offer_id": offer_id,
        "name": "Existing Offer",
        "profile_version": "v1",
        "status": "sourced",
        "positioning": {"one_liner": "old"},
        "problem": {"canonical": "old problem"},
        "outcomes": {"primary": []},
        "icp": {},
        "hard_gates": [{"id": "G1", "test": "x", "severity": "blocker"}],
        "proof": {"evidence_status": "old", "epistemic_status": "vendor_claim"},
    }
    if extra:
        offer.update(extra)
    (root / "product_catalog" / file_name).write_text(
        yaml.safe_dump({"schema_version": "0.2", "offer": offer}), encoding="utf-8"
    )


class CatalogPromotionTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        _write_shelves(self.root)
        _write_index(self.root, [])

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _stage_one(self, *, with_source: bool = True) -> str:
        harvester = CatalogHarvester(self.root)
        item = {"name": "Widgetron"}
        if with_source:
            item["source_url"] = "https://widgetron.example/"
            item["raw_claims"] = ["Automates widget assembly."]
        result = harvester.stage({"company": "Widgetron Inc", "shelf_id": "shelf-1", "items": [item]})
        candidates = list_staged_candidates(self.root)
        self.assertEqual(len(candidates), 1)
        return candidates[0]["id"]

    def test_list_staged_candidates_reads_harvested_items(self) -> None:
        candidate_id = self._stage_one()
        candidates = list_staged_candidates(self.root)
        self.assertEqual(candidates[0]["name"], "Widgetron")
        self.assertEqual(candidates[0]["id"], candidate_id)

    def test_list_staged_candidates_with_no_filters_is_unchanged(self) -> None:
        self._stage_one()
        unfiltered = list_staged_candidates(self.root)
        self.assertEqual(len(unfiltered), 1)

    def test_list_staged_candidates_filters_by_text(self) -> None:
        self._stage_one()
        self.assertEqual(len(list_staged_candidates(self.root, text="widget")), 1)
        self.assertEqual(len(list_staged_candidates(self.root, text="nomatch")), 0)

    def test_list_staged_candidates_filters_by_company_and_shelf(self) -> None:
        self._stage_one()
        self.assertEqual(len(list_staged_candidates(self.root, company="Widgetron Inc")), 1)
        self.assertEqual(len(list_staged_candidates(self.root, company="Other Co")), 0)
        self.assertEqual(len(list_staged_candidates(self.root, shelf_id="shelf-1")), 1)
        self.assertEqual(len(list_staged_candidates(self.root, shelf_id="shelf-9")), 0)

    def test_list_staged_candidates_filters_by_promotion_status(self) -> None:
        self._stage_one()
        self.assertEqual(len(list_staged_candidates(self.root, promotion_status="promoted")), 0)

    def test_get_staged_candidate_returns_full_detail(self) -> None:
        candidate_id = self._stage_one()
        candidate = get_staged_candidate(self.root, candidate_id)
        self.assertEqual(candidate["id"], candidate_id)
        self.assertEqual(candidate["name"], "Widgetron")
        self.assertIn("raw_claims", candidate)
        self.assertIn("source_url", candidate)

    def test_get_staged_candidate_rejects_unknown_id(self) -> None:
        with self.assertRaises(ControlPlaneError):
            get_staged_candidate(self.root, "bogus:CAND-999")

    def test_promote_candidate_creates_schema_conformant_offer(self) -> None:
        candidate_id = self._stage_one()
        offer = promote_candidate(self.root, candidate_id, offer_id="OFFER-WD-01")

        for field in ["offer_id", "profile_version", "positioning", "problem", "outcomes", "icp", "hard_gates", "proof"]:
            self.assertIn(field, offer)
        self.assertEqual(offer["offer_id"], "OFFER-WD-01")
        self.assertEqual(offer["proof"]["epistemic_status"], "vendor_claim")

        offer_path = self.root / "product_catalog" / "OFFER-WD-01.yaml"
        self.assertTrue(offer_path.is_file())
        on_disk = yaml.safe_load(offer_path.read_text(encoding="utf-8"))
        self.assertEqual(on_disk["offer"]["offer_id"], "OFFER-WD-01")

        index = yaml.safe_load((self.root / "product_catalog" / "index.yaml").read_text(encoding="utf-8"))
        offer_ids = {entry["offer_id"] for entry in index["offers"]}
        self.assertIn("OFFER-WD-01", offer_ids)

    def test_promote_candidate_missing_source_data_produces_honest_unknowns(self) -> None:
        candidate_id = self._stage_one(with_source=False)
        offer = promote_candidate(self.root, candidate_id, offer_id="OFFER-WD-02")
        self.assertEqual(offer["proof"]["epistemic_status"], "hypothesis")
        self.assertGreater(len(offer["unknowns"]), 0)
        self.assertIsNone(offer["problem"]["canonical"])
        self.assertEqual(offer["hard_gates"], [])

    def test_promote_candidate_rejects_unknown_candidate_id(self) -> None:
        with self.assertRaises(ControlPlaneError):
            promote_candidate(self.root, "bogus:CAND-999", offer_id="OFFER-X")

    def test_promote_candidate_rejects_existing_offer_id(self) -> None:
        _write_offer(self.root, "OFFER-EXIST-01", "OFFER-EXIST-01.yaml")
        _write_index(self.root, [{"offer_id": "OFFER-EXIST-01", "file": "OFFER-EXIST-01.yaml", "name": "Existing"}])
        candidate_id = self._stage_one()
        with self.assertRaises(ControlPlaneError):
            promote_candidate(self.root, candidate_id, offer_id="OFFER-EXIST-01")

    def test_update_offer_sheet_updates_only_allowed_fields(self) -> None:
        _write_offer(self.root, "OFFER-EXIST-01", "OFFER-EXIST-01.yaml")
        _write_index(self.root, [{"offer_id": "OFFER-EXIST-01", "file": "OFFER-EXIST-01.yaml", "name": "Existing"}])
        updated = update_offer_sheet(
            self.root,
            "OFFER-EXIST-01",
            {"positioning": {"one_liner": "new one-liner"}},
            workspace_id="ws1",
        )
        self.assertEqual(updated["positioning"]["one_liner"], "new one-liner")
        self.assertEqual(updated["problem"]["canonical"], "old problem")

        on_disk = yaml.safe_load((self.root / "product_catalog" / "OFFER-EXIST-01.yaml").read_text(encoding="utf-8"))
        self.assertEqual(on_disk["offer"]["positioning"]["one_liner"], "new one-liner")

    def test_update_offer_sheet_rejects_hard_gates_and_proof_edits(self) -> None:
        _write_offer(self.root, "OFFER-EXIST-01", "OFFER-EXIST-01.yaml")
        _write_index(self.root, [{"offer_id": "OFFER-EXIST-01", "file": "OFFER-EXIST-01.yaml", "name": "Existing"}])
        with self.assertRaises(ControlPlaneError):
            update_offer_sheet(self.root, "OFFER-EXIST-01", {"hard_gates": []})
        with self.assertRaises(ControlPlaneError):
            update_offer_sheet(self.root, "OFFER-EXIST-01", {"proof": {"evidence_status": "hacked"}})

    def test_update_offer_sheet_rejects_unknown_offer_id(self) -> None:
        with self.assertRaises(ControlPlaneError):
            update_offer_sheet(self.root, "OFFER-NOPE", {"positioning": {}})


if __name__ == "__main__":
    unittest.main()
