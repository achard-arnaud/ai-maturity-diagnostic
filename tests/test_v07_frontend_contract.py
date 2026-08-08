from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class V07FrontendContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.html = (ROOT / "app/frontend/index.html").read_text(encoding="utf-8")
        self.js = (ROOT / "app/frontend/app.js").read_text(encoding="utf-8")
        self.css = (ROOT / "app/frontend/styles.css").read_text(encoding="utf-8")

    def test_primary_navigation_stays_compact(self) -> None:
        for label in ("Demande", "Offres", "Qualification", "Nudging", "Suivi", "Skills"):
            self.assertIn(f">{label}<", self.html)
        self.assertNotIn('data-target="reach"', self.html)

    def test_company_deep_dive_exposes_value_chain_and_uc_heritage(self) -> None:
        self.assertIn("Analyse chaîne de valeur", self.js)
        self.assertIn("Patrimoine UC", self.html + self.js)
        self.assertIn("Organisation", self.js)
        self.assertIn("Parcours entreprise", self.js)
        self.assertIn("/api/value-chain/prepare", self.js)
        self.assertIn("/api/heritage/company", self.js)
        self.assertIn("/api/heritage/sector", self.js)

    def test_reach_is_contextual_after_qualification(self) -> None:
        self.assertIn("Qualification, matching & reach", self.html)
        self.assertIn("First wave", self.js)
        self.assertIn("Second wave", self.js)
        self.assertIn("Validation only", self.js)
        self.assertIn("/api/reach/preview", self.js)
        self.assertIn("/api/reach/prepare", self.js)

    def test_blocked_steps_have_resolver_ui_instead_of_disabled_workflow_buttons(self) -> None:
        self.assertIn("resolverButton", self.js)
        self.assertIn("bindResolverButtons", self.js)
        self.assertIn("Besoin :", self.js)
        self.assertIn("Après :", self.js)
        self.assertNotIn('step.status === "blocked" ? "disabled"', self.js)
        self.assertIn(".blocker-card", self.css)

    def test_zettelkasten_is_implemented_as_derived_graph_not_new_menu(self) -> None:
        self.assertIn("Graphe dérivé", self.js)
        self.assertIn("Aucun second store canonique", self.js)
        self.assertNotIn(">Zettelkasten<", self.html)


if __name__ == "__main__":
    unittest.main()
