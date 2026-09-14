from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class V08FrontendContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.html = (ROOT / "app/frontend/index.html").read_text(encoding="utf-8")
        self.js = (ROOT / "app/frontend/app.js").read_text(encoding="utf-8")
        self.css = (ROOT / "app/frontend/styles.css").read_text(encoding="utf-8")

    def test_uc_graph_has_a_real_cta_wired_to_the_backend_endpoint(self) -> None:
        # The uc-graph endpoints existed server-side with zero frontend trigger before
        # this sprint (S6 D1). There must now be a CTA that calls them directly.
        self.assertIn("/api/uc-graph/company", self.js)
        self.assertIn("/api/uc-graph/sector", self.js)
        self.assertIn("ucGraphBtn", self.js + self.html)

    def test_uc_graph_modal_follows_the_existing_drawer_pattern(self) -> None:
        # Follows the existing openReach / openWorkflow contextual-drawer convention
        # (no new UI paradigm), rendering into the existing #dataPanel drawer.
        self.assertIn("openUseCaseGraph", self.js)
        self.assertIn("dataPanel", self.js)

    def test_mermaid_is_vendored_locally_not_loaded_from_a_cdn(self) -> None:
        # Decision point: this project has zero existing CDN/external <script src="http…">
        # references (fully local-first static frontend served by a stdlib http.server
        # with no CDN allowlist), so mermaid.js is vendored under app/frontend/vendor/
        # rather than introducing the project's first external network dependency.
        self.assertNotIn("cdn.jsdelivr.net", self.html)
        self.assertNotIn("unpkg.com", self.html)
        self.assertIn("vendor/mermaid", self.html)
        self.assertTrue((ROOT / "app/frontend/vendor/mermaid.min.js").is_file())

    def test_mermaid_translation_is_a_pure_structural_mapping_of_backend_json(self) -> None:
        # The frontend must not compute graph semantics; it only reshapes the
        # already-derived node/edge JSON from /api/uc-graph/* into Mermaid syntax.
        self.assertIn("function buildMermaidGraph", self.js)
        self.assertIn("graph TD", self.js)

    def test_blocker_cards_expose_kill_step_back_and_force_actions(self) -> None:
        self.assertIn("blockerActionBtn", self.js)
        self.assertIn("data-action=\"cancel\"", self.js)
        self.assertIn("data-action=\"step_back\"", self.js)
        self.assertIn("data-action=\"force\"", self.js)
        self.assertIn("/api/qualification/actions", self.js)
        self.assertIn(".blocker-actions", self.css)

    def test_add_new_person_action_is_explicitly_deferred(self) -> None:
        # Not implemented in this sprint: needs product clarification on where a
        # person gets added and what data it requires. Guard against silently
        # inventing it later without going through the same TDD/spec process.
        self.assertNotIn("addPersonBtn", self.js)


if __name__ == "__main__":
    unittest.main()
