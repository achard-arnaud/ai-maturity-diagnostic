# Test and CI Baseline — verified 2026-09-17

## `scripts/check_release.py` — what it actually checks (read in full, 156 lines)

Runs 10 checks in sequence, collecting all failures before reporting (not
fail-fast):

1. **`ruff lint`** — `ruff check .` over the whole repo.
2. **`package validator`** — `scripts/validate_package.py` (302 lines):
   validates the `qualification-tunnel-router` skill family (10 named
   skills), contracts, catalog and templates/evals structure. This is the
   check that rejects `feat/prospection-principes-todo`
   (`SKILL.md` >500 lines / missing `agents/openai.yaml` / unsupported
   `status` frontmatter key).
3. **`LinkedIn deferred-design validator`** —
   `scripts/validate_linkedin_design.py` (146 lines): enforces that the
   LinkedIn connector stays documented-only/deferred and isn't silently
   activated in the runtime.
4. **`unit and integration tests with app coverage`** —
   `coverage run --branch --source=app -m unittest discover -s tests`.
5. **`app line coverage >=80%`** — `coverage report --fail-under=80` (branch
   coverage is collected but the gate itself checks line coverage only).
6. **`parse_structured_files`** — every `.yaml`/`.yml`/`.json` file in the
   repo must parse, and any file declaring
   `$schema: https://json-schema.org/draft/2020-12/schema` must pass
   `Draft202012Validator.check_schema`.
7. **`markdown_links`** — every local (non-`http(s)`/`mailto`/anchor-only)
   Markdown link must resolve to a file that exists inside the repo root
   (no link may escape the repo).
8. **`privacy_and_portability`** — scans every text file for PEM private-key
   headers and for a specific non-portable home-directory path (the scanner's
   own source names it; not repeated here verbatim so this audit file itself
   doesn't trip the same check).
9. **DOCX example configuration + generation** — runs
   `skills/tech-leadership-org-intelligence/scripts/build_org_tech_note.py`
   in `--validate-only` mode and then for real, against the shipped example
   config, into a temp file.
10. **Private network validator** (conditional) — `scripts/validate_network.py`
    (366 lines) only runs if `data/private/network/people.jsonl` exists in
    the clone; otherwise explicitly `SKIP`s (private data is never present
    in a fresh clone, so this always skips in CI and in this session).

Exit code is `1` if any check produced an error message, `0` otherwise.
`EXCLUDED_PARTS` kept out of every file-scan: `.git`, `.venv`, `__pycache__`,
`.pytest_cache`, `data/private`, `node_modules`, `.claude`,
`playwright-report`, `test-results`.

## `scripts/run_e2e_gate.py` — what it actually checks (read in full, 160 lines)

Not a simple "run Playwright" wrapper — it implements a specific gating
policy documented in its own docstring and in `tests/e2e/README.md`:

1. Waits up to 20s for `GET /api/health` to return 200 on the app it starts
   itself (`uvicorn app.server:APP` on `127.0.0.1:8080`).
2. Mints a real authenticated session via `scripts/dev_login.py
   e2e-gate@example.com` (the same session mechanism the app itself uses,
   not a mock) and writes it as a Playwright `storageState` cookie
   (`aimd_session`), so the authenticated halves of each journey run for
   real instead of redirecting at the first protected page.
3. Runs `npx playwright test --reporter=json` against the 3 journeys under
   `tests/e2e/` (`journey-a-product`, `journey-b-contact`,
   `journey-c-company` — confirmed present).
4. **Gates on regressions only, by test title convention**: any test whose
   title is prefixed `GAP:` is a documented, intentional current gap in the
   UI (living functional spec / TDD-for-UI, per `tests/e2e/README.md`) and
   is **expected to fail today** — a GAP failure does not fail the gate. Any
   **non-GAP** test that fails is a real regression and fails the gate
   (exit 1). A GAP test that newly *passes* is printed as a NOTICE (progress
   to retire in a future frontend sprint), not an error.
5. Exit 0 only if there are zero non-GAP failures.

This means "the E2E gate is green" is a materially weaker/different claim
than "all 3 Playwright journeys fully pass" — some assertions inside those
journeys are allowed, by design, to still be red. Read `tests/e2e/README.md`
in full before treating a green `e2e-gate` as "the UI has no known gaps."

## Coverage — actually run in this session, not taken on faith

`python -m unittest discover -s tests -v`: **1149 tests, all passed, 1
skipped**, in ~10.4s.

`coverage report` (branch coverage on, `--source=app`): **TOTAL 91%** line
coverage (6720 statements, 450 missed; 1886 branches, 306 partial) — well
above the 80% gate `check_release.py` enforces. Every `app/*.py` module
individually clears 80%+ except none fell below the reported per-file
minimums in this run (spot-checked `app/workflows.py` at 82%,
`app/workspace_migrator.py` at 82%, `app/workspace_paths.py` at 100%).

## Could these actually be run locally? Yes, with caveats

- **`check_release.py`: run successfully in this worktree this session**,
  full result `RESULT: 0 release error(s)` (all 10 checks passed, the
  conditional private-network check correctly skipped). The repo's system
  Python had a broken `cryptography` package (`Cannot uninstall
  cryptography 41.0.7, RECORD file not found` — a Debian-packaged install
  conflicting with pip) that blocked `pip install -e '.[docs,dev]'`
  in-place; this was worked around by creating a throwaway venv
  (`python3 -m venv /tmp/aimd_venv && /tmp/aimd_venv/bin/pip install -e
  '.[docs,dev]'`), which installed cleanly (fastapi 0.141.1, starlette
  1.6.0, jsonschema 4.26.0, coverage 7.16.1, ruff 0.16.8, Authlib 1.8.0,
  itsdangerous 2.2.0, uvicorn 0.53.0, PyYAML already present system-wide).
- **`run_e2e_gate.py`: not run locally in this session.** Node/npm/npx are
  present (`/opt/node22/bin/{node,npm,npx}`), so it is plausibly runnable,
  but it additionally requires `npx playwright install --with-deps
  chromium` (a real browser download) and starting the FastAPI app as a
  background process — judged out of scope for this Phase-1 task given the
  GitHub Actions `e2e-gate` job for the exact same commit
  (`7a8a618`) was independently confirmed **green** via the GitHub API
  (see `IMPLEMENTATION_BASELINE.md`; job id `105126762904`, conclusion
  `success`). If a future task needs the E2E gate reproduced byte-for-byte
  locally rather than trusted from CI, that install step is the next thing
  to do.

## GitLab mirror (`.gitlab-ci.yml`)

Structurally mirrors the GitHub jobs (`release-check` in a
`python:3.11-slim` image, `e2e-gate` in `mcr.microsoft.com/playwright:v1.56.1-jammy`),
and its own comment says GitHub Actions is the enforced source of truth.
No GitLab runner is reachable from this environment; every Epic acceptance
record consistently says the same thing ("GitLab `e2e-gate` mirror
unverified against a live runner") going back to E00 — this is a
long-standing, consistently-documented, non-blocking limitation, not new
drift.
