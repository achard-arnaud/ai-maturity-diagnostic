import { test, expect } from "@playwright/test";
import { assertLoginRedirectWorks, STORAGE_STATE } from "./helpers";

/**
 * Journey C — starting from adding a company.
 *
 * Generic skill-invoke facade (same drawer/skill family as contact intake,
 * network-contact-intake) -> [GAP] /api/network/companies search CTA ->
 * existing rich company drill-down in the Demande tab (ICB/sector
 * intelligence: org, heritage, qualification, value chain, uc-graph — this
 * ALREADY WORKS) -> [GAP] no bridge/reconciliation between the network-layer
 * company (companies.jsonl) and the ICB/sector-intelligence company concept
 * -> [GAP] kanban.
 */

test.describe("Journey C - company (login)", () => {
  test("unauthenticated access redirects to the login page", async ({ page }) => {
    await assertLoginRedirectWorks(page);
  });
});

test.describe("Journey C - company (authenticated)", () => {
  test.use({ storageState: STORAGE_STATE });

  test.beforeEach(async ({ page }) => {
    await page.goto("/");
  });

  test("adding a company from the sector view opens the same generic skill-invoke drawer", async ({ page }) => {
    await page.getByRole("button", { name: "Demande", exact: true }).click();
    await expect(page.locator("#demand.panel.active")).toBeVisible();
    const primaryBtn = page.locator(".sectorPrimaryBtn").first();
    if (await primaryBtn.count()) {
      await primaryBtn.click();
      // Built today: sector "add company"/"add third company" CTAs route
      // through the same network-contact-intake skill-invoke drawer used
      // for individual contacts — there is no company-specific facade.
      await expect(page.locator("#invokePanel")).not.toHaveClass(/hidden/);
      await expect(page.locator("#invokeTitle")).toContainText(/network-contact-intake|sector-intelligence-consolidation/);
    } else {
      test.skip(true, "No sector card present in this environment's demand grid.");
    }
  });

  test("GAP: company intake is a structured form, not a raw prompt textarea", async ({ page }) => {
    await page.getByRole("button", { name: "Demande", exact: true }).click();
    const primaryBtn = page.locator(".sectorPrimaryBtn").first();
    if (!(await primaryBtn.count())) {
      test.skip(true, "No sector card present in this environment's demand grid.");
      return;
    }
    await primaryBtn.click();
    await expect(page.locator("#invokePanel")).not.toHaveClass(/hidden/);

    // GAP: same facade issue as Journey B — #invokeInput is a single
    // freeform textarea; there is no structured company name / domain /
    // sector field anywhere in this drawer.
    await expect(page.getByLabel(/^Nom de l.entreprise$/i)).toBeVisible();
    await expect(page.getByLabel(/^Domaine$/i)).toBeVisible();
  });

  test("GAP: /api/network/companies is searchable from the UI", async ({ page }) => {
    // GAP: /api/network/companies is built server-side but has no
    // call-to-action anywhere in the frontend — no nav entry, no search
    // box, no results list for network-layer companies (companies.jsonl).
    await expect(page.getByRole("button", { name: /Entreprises \(réseau\)|Companies/i })).toBeVisible();
  });

  test("the existing ICB/sector company drill-down in Demande already works", async ({ page }) => {
    await page.getByRole("button", { name: "Demande", exact: true }).click();
    const detailBtn = page.locator(".sectorDetailBtn").first();
    if (!(await detailBtn.count())) {
      test.skip(true, "No sector card present in this environment's demand grid.");
      return;
    }
    await detailBtn.click();
    await expect(page.locator("#sectorDetail")).not.toHaveClass(/hidden/);

    const companyOrgBtn = page.locator(".companyOrgBtn").first();
    const companyHeritageBtn = page.locator(".companyHeritageBtn").first();
    const companyFlowBtn = page.locator(".companyFlowBtn").first();
    const companyQualBtn = page.locator(".companyQualBtn").first();

    if (await companyOrgBtn.count()) {
      // Org/heritage/qualification/value-chain drill-down all exist today.
      await expect(companyOrgBtn).toBeVisible();
      await expect(companyHeritageBtn).toBeVisible();
      await expect(companyFlowBtn).toBeVisible();
      await expect(companyQualBtn).toBeVisible();

      await companyHeritageBtn.click();
      await expect(page.locator("#dataPanel")).not.toHaveClass(/hidden/);
      await expect(page.locator("#dataTitle")).toContainText("Patrimoine UC");
    } else {
      test.skip(true, "No mapped company/study present in this environment's sector detail to drill into.");
    }
  });

  test("use-case graph (Mermaid) renders for a company in the Demande drill-down", async ({ page }) => {
    await page.getByRole("button", { name: "Demande", exact: true }).click();
    const detailBtn = page.locator(".sectorDetailBtn").first();
    if (!(await detailBtn.count())) {
      test.skip(true, "No sector card present in this environment's demand grid.");
      return;
    }
    await detailBtn.click();
    const ucGraphBtn = page.locator(".ucGraphBtn").first();
    if (await ucGraphBtn.count()) {
      await ucGraphBtn.click();
      await expect(page.locator("#dataPanel")).not.toHaveClass(/hidden/);
      await expect(page.locator("#dataContent .mermaid")).toBeVisible();
    } else {
      test.skip(true, "No mapped company/study present in this environment's sector detail to open the UC graph for.");
    }
  });

  test("GAP: a visible bridge reconciles the network-layer company with the ICB/sector-intelligence company", async ({ page }) => {
    await page.getByRole("button", { name: "Demande", exact: true }).click();
    const detailBtn = page.locator(".sectorDetailBtn").first();
    if (!(await detailBtn.count())) {
      test.skip(true, "No sector card present in this environment's demand grid.");
      return;
    }
    await detailBtn.click();

    // GAP: the company shown here (ICB/sector-intelligence, keyed by
    // study_id) is a different record from the network-layer company in
    // companies.jsonl (created via network-contact-intake). Nothing in the
    // sector detail or company drill-down links, cross-references, or lets
    // a user reconcile the two — no "same company as <network company>"
    // affordance exists.
    await expect(page.getByText(/Lié à l.entreprise réseau|Rapprocher avec/i)).toBeVisible();
  });

  test("GAP: company records and their pipeline stage are organized on a shared kanban board", async ({ page }) => {
    // GAP: no kanban exists anywhere in the app for companies either —
    // sector/company progress is shown as badges (benchmark_state,
    // eligible/mapped counts) on cards, not a stage-tracked board.
    await page.getByRole("button", { name: "Demande", exact: true }).click();
    await expect(page.getByRole("region", { name: /Kanban/i })).toBeVisible();
  });
});
