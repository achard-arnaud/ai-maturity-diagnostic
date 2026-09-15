import { Page, expect } from "@playwright/test";

/**
 * Shared helpers for the 3 journey specs.
 *
 * Auth reality check (S8b, already built): the control plane is protected by
 * Google OAuth (`/auth/login` -> Google -> `/auth/callback` presumably ->
 * session cookie). Unauthenticated access to "/" redirects client-side to
 * "/login.html" once app.js's checkAuth() sees a 401 from `/api/auth/me`.
 *
 * There is no test-only auth bypass in this codebase, so a real Playwright
 * run cannot complete the Google OAuth handshake headlessly. To keep the
 * "walk the journey while authenticated" steps meaningful (rather than every
 * single one being a trivial redirect-to-login failure), each spec accepts
 * an optional pre-authenticated storage state via the E2E_STORAGE_STATE env
 * var (a Playwright storageState JSON path containing a valid session
 * cookie for the target instance). When it is not set, the "authenticated"
 * describe blocks run without a session and will fail at the first
 * protected-page assertion — that failure is itself an accurate reflection
 * of "you must supply a session to exercise this spec end-to-end", not a
 * bug in the test.
 */
export const STORAGE_STATE = process.env.E2E_STORAGE_STATE || undefined;

/** Assert the built, working part of the auth flow: unauthenticated access
 * to "/" redirects to the login page, which offers the Google login CTA. */
export async function assertLoginRedirectWorks(page: Page) {
  await page.goto("/");
  await page.waitForURL(/\/login\.html$/);
  await expect(page.getByRole("heading", { name: "Connexion requise" })).toBeVisible();
  const googleLogin = page.getByRole("link", { name: /Se connecter avec Google/i });
  await expect(googleLogin).toBeVisible();
  await expect(googleLogin).toHaveAttribute("href", "/auth/login");
}

/** Navigate to the control plane and switch to the given top-level nav tab. */
export async function openTab(page: Page, tabName: string) {
  await page.goto("/");
  await page.getByRole("button", { name: tabName, exact: true }).click();
}
