from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class GtmRouterContractTests(unittest.TestCase):
    def test_job_spaces_and_router_are_wired(self) -> None:
        html = (ROOT / "app/frontend/index.html").read_text(encoding="utf-8")
        for space in ("home", "discover", "research", "fit", "targets", "reach", "engagement", "pipeline", "insights"):
            self.assertIn(f'data-space="{space}"', html)
        self.assertLess(html.index('/router.js'), html.index('/app.js'))

    def test_router_uses_history_and_authoritative_workspace(self) -> None:
        router = (ROOT / "app/frontend/router.js").read_text(encoding="utf-8")
        self.assertIn("pushState", router)
        self.assertIn("popstate", router)
        self.assertIn("current.workspace !== workspaceId", router)
        self.assertNotIn("localStorage", router)

if __name__ == "__main__":
    unittest.main()
