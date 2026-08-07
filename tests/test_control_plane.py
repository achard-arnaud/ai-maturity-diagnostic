from __future__ import annotations

import os
import unittest
from pathlib import Path

from app.core import ControlPlaneError, RepoControlPlane

ROOT = Path(__file__).resolve().parents[1]


class ControlPlaneTests(unittest.TestCase):
    def setUp(self) -> None:
        self.control = RepoControlPlane(ROOT)
        self.previous_executor = os.environ.pop("AI_DIAGNOSTIC_SKILL_EXECUTOR", None)

    def tearDown(self) -> None:
        if self.previous_executor is not None:
            os.environ["AI_DIAGNOSTIC_SKILL_EXECUTOR"] = self.previous_executor
        else:
            os.environ.pop("AI_DIAGNOSTIC_SKILL_EXECUTOR", None)

    def test_skill_registry_discovers_atomic_packages(self) -> None:
        skill_ids = {item["id"] for item in self.control.list_skills()}
        self.assertIn("qualification-tunnel-router", skill_ids)
        self.assertIn("product-icp-intelligence", skill_ids)
        self.assertIn("nice-output-engine", skill_ids)

    def test_prepared_invocation_is_honest_without_executor(self) -> None:
        result = self.control.invoke(
            "product-icp-intelligence",
            {"input": "Audit one canonical offer", "context_paths": ["product_catalog/index.yaml"]},
        )
        self.assertEqual("prepared", result["status"])
        self.assertFalse(result["executor_configured"])
        self.assertEqual("unit", result["invocation"]["mode"])
        self.assertEqual("product-icp-intelligence", result["invocation"]["skill"]["id"])

    def test_invocation_rejects_path_escape(self) -> None:
        with self.assertRaises(ControlPlaneError):
            self.control.build_invocation(
                "product-icp-intelligence",
                {"input": "x", "context_paths": ["../outside"]},
            )

    def test_offers_and_shelves_reference_existing_catalog(self) -> None:
        offers = {item["offer_id"] for item in self.control.list_offers()}
        self.assertIn("OFFER-AF-01", offers)
        self.assertIn("OFFER-LD-01", offers)
        for shelf in self.control.list_shelves():
            for offer_id in shelf.get("offer_ids", []):
                self.assertIn(offer_id, offers)

    def test_backlog_keeps_historical_release_items_visible(self) -> None:
        ids = {item["id"] for item in self.control.backlog()}
        self.assertIn("TODO-REL-001", ids)
        self.assertIn("TODO-V05-007", ids)


if __name__ == "__main__":
    unittest.main()
