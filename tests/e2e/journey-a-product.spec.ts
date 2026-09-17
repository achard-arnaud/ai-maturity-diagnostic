import { test, expect } from "@playwright/test";
import { assertLoginRedirectWorks, STORAGE_STATE } from "./helpers";

/**
 * Journey A — starting from adding a product (catalog offer).
 *
 * Offres tab -> discover/import catalog forms -> [GAP] review/promote to
 * canonical product_catalog/*.yaml -> [GAP] "my product" owner-edit screen
 * -> [GAP] /api/catalog/search CTA -> matching to demand (Opportunités) ->
 * Qualification tab -> [GAP] rerun any pipeline evidence/synthesis step ->
 * Suivi tab -> Nudging cross-sell -> [GAP] shared kanban across Suivi/Nudging.
 */

test.describe("Journey A - product/offer (login)", () => {
  test("unauthenticated access redirects to the login page", async ({ page }) => {
    await assertLoginRedirectWorks(page);
  });
});

test.describe("Journey A - product/offer (authenticated)", () => {
  test.use({ storageState: STORAGE_STATE });

  test.beforeEach(async ({ page }) => {
    await page.goto("/?legacy=1");
  });

  test("Offres tab exposes the Découvrir and Importer catalog forms", async ({ page }) => {
    await page.getByRole("button", { name: "Offres", exact: true }).click();
    await expect(page.locator("#offers.panel.active")).toBeVisible();

    // Découvrir un catalogue fournisseur — built today.
    await expect(page.getByRole("heading", { name: "Découvrir un catalogue fournisseur" })).toBeVisible();
    await expect(page.locator("#discoverForm")).toBeVisible();
    await expect(page.locator("#discoverCompany")).toBeVisible();
    await expect(page.locator("#discoverShelf")).toBeVisible();
    await expect(page.getByRole("button", { name: "Découvrir et stager" })).toBeVisible();

    // Importer un catalogue déjà récolté — built today.
    await expect(page.getByRole("heading", { name: "Importer un catalogue déjà récolté" })).toBeVisible();
    await expect(page.locator("#harvestForm")).toBeVisible();
    await expect(page.locator("#company")).toBeVisible();
    await expect(page.locator("#shelf")).toBeVisible();
    await expect(page.getByRole("button", { name: "Stager le catalogue" })).toBeVisible();
  });

  test("submitting the Découvrir form stages a candidate offer", async ({ page }) => {
    await page.getByRole("button", { name: "Offres", exact: true }).click();
    // Shelves are loaded asynchronously after the shell becomes interactive.
    // Wait for a real choice so native form validation cannot race the request.
    await expect(page.locator("#discoverShelf option")).not.toHaveCount(0);
    await page.locator("#discoverCompany").fill("Acme Robotics");
    await page.getByRole("button", { name: "Découvrir et stager" }).click();
    // The staged/raw API result is dumped to a <pre>; the page does not
    // navigate anywhere else because there is nowhere else to go yet.
    await expect(page.locator("#discoverResult")).not.toHaveText("");
  });

  test("GAP: a staged catalog candidate can be reviewed and promoted to a canonical offer", async ({ page }) => {
    await page.getByRole("button", { name: "Offres", exact: true }).click();
    await expect(page.locator("#discoverShelf option")).not.toHaveCount(0);
    await page.locator("#discoverCompany").fill("Acme Robotics");
    await page.getByRole("button", { name: "Découvrir et stager" }).click();
    await expect(page.locator("#discoverResult")).not.toHaveText("");

    // GAP: no review/promotion screen exists today. Staging a candidate via
    // /api/catalog/discover or /api/catalog/harvest currently dead-ends at a
    // raw JSON <pre> dump — there is no UI path that turns a staged
    // candidate into a canonical product_catalog/*.yaml offer.
    await expect(page.getByRole("button", { name: /Promouvoir|Valider l.offre|Publier au catalogue/i })).toBeVisible();
  });

  test("GAP: a product_owner can open and edit their own offer sheet", async ({ page }) => {
    await page.getByRole("button", { name: "Offres", exact: true }).click();
    await expect(page.locator("#shelfGrid")).toBeVisible();

    // GAP: the shelf grid's per-offer actions today are "Auditer / MAJ"
    // (opens a generic skill-invoke drawer), "Opportunités" (client-side
    // filter) and "Parcours complet" (workflow drawer) — none of these is a
    // structured "my product" edit screen a product_owner can use to edit
    // their own canonical offer sheet directly.
    await expect(page.getByRole("button", { name: /Modifier ma fiche produit|Éditer l.offre/i }).first()).toBeVisible();
  });

  test("GAP: the Offres tab exposes a search CTA over /api/catalog/search", async ({ page }) => {
    await page.getByRole("button", { name: "Offres", exact: true }).click();

    // GAP: /api/catalog/search is built server-side but has no call-to-action
    // anywhere in the Offres panel — there is no search box/button wired to it.
    await expect(page.getByPlaceholder(/Rechercher (un|dans le) catalogue/i)).toBeVisible();
  });

  test("Opportunités button surfaces matching demand studies for an offer (client-side filter)", async ({ page }) => {
    await page.getByRole("button", { name: "Offres", exact: true }).click();
    const opportunitiesBtn = page.locator(".offerOppBtn").first();
    // This exists today, but only when at least one canonical offer is
    // present in the current workspace/runtime data.
    if (await opportunitiesBtn.count()) {
      await opportunitiesBtn.click();
      await expect(page.locator("#dataPanel")).not.toHaveClass(/hidden/);
      await expect(page.locator("#dataTitle")).toContainText("Opportunités");
    } else {
      test.skip(true, "No canonical offer present in this environment's shelf grid to click Opportunités on.");
    }
  });

  test("Qualification tab renders the demand-to-reach tunnel", async ({ page }) => {
    await page.getByRole("button", { name: "Qualification", exact: true }).click();
    await expect(page.locator("#qualification.panel.active")).toBeVisible();
    await expect(page.locator("#qualificationGrid")).toBeVisible();
  });

  test("GAP: intermediate pipeline evidence/synthesis artifacts can be rerun from the UI", async ({ page }) => {
    await page.getByRole("button", { name: "Qualification", exact: true }).click();
    const firstCard = page.locator(".qualification-card").first();
    if (await firstCard.count()) {
      await firstCard.locator(".qualFlowBtn").click();
      await expect(page.locator("#workflowPanel")).not.toHaveClass(/hidden/);
      // GAP: the workflow drawer only offers "Préparer" (initial generation
      // via skill-invoke) per un-started step, or a resolver CTA for a
      // blocker. There is no "rerun this step" / "regenerate evidence" /
      // "regenerate synthesis" action for a step that has already run once,
      // anywhere in the 9-step pipeline.
      await expect(page.getByRole("button", { name: /Rejouer|Régénérer|Rerun/i }).first()).toBeVisible();
    } else {
      test.skip(true, "No qualification study present in this environment to open a workflow for.");
    }
  });

  test("Suivi tab lists follow-up items as a flat list", async ({ page }) => {
    await page.getByRole("button", { name: "Suivi", exact: true }).click();
    await expect(page.locator("#backlog.panel.active")).toBeVisible();
    await expect(page.locator("#followUpGrid")).toBeVisible();
    await expect(page.locator(".table-title")).toHaveText("Backlog de gouvernance et de release");
  });

  test("Nudging tab generates cross-sell packages for a selected inventory", async ({ page }) => {
    await page.getByRole("button", { name: "Nudging", exact: true }).click();
    await expect(page.locator("#nudging.panel.active")).toBeVisible();
    const inventorySelect = page.locator("#nudgeInventory");
    const hasInventory = (await inventorySelect.locator("option").count()) > 0 &&
      (await inventorySelect.locator("option").first().getAttribute("value")) !== "";
    if (hasInventory) {
      await page.locator('.nudgeBtn[data-mode="cross_sell_package"]').click();
      await expect(page.locator("#nudgeResults")).not.toContainText("Calcul…", { timeout: 10_000 });
    } else {
      test.skip(true, "No nudge inventory present in this environment to generate cross-sell packages for.");
    }
  });

  test("GAP: Suivi and Nudging share a single pipeline/stage kanban board", async ({ page }) => {
    // GAP: today "Suivi" (#backlog, a flat follow-up list + governance table)
    // and "Nudging" (#nudging, per-mode generation buttons keyed to one
    // selected inventory) are two disconnected tabs. Neither renders a
    // kanban, and there is no shared pipeline/stage board linking a study's
    // qualification/reach stage to its nudging opportunities.
    await page.getByRole("button", { name: "Suivi", exact: true }).click();
    await expect(page.getByRole("region", { name: /Kanban|Pipeline/i })).toBeVisible();
  });
});
