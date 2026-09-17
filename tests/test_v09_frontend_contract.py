from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class V09FrontendContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.html = (ROOT / "app/frontend/index.html").read_text(encoding="utf-8")
        self.js = (ROOT / "app/frontend/app.js").read_text(encoding="utf-8")
        self.css = (ROOT / "app/frontend/styles.css").read_text(encoding="utf-8")

    def test_catalog_search_cta_is_wired(self) -> None:
        self.assertIn('id="catalogSearchQuery"', self.html)
        self.assertIn('id="catalogSearchBtn"', self.html)
        self.assertIn("/api/catalog/search", self.js)
        self.assertIn("runCatalogSearch", self.js)

    def test_network_people_and_companies_search_ctas_are_wired(self) -> None:
        self.assertIn('id="peopleSearchForm"', self.html)
        self.assertIn('id="companiesSearchForm"', self.html)
        self.assertIn("/api/network/people", self.js)
        self.assertIn("/api/network/companies", self.js)
        self.assertIn("runPeopleSearch", self.js)
        self.assertIn("runCompaniesSearch", self.js)

    def test_structured_contact_and_company_creation_forms_exist(self) -> None:
        self.assertIn('id="createPersonForm"', self.html)
        self.assertIn('id="createCompanyForm"', self.html)
        self.assertIn('"/api/network/people"', self.js)
        self.assertIn('"/api/network/companies"', self.js)
        self.assertIn("confirmation-banner", self.js)

    def test_demand_intake_form_is_wired(self) -> None:
        self.assertIn('id="demandIntakeForm"', self.html)
        self.assertIn('id="demandIntakeCompany"', self.html)
        self.assertIn('id="demandIntakeProblem"', self.html)
        self.assertIn('"/api/demand/intake"', self.js)
        self.assertIn("confirmation-banner", self.js)

    def test_invoke_panel_shows_executor_not_configured_banner(self) -> None:
        self.assertIn('id="executorBanner"', self.html)
        self.assertIn("executorConfigured", self.js)

    def test_invoke_panel_has_structured_contact_fields(self) -> None:
        self.assertIn('id="contactStructName"', self.html)
        self.assertIn('id="contactStructEmail"', self.html)
        self.assertIn('id="contactStructCompany"', self.html)

    def test_catalog_candidates_route_and_promote_cta_exist(self) -> None:
        self.assertIn("/api/catalog/candidates", self.js)
        self.assertIn("promoteCandidateBtn", self.js)
        self.assertIn("/promote", self.js)

    def test_candidates_filter_bar_is_wired(self) -> None:
        self.assertIn('id="candidatesFilterForm"', self.html)
        self.assertIn('id="candidatesFilterText"', self.html)
        self.assertIn('id="candidatesFilterStatus"', self.html)
        self.assertIn('id="candidatesFilterShelf"', self.html)
        self.assertIn('id="candidatesFilterCompany"', self.html)
        self.assertIn("candidatesFilterForm", self.js)
        self.assertIn("loadCandidates", self.js)

    def test_candidate_detail_view_reuses_data_panel(self) -> None:
        self.assertIn("openCandidateDetail", self.js)
        self.assertIn("viewCandidateBtn", self.js)
        self.assertIn("/api/catalog/candidates/${encodeURIComponent(candidateId)}", self.js)
        self.assertIn("openDataPanel", self.js)

    def test_offer_edit_form_calls_patch_offer_route(self) -> None:
        self.assertIn("openOfferEditForm", self.js)
        self.assertIn("offerEditBtn", self.js)
        self.assertIn("method: \"PATCH\"", self.js)
        self.assertIn("/api/catalog/offers/", self.js)

    def test_kanban_board_is_rendered_from_real_endpoint(self) -> None:
        self.assertIn("/api/kanban/board", self.js)
        self.assertIn("renderKanbanInto", self.js)
        self.assertIn("kanban-board", self.css)
        self.assertIn('aria-label="Kanban pipeline"', self.html)

    def test_campaigns_prospecting_and_cross_sell_ctas_exist(self) -> None:
        self.assertIn("/api/campaigns/prospecting", self.js)
        self.assertIn("/api/campaigns/cross-sell", self.js)
        self.assertIn("/api/campaigns", self.js)
        self.assertIn("crossSellBtn", self.js)

    def test_campaign_mark_sent_cta_exists(self) -> None:
        self.assertIn("markCampaignSentBtn", self.js)
        self.assertIn("markCampaignSent", self.js)
        self.assertIn("/mark-sent", self.js)
        self.assertIn("Marquer envoy", self.js)

    def test_account_360_view_is_wired(self) -> None:
        self.assertIn("/api/accounts/", self.js)
        self.assertIn("openAccount360", self.js)
        self.assertIn("open360Btn", self.js)

    def test_admin_link_shown_for_admin_users(self) -> None:
        self.assertIn("/admin/workspaces", self.js)
        self.assertIn("is_admin", self.js)

    def test_duplicate_detection_and_reassign_are_wired(self) -> None:
        self.assertIn("/api/network/duplicates", self.js)
        self.assertIn("loadDuplicates", self.js)
        self.assertIn("/reassign", self.js)

    def test_blocker_actions_journal_view_is_wired(self) -> None:
        self.assertIn('data-space="insights"', self.html)
        self.assertIn('id="journal" class="panel"', self.html)
        self.assertIn('id="blockerActionsFilterForm"', self.html)
        self.assertIn('id="blockerActionsStudyId"', self.html)
        self.assertIn('id="blockerActionsCompanyId"', self.html)
        self.assertIn('id="blockerActionsStepId"', self.html)
        self.assertIn('id="blockerActionsAction"', self.html)
        self.assertIn('id="blockerActionsSince"', self.html)
        self.assertIn('id="blockerActionsUntil"', self.html)
        self.assertIn('id="blockerActionsRows"', self.html)
        self.assertIn("/api/blocker-actions", self.js)
        self.assertIn("loadBlockerActions", self.js)


if __name__ == "__main__":
    unittest.main()
