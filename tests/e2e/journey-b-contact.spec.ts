import { test, expect } from "@playwright/test";
import { assertLoginRedirectWorks, STORAGE_STATE } from "./helpers";

/**
 * Journey B — starting from adding a contact.
 *
 * "Ajouter un contact" (built) -> generic skill-invoke drawer for
 * network-contact-intake -> [GAP] structured name/email/company form ->
 * [GAP] post-invoke confirmation/feedback + no-op-until-executor-configured
 * banner (ADR-004) -> [GAP] /api/network/people search CTA -> [GAP] person
 * detail/profile page -> Reach flow (exists, operates on aggregate
 * stakeholder lanes, not a single contact) -> shared kanban (built after
 * this spec was written -- see the kanban test below, no longer GAP-flagged).
 */

test.describe("Journey B - contact (login)", () => {
  test("unauthenticated access redirects to the login page", async ({ page }) => {
    await assertLoginRedirectWorks(page);
  });
});

test.describe("Journey B - contact (authenticated)", () => {
  test.use({ storageState: STORAGE_STATE });

  test.beforeEach(async ({ page }) => {
    await page.goto("/");
  });

  test("Ajouter un contact opens the generic skill-invoke drawer for network-contact-intake", async ({ page }) => {
    await page.getByRole("button", { name: "Ajouter un contact" }).click();
    await expect(page.locator("#invokePanel")).not.toHaveClass(/hidden/);
    await expect(page.locator("#invokeTitle")).toHaveText("network-contact-intake");
    // Today this is a raw LLM-prompt textarea, not a structured form.
    await expect(page.locator("#invokeInput")).toBeVisible();
    await expect(page.locator("#contextPaths")).toBeVisible();
    await expect(page.getByRole("button", { name: "Préparer / exécuter cette skill" })).toBeVisible();
  });

  test("GAP: contact intake is a structured name/email/company form, not a raw prompt textarea", async ({ page }) => {
    await page.getByRole("button", { name: "Ajouter un contact" }).click();
    await expect(page.locator("#invokePanel")).not.toHaveClass(/hidden/);

    // GAP: #invokeInput is a single freeform textarea today. There is no
    // structured field for name, email or company anywhere in the drawer.
    await expect(page.getByLabel(/^Nom$/i)).toBeVisible();
    await expect(page.getByLabel(/^Email$/i)).toBeVisible();
    await expect(page.getByLabel(/^Entreprise$/i)).toBeVisible();
  });

  test("GAP: invoking the skill shows confirmation the contact was actually created", async ({ page }) => {
    await page.getByRole("button", { name: "Ajouter un contact" }).click();
    await page.locator("#invokeInput").fill("Nouveau contact: Jane Doe, jane.doe@example.com, Acme Robotics.");
    await page.getByRole("button", { name: "Préparer / exécuter cette skill" }).click();
    // Today this only dumps the raw invoke response JSON into a <pre>; there
    // is no follow-up confirmation UI (e.g. a link to the new contact, or a
    // "Contact créé" toast/banner) once the call returns.
    await expect(page.locator("#invokeResult")).not.toHaveText("");

    // GAP: no confirmation banner distinguishing an actual creation from a
    // no-op response.
    await expect(page.getByText(/Contact créé/i)).toBeVisible();
  });

  test("GAP: a banner distinguishes a real creation from an executor-not-configured no-op (ADR-004)", async ({ page }) => {
    await page.getByRole("button", { name: "Ajouter un contact" }).click();
    await page.locator("#invokeInput").fill("Nouveau contact: Jane Doe, jane.doe@example.com, Acme Robotics.");
    await page.getByRole("button", { name: "Préparer / exécuter cette skill" }).click();
    await expect(page.locator("#invokeResult")).not.toHaveText("");

    // GAP: per ADR-004, nothing is actually persisted unless
    // AI_DIAGNOSTIC_SKILL_EXECUTOR is configured, but the UI never
    // surfaces this distinction — the health bar's "Executor à configurer"
    // notice is global and not repeated as a contextual warning right where
    // the user just triggered a would-be write.
    await expect(page.getByText(/exécuteur non configuré|no-op tant que|aucun exécuteur/i)).toBeVisible();
  });

  test("GAP: /api/network/people is searchable from the UI to find a created contact", async ({ page }) => {
    // GAP: /api/network/people is built server-side but there is no
    // call-to-action anywhere in the frontend (no nav entry, no search box,
    // no results list) that lets a user browse or search created people.
    await expect(page.getByRole("button", { name: /Personnes|Contacts|Réseau/i })).toBeVisible();
  });

  test("GAP: a person has a dedicated detail/profile page", async ({ page }) => {
    // GAP: there is no person detail/profile route or panel anywhere in the
    // SPA. The closest concept, the Demande tab's company drill-down, is
    // organized around companies/ICB, never around an individual contact.
    await page.goto("/#/people/jane-doe");
    await expect(page.getByRole("heading", { name: /Jane Doe/i })).toBeVisible();
  });

  test("Reach flow operates on aggregate stakeholder lanes for a study, not a single contact", async ({ page }) => {
    await page.getByRole("button", { name: "Qualification", exact: true }).click();
    const reachBtn = page.locator(".reachBtn").first();
    if (await reachBtn.count()) {
      await reachBtn.click();
      await expect(page.locator("#dataPanel")).not.toHaveClass(/hidden/);
      // Built today: first/second wave + validation-only lanes, all keyed
      // by study, not by an individually addressable contact record.
      await expect(page.getByText("First wave")).toBeVisible();
      await expect(page.getByText("Second wave")).toBeVisible();
      await expect(page.getByText("Validation only")).toBeVisible();
    } else {
      test.skip(true, "No study with decision pursue/validate present in this environment to open Reach for.");
    }
  });

  test("contacts and reach are organized on a shared kanban board", async ({ page }) => {
    // No longer GAP: app/kanban.py's build_board() now exists and
    // app/frontend/index.html's #qualification panel renders it via
    // #kanbanQualification (app.js's loadKanban()). This assertion used to
    // be GAP-flagged before that build landed; it now genuinely passes.
    // (Per-contact drag/drop staging still does not exist -- the board is
    // per-study/per-company, not per-contact -- but the region itself is real.)
    await page.getByRole("button", { name: "Qualification", exact: true }).click();
    await expect(page.getByRole("region", { name: /Kanban/i })).toBeVisible();
  });
});
