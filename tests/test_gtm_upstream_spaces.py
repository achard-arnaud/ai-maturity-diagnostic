from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class GtmUpstreamSpaceTests(unittest.TestCase):
    def test_home_discover_research_use_real_endpoints(self) -> None:
        source = (ROOT / "app/frontend/gtm-spaces.js").read_text(encoding="utf-8")
        for endpoint in ("/api/follow-up", "/signals", "/research-cases"):
            self.assertIn(endpoint, source)
        self.assertIn("{workspace}", source)
        self.assertNotIn("localStorage", source)

    def test_new_shell_has_one_route_owned_view(self) -> None:
        html = (ROOT / "app/frontend/index.html").read_text(encoding="utf-8")
        self.assertIn('id="gtmSpace"', html)
        self.assertEqual(9, html.count('data-target="gtmSpace"'))

if __name__ == "__main__":
    unittest.main()
