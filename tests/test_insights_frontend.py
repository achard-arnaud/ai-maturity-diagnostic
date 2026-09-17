from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class InsightsFrontendTests(unittest.TestCase):
    def setUp(self) -> None:
        self.spaces = (ROOT / "app/frontend/gtm-spaces.js").read_text(encoding="utf-8")
        self.server = (ROOT / "app/server.py").read_text(encoding="utf-8")

    def test_insights_is_endpoint_backed_and_exposes_decision_context(self) -> None:
        self.assertIn('/api/v1/workspaces/{workspace}/insights', self.spaces)
        for phrase in ("Funnel", "Qualité", "Coût", "LearningProposal", "Revoir et décider"):
            self.assertIn(phrase, self.spaces)

    def test_privacy_and_projection_boundaries_are_visible(self) -> None:
        self.assertIn("minimum_cohort_size", self.spaces)
        self.assertIn("projection uniquement", self.spaces)
        self.assertIn("Cohorte masquée", self.spaces)
        self.assertIn("create_v1_insights_router", self.server)


if __name__ == "__main__":
    unittest.main()
