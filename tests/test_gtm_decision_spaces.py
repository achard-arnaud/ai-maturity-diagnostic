from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class GtmDecisionSpaceTests(unittest.TestCase):
    def test_fit_targets_reach_use_v1_workspace_endpoints(self) -> None:
        source = (ROOT / "app/frontend/gtm-spaces.js").read_text(encoding="utf-8")
        for resource in ("fit-assessments", "target-plans", "sequences"):
            self.assertIn(f'/api/v1/workspaces/{{workspace}}/{resource}', source)

    def test_fit_gates_are_visible(self) -> None:
        source = (ROOT / "app/frontend/gtm-spaces.js").read_text(encoding="utf-8")
        self.assertIn("item.gates", source)
        self.assertIn("bloqué", source)

if __name__ == "__main__":
    unittest.main()
