from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class GtmShellQualityTests(unittest.TestCase):
    def test_navigation_has_telemetry_and_rollback_flag(self) -> None:
        router = (ROOT / "app/frontend/router.js").read_text(encoding="utf-8")
        self.assertIn('gtm:navigation', router)
        self.assertIn('legacy', router)
        self.assertIn('CustomEvent', router)

    def test_accessibility_and_mobile_contracts(self) -> None:
        app = (ROOT / "app/frontend/app.js").read_text(encoding="utf-8")
        css = (ROOT / "app/frontend/styles.css").read_text(encoding="utf-8")
        self.assertIn('aria-current', app)
        self.assertIn('focus-visible', css)
        self.assertIn('@media (max-width: 720px)', css)
        self.assertIn('min-height: 44px', css)

    def test_legacy_panels_remain_for_one_release_but_not_in_primary_nav(self) -> None:
        html = (ROOT / "app/frontend/index.html").read_text(encoding="utf-8")
        self.assertIn('id="qualification"', html)
        self.assertIn('id="legacyNav" class="hidden"', html)
        self.assertIn('data-legacy-target="qualification">Qualification</button>', html)
        primary_nav = html.split('id="gtmNav"', 1)[1].split("</nav>", 1)[0]
        self.assertNotIn('>Qualification</button>', primary_nav)

if __name__ == "__main__":
    unittest.main()
