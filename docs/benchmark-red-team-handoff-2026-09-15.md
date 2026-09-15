# AI Maturity Diagnostic — benchmark red-team handoff for Claude

Date: 2026-09-15
Status: sprint-prep / architecture decision handoff

## Executive decision

The prior benchmark and Claude's counter-analysis are **aligned on the problem and constraints but diverged on the solution**.

After a deeper pass on `main`, the updated recommendation is:

> **PIVOT NATIVE, with a targeted reopen gate.**

Do **not** integrate Baserow now. Strengthen the native Python control plane and admin surfaces first. Reopen Baserow/Directus only if a concrete unmet need appears around bulk tabular editing, cross-object administration, or materially richer multi-role permissions.

This replaces the earlier `COEXIST / PARTNER` recommendation for Baserow as the default next step.

## Why the decision changed

The earlier benchmark correctly identified the underlying need: lightweight human administration for a small, vibe-coded system without creating a data-platform project. The mistake was to overestimate the absence of a native admin/control surface.

`main` already contains:

- a Python control plane (`app/server.py`, `app/core.py`);
- a static admin frontend (`app/frontend/`);
- demand, qualification, nudging, reach, value-chain and follow-up views;
- explicit blocker/resolver contracts (`app/blockers.py`);
- catalog staging with `automatic_promotion_to_product_catalog: false` and `required_human_review: true` (`app/catalog.py`);
- a workflow that treats artifacts as handoffs and preserves domain separation.

That materially changes the build-vs-integrate equation. A third-party admin layer would now duplicate an existing direction rather than fill a blank capability.

## Reconciliation with Claude's C1–C8

### C1 — existing admin/control plane
**Confirmed in substance.**

`main` exposes native UI and APIs for demand, offers, qualification, nudging, follow-up, skills and workflow planning. The current public `main` does **not** contain the exact `app/authruntime/` paths cited in Claude's response, so those claims appear to refer to a newer/local branch or another unmerged state. The architectural conclusion still holds: there is already a native control plane substantial enough to make Baserow non-default.

### C2 — best pilot object
**Agree with the principle, not yet with the exact file-level claim.**

The right next sprint should identify one native workflow where human review is currently awkward and improve that workflow in place. If Claude's newer branch contains an `overrides` approval queue, reconcile that branch into this repo and evaluate it first. On `main`, blockers, qualification gates, catalog staging and follow-up are the closest equivalent control points.

### C3/C4 — canonical boundary and merge gate
**Confirmed.**

The repo already encodes governance in domain/runtime code instead of delegating it to a data UI. `CatalogHarvester.stage()` explicitly prevents automatic product-catalog promotion and requires both a skill and human review. `blockers.py` also models owner skill/human action, required state and postcondition.

Therefore an external admin tool would have to mirror or bypass existing governance. That is a negative unless a concrete UX need justifies it.

### C5 — lock-in
**Agree.**

A Baserow layer would add another runtime, schema, identity/permissions surface and operational habit. The most important lock-in risk is not PostgreSQL itself; it is moving workflow semantics and human operating habits into the external UI.

### C6 — operating cost
**Agree.**

For the current scale and single-maintainer/vibe-coded operating model, another service should clear a high value threshold before adoption.

### C7 — native alternative
**Now the preferred path.**

The repo has already proven a native admin/control-plane pattern. The next sprint should extend this pattern rather than introduce a second administration substrate.

### C8 — license
**No longer decision-relevant for the immediate sprint.**

Keep license/sovereignty as a reopen criterion only if a third-party admin layer is reconsidered.

## What is confirmed on current `main`

### Existing control-plane assets

- `app/server.py` — HTTP control plane and API routing.
- `app/frontend/index.html`, `app/frontend/app.js`, `app/frontend/styles.css` — native frontend.
- `app/core.py` — repo control plane, skill invocation envelope and safe context boundaries.
- `app/dashboard.py` — follow-up dashboard and use-case heritage views.
- `app/blockers.py` — explicit resolver contract and human-review blocker.
- `app/catalog.py` — staged catalog harvesting with promotion guardrails.
- `app/qualification.py`, `app/nudging.py`, `app/reach.py`, `app/value_chain.py`, `app/uc_graph.py`, `app/workflows.py` — domain-specific control paths.

### Existing governance signals

The repo already encodes several properties the Baserow integration note wanted to create:

1. artifacts as handoffs;
2. explicit ownership of blockers and postconditions;
3. no automatic promotion of external/catalog evidence into canonical truth;
4. domain-specific views instead of a generic CRUD-first design;
5. external integrations treated as optional rather than canonical.

## Gaps Claude should harvest next

The next sprint should **not** start by coding a generic admin framework. It should perform a focused harvest of native-control gaps and then close the highest-value ones.

### Harvest zone 1 — reconciliation of Claude's newer runtime

Claude cited paths that are absent from current `main`:

- `app/authruntime/app.py`;
- `ControlStore.list_overrides` / `db.py`;
- `app/catalog_promotion.py`;
- admin routes for workspaces/users/memberships/audit/overrides.

Action:

1. identify the branch/commit/session containing these changes;
2. compare against current `main`;
3. decide whether they are pending implementation, stale local work or an alternate architecture;
4. do **not** build duplicate equivalents until this is resolved.

### Harvest zone 2 — native approval/inbox workflow

Find every place where a human must approve, resolve or promote something:

- catalog candidates;
- blockers / manual validation;
- qualification gates;
- reach readiness;
- any overrides if present in newer work.

Goal: determine whether these should converge into a small reusable native approval queue rather than separate one-off UI patterns.

### Harvest zone 3 — catalog staging → promotion

`CatalogHarvester` stages candidates and explicitly blocks auto-promotion, but the UX/service handoff from staged candidate to reviewed canonical product profile should be mapped end-to-end.

Questions:

- Where is the review action surfaced?
- What exact object is promoted?
- Which evidence/epistemic fields survive promotion?
- Is there a reversible rejection/defer state?
- Is the action idempotent and auditable?

### Harvest zone 4 — generic admin need versus domain UI

Audit whether users actually need:

- bulk editing;
- arbitrary sorting/filtering across object families;
- spreadsheet-like multi-row editing;
- ad hoc joins/cross-object views;
- non-technical schema editing.

If these do **not** appear in actual usage, stay domain-native. If they do, reopen a targeted admin-tool benchmark.

### Harvest zone 5 — persistence truth

Document the actual persistence model by domain:

- YAML/filesystem canonical artifacts;
- any SQLite/control DB if present outside current `main`;
- private data paths;
- generated/derived indexes;
- ephemeral frontend state.

Do not introduce another store until this map is explicit.

### Harvest zone 6 — authorization boundary

Current `main` exposes a local HTTP control plane. Determine what the near-term user model actually is:

- single maintainer/local;
- small trusted team;
- multiple roles with different write rights;
- external/customer access.

Do not import a heavy permission model before a real role boundary appears.

### Harvest zone 7 — audit trail

The repo has strong evidence/provenance contracts, but admin mutations should be checked for an explicit audit trail:

- actor;
- timestamp;
- before/after;
- reason;
- source object / claim IDs;
- reversible status where appropriate.

If Claude's newer `audit` routes already implement this, harvest and consolidate rather than rebuild.

### Harvest zone 8 — native UX debt

Review `app/frontend/` for the smallest high-impact improvements:

- filtering/search consistency;
- pending/approved/rejected status visibility;
- resolver CTAs;
- inline edit only where safe;
- bulk actions only where a real workflow needs them;
- clear canonical vs staged/proposed state.

## Sprint recommendation

### Sprint objective

> **Prove that the native control plane can cover the next operational needs without introducing a second administration platform.**

### Suggested work packages

#### WP1 — Reconcile runtime branches
- locate Claude's `authruntime` / overrides / catalog-promotion implementation;
- compare to `main`;
- merge/harvest only non-duplicative capabilities.

#### WP2 — Approval workflow map
- inventory all human-review points;
- model one reusable approval state machine only if repetition is demonstrated;
- preserve domain-specific hard gates.

#### WP3 — Close one real admin gap
Preferred candidates:
1. staged catalog candidate → reviewed promotion;
2. blocker/manual-validation queue;
3. overrides queue if Claude's newer code is recovered.

#### WP4 — Auditability and tests
For the selected mutation flow, add tests for:
- cannot promote `unknown`/unsupported claim to canonical fact;
- explicit actor/reason where applicable;
- idempotence or duplicate prevention;
- failure/rollback path;
- permissions boundary appropriate to current user model.

#### WP5 — Reassess need for external admin
At sprint end, explicitly answer:

`NATIVE_SUFFICIENT | REOPEN_TARGETED_ADMIN_TOOL`

No broad benchmark unless a named gap survives the native sprint.

## Reopen criteria for Baserow / Directus

Reopen only if at least one of these becomes concrete and recurring:

1. non-developers need high-volume spreadsheet-like bulk editing across many objects;
2. cross-object exploratory filtering/joining becomes operationally important;
3. multiple roles require materially finer-grained data permissions than the native control plane can justify implementing;
4. native admin maintenance demonstrably consumes more effort than an external surface would save;
5. the required generic admin UX is clearly outside the product's differentiating domain logic.

If reopened, compare the external tool against the **actual native baseline**, not against a blank-slate architecture.

## Counter-perspective against PIVOT NATIVE

The native choice should also be red-teamed. It fails if:

- native UI becomes a growing bespoke CRUD framework with duplicated table/filter/form logic;
- admin needs spread faster than domain value;
- role/permission complexity materially increases;
- non-developers cannot operate the system without developer intervention;
- the team spends repeated sprints rebuilding generic admin primitives.

If two or more of these appear with evidence, use `REOPEN_TARGETED` and benchmark only the missing admin capability.

## Final instruction to Claude

Do not treat `PIVOT NATIVE` as permission to build a generic internal admin platform.

The required posture is:

1. reconcile the code states first;
2. reuse the native control plane and existing governance contracts;
3. close one concrete admin workflow gap;
4. add only the minimum reusable primitive demonstrated by repetition;
5. preserve canonical artifact/evidence boundaries;
6. stop when the workflow is operational;
7. reopen Baserow/Directus only against a named, evidenced failure of the native path.

### Expected sprint-end verdict

- `NATIVE_SUFFICIENT` — continue native incrementally; or
- `REOPEN_TARGETED_ADMIN_TOOL` — state the exact unmet capability and compare only tools that solve it.

The objective is not to defend native code ideologically. It is to minimize irreversible architecture and operational burden while preserving a credible exit path.