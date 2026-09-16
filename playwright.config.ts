import { defineConfig, devices } from "@playwright/test";

// These tests are a functional spec of 3 end-to-end journeys through the
// control-plane frontend (app/frontend/index.html + app.js), written against
// a running instance of the FastAPI app (app/server.py). See tests/e2e/README.md
// for how to start the app before running this suite.
//
// This config does NOT start the app itself (webServer is intentionally
// omitted) — auth/DB bootstrapping for app/server.py is out of scope here.

const baseURL = process.env.E2E_BASE_URL || "http://127.0.0.1:8080";

// Playwright + Chromium are pre-installed in this environment at a fixed
// path rather than the default cache location, so we point executablePath
// there explicitly instead of relying on `playwright install`.
const chromiumExecutablePath = process.env.PLAYWRIGHT_CHROMIUM_PATH || "/opt/pw-browsers/chromium";

export default defineConfig({
  testDir: "./tests/e2e",
  timeout: 30_000,
  expect: { timeout: 5_000 },
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: 0,
  reporter: [["list"]],
  use: {
    baseURL,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: {
        ...devices["Desktop Chrome"],
        launchOptions: {
          executablePath: chromiumExecutablePath,
        },
      },
    },
  ],
});
