from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class V10FrontendContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.js = (ROOT / "app/frontend/app.js").read_text(encoding="utf-8")
        self.css = (ROOT / "app/frontend/styles.css").read_text(encoding="utf-8")

    def test_follow_up_card_renders_age_badge(self) -> None:
        self.assertIn("ageBadge", self.js)
        self.assertIn("days_in_current_state", self.js)
        self.assertIn("is_stale", self.js)
        self.assertIn("badge-age", self.js)

    def test_stale_badge_has_dedicated_style(self) -> None:
        self.assertIn(".badge-age", self.css)
        self.assertIn(".badge-age.status-stale", self.css)


if __name__ == "__main__":
    unittest.main()
