from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class V06FrontendContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.html = (ROOT / "app/frontend/index.html").read_text(encoding="utf-8")
        self.js = (ROOT / "app/frontend/app.js").read_text(encoding="utf-8")

    def test_primary_menus_exist(self) -> None:
        for label in ("Demande", "Offres", "Qualification", "Nudging"):
            self.assertIn(f">{label}<", self.html)

    def test_demand_ctas_are_user_visible(self) -> None:
        for phrase in (
            "Ajouter un contact",
            "Ajouter / MAJ use flow",
            "Ajouter une 3e entreprise",
            "Lancer le benchmark",
            "Récolter / consolider use cases",
            "Parcours complet",
        ):
            self.assertIn(phrase, self.html + self.js)

    def test_nudging_modes_are_visible_and_separate(self) -> None:
        for phrase in ("Productivisation", "Upsell par dépendance", "Cross-sell package"):
            self.assertIn(phrase, self.html)
        self.assertIn("ne charge ni ICB", self.html)
        self.assertIn("/api/nudging/generate", self.js)

    def test_qualification_exposes_next_and_full_flow(self) -> None:
        self.assertIn("Qualification & matching", self.html)
        self.assertIn("qualNextBtn", self.js)
        self.assertIn("qualFlowBtn", self.js)
        self.assertIn("/api/workflows/plan", self.js)


if __name__ == "__main__":
    unittest.main()
