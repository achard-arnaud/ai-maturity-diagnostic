# E2E functional spec (Playwright)

These specs are a **living functional spec**, not a bug report to silence.
They encode 3 full user journeys through the control-plane frontend
(`app/frontend/index.html` + `app.js`) end-to-end, as they should work once
upcoming frontend sprints land — not only as they work today.

Every assertion that documents a gap in the current UI is marked with a
comment directly above it: `// GAP: not implemented yet` (or a specific
variant explaining what's missing). **GAP-flagged assertions are expected to
FAIL today.** That is intentional TDD-for-UI: the failing assertion *is* the
target for the corresponding frontend sprint. Do not "fix" a GAP test by
deleting or skipping it — fix it by building the feature it describes, then
watch it turn green.

Assertions with no `GAP:` comment describe behavior that already exists and
should pass against a correctly running instance.

## Journeys covered

- `journey-a-product.spec.ts` — starting from adding a product/offer to the
  catalog, through matching, qualification, and nudging.
- `journey-b-contact.spec.ts` — starting from adding a contact, through
  discovery and reach.
- `journey-c-company.spec.ts` — starting from adding a company, through the
  existing ICB/sector-intelligence drill-down.

## Running the app under test

This is a Python/FastAPI backend (`app/server.py`) with a plain HTML/JS/CSS
frontend served by the same app — there is no separate frontend dev server.
Start it yourself before running the suite, e.g.:

```bash
# from the repo root, with the project's Python env set up per pyproject.toml
uvicorn app.server:APP --host 127.0.0.1 --port 8080
# or
python -m app.server
```

By default the suite targets `http://127.0.0.1:8080`. Override with:

```bash
export E2E_BASE_URL=http://127.0.0.1:8080
```

### Auth

The app requires an authenticated session (Google OAuth via `/auth/login`).
There is no test-only auth bypass in this codebase, so a headless Playwright
run cannot complete the real Google OAuth handshake. Each spec always
verifies the unauthenticated redirect-to-login behavior (this part is built
and should pass), then runs its "authenticated" journey steps under an
optional pre-authenticated Playwright `storageState`:

```bash
export E2E_STORAGE_STATE=/path/to/storage-state.json
```

If `E2E_STORAGE_STATE` is not set, the authenticated steps run without a
session and will fail at the first protected-page assertion — that failure
accurately reflects "you must supply a session to exercise this spec
end-to-end," it is not a bug in the tests.

## Running the suite

```bash
npm install
npx playwright test            # run everything (expect GAP failures)
npx playwright test --list     # enumerate tests without running them
npx playwright test journey-a-product.spec.ts
```

Playwright + Chromium are expected to be pre-installed in this environment
(`PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers`); `playwright.config.ts` points
`launchOptions.executablePath` at `/opt/pw-browsers/chromium` by default —
override with `PLAYWRIGHT_CHROMIUM_PATH` if needed. Do not run
`playwright install` in this environment.
