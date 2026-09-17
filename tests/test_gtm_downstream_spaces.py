from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class GtmDownstreamSpaceTests(unittest.TestCase):
    def test_engagement_and_pipeline_use_canonical_endpoints(self) -> None:
        source = (ROOT / "app/frontend/gtm-spaces.js").read_text(encoding="utf-8")
        self.assertIn("/conversations", source)
        self.assertIn("/opportunities/pipeline-board", source)
        self.assertIn("payload.stages", source)

    def test_insights_boundary_and_admin_link_are_explicit(self) -> None:
        source = (ROOT / "app/frontend/gtm-spaces.js").read_text(encoding="utf-8")
        self.assertIn("ne modifieront aucune vérité métier", source)
        self.assertIn('/admin/workspaces', source)

if __name__ == "__main__":
    unittest.main()
