# CRUD, search and artifact-retrieval gap analysis (CLAUDE_01 Workstream D)

Status: **research only, PROPOSE_ONLY**. This document is an input to the
human/architecture-owner's next-wave Epic decision (candidate E15
"Universal CRUD, Retrieval & Artifact Library" in particular), not
authorization to build anything. No runtime code was modified to produce
it.

Author context: prepared for francois.arnaud.rjc@gmail.com's review.
Repo: `achard-arnaud/ai-maturity-diagnostic`, HEAD at the PR #67 merge
commit (`16cd776`) on `main`, 2026-09-17. Companion document:
`USE_CASE_PLATFORM_GAP_MATRIX.md` (Workstream A) — read that first for the
per-space overview; this document goes deeper on the ten canonical
objects the brief named, plus the retrieval question.

Method: every "does X exist over HTTP" claim was verified by reading the
actual `app/*_routes.py` file (`grep -n "@router\."` plus a full read),
not by trusting an acceptance doc's wording alone — the acceptance docs
were used as **primary evidence to cross-check**, per the task brief, and
every one of them was confirmed against the route file itself. No
discrepancy was found between what an `EPIC_0X_ACCEPTANCE.md` "Known
limitations" section says and what the route file actually contains.

---

## 1. Per-object CRUD, concurrency and audit table

"HTTP" below means an actual `@router.get/post/patch/delete` in an
`app/*_routes.py` file wired into `app/server.py`, not a Python function
that could theoretically be called from one.

| Object | Create (HTTP) | Read (HTTP) | Update (HTTP) | Archive/Delete/Restore (HTTP) | Optimistic concurrency | Audit/history | Evidence |
|---|---|---|---|---|---|---|---|
| **Company / Person** | Yes — but on the **legacy** surface only: `POST /api/network/people`, `POST /api/network/companies` (`app/server.py:624,638`, calling `app/network_writer.py`'s `create_person`/`create_company`), not the `/api/v1/...` router | Yes — `app/network_v1_routes.py`: `GET /people`, `GET /people/{id}`, `GET /companies`, `GET /companies/{id}`, `GET /relationships`, `GET /relationships/{id}`, `GET /people/{id}/360` | **No** — no PATCH anywhere for a person/company record on either the legacy or v1 surface | **No** — no delete/archive/restore; `POST /admin/network/companies/{id}/reassign` (`app/server.py:421`) is a company-merge/reassignment action, not a lifecycle delete | None — `app/network_v1_store.py`'s `put_entity` is a plain upsert, no version field | None beyond the generic `ControlStore.record_audit()` on the `/admin/network/*` actions specifically (not on ordinary person/company creation) | `app/network_v1_routes.py`, `app/network_v1_store.py`, `app/server.py:624-649`, `app/network_writer.py` |
| **Signal** | **No** — signals are produced by `app/signal_ingestion.py`/`app/signal_screening.py` only, no `POST /signals` route exists | Yes — `app/signal_routes.py:22,36` `GET /signals`, `GET /signals/{id}` | **No** — no PATCH | **No**; the only write route is `POST /signals/{id}/queue-research` (`app/signal_routes.py:47`), a one-way state transition (handoff to Research), not a general update/archive | None — `app/signal_store.py`'s `put_signal` is a plain upsert | Handoff itself is journaled (`app/signal_handoff.py` writes to `EventJournal`), but there is no per-field edit history for a signal | `app/signal_routes.py`, `app/signal_store.py`, `app/signal_handoff.py` |
| **ResearchCase / Claim** | **No** — a case is created by `app/research_orchestration.py`/`app/research_review.py` Python calls only; same for claims via `app/claim_store.py`'s `put_claim` (no route calls it) | Yes, ResearchCase only — `app/research_routes.py:33,47` `GET /research-cases`, `GET /research-cases/{id}`, plus `GET /companies/{id}/360`. **Claim has no HTTP read route at all** — `app/claim_store.py`'s `list_claims`/`get_claim` are never imported by any `*_routes.py` file | **No** — no PATCH for case status or for a claim | **No** | None on either object | `app/research_review.accept_case` writes to `EventJournal`, but that is a Python-only code path with no HTTP trigger, so no audit trail is produced by anything a user can actually click today | `app/research_routes.py`, `app/research_case_store.py`, `app/claim_store.py` (confirmed no importer via `grep -rl "claim_store" app/*routes.py` → no match) |
| **Demand** | **Yes** — `POST /demands` (`app/demand_routes.py:61`), refuses duplicate `demand_id` with 409 | Yes — `GET /demands`, `GET /demands/{id}`, `GET /demands/{id}/resolver` | **Yes** — `PATCH /demands/{id}` (`:73`), requires `expected_version` in the body | **No** — no archive/delete/restore | **Yes** — `app/demand_store.py`'s `_version` field, `expected_version` required on PATCH, `DemandConflict` → HTTP 409 on stale write, `DemandNotFound` → 404 | No per-field audit trail beyond the version counter itself (no who/when/what-changed log distinct from the record's own current state) | `app/demand_routes.py`, `app/demand_store.py` (full read above) |
| **Product / ProductSnapshot** | **No** — `app/product_routes.py` is 100% read routes; publishing a version is Python-only via `app/product_workflow.py`. EPIC_06's own acceptance record says this explicitly ("no HTTP publish endpoint exists yet") | Yes — `GET /products`, `GET /products/{id}`, `GET /products/{id}/snapshots/{id}`, `GET /products/{id}/diff` | **No** | **No** — `ProductSnapshot` is immutable by design (stated in the route file's own docstring), so "no update" here is intentional, not a gap; `Product` (the mutable parent) still has no write route at all | None (nothing to version — no write route) | None | `app/product_routes.py` |
| **FitAssessment** | **Yes** — `POST /fit-assessments` (`app/fit_routes.py:75`), 409 on duplicate | Yes — `GET /fit-assessments`, `GET .../compare`, `GET .../{id}` | **Yes** — `PATCH /fit-assessments/{id}` (`:87`), requires `expected_version` | **No** | **Yes** — identical shape to Demand: `_version` in `app/fit_store.py`, `FitConflict` → 409, `FitNotFound` → 404 | Same as Demand: version counter only, no separate audit log | `app/fit_routes.py`, `app/fit_store.py` |
| **TargetPlan / Sequence-adjacent stakeholder** | **No** — EPIC_08's acceptance record: "`app.target_plan_store`/`app.target_plan_routes` do not yet expose a write path... Writing plans and assigning stakeholders is currently Python-API-only" — confirmed: `app/target_plan_routes.py` has 4 `@router.get`, 0 `post`/`patch` | Yes — `GET /target-plans`, `GET /target-plans/{id}`, `GET .../stakeholders`, `GET .../committee-graph` | **No** | **No** | None | None | `app/target_plan_routes.py`, EPIC_08_ACCEPTANCE.md |
| **Sequence / Touchpoint** | **No** — EPIC_09's acceptance record: same pattern, confirmed by `app/reach_routes.py` having 5 `@router.get`, 0 write verbs | Yes — sequences, steps, tasks, touchpoints, all list/get | **No** | **No** | None | None | `app/reach_routes.py`, EPIC_09_ACCEPTANCE.md |
| **EngagementEvent / Conversation** | **No** — EPIC_10's acceptance record: same pattern, confirmed by `app/engagement_routes.py` having 4 `@router.get`, 0 write verbs. Ingestion happens via `app/engagement_ingestion.py` Python calls only | Yes — conversations, events, objections, all list/get | **No** | **No** | None | None | `app/engagement_routes.py`, EPIC_10_ACCEPTANCE.md |
| **Opportunity / Deal** | **No** — EPIC_11's acceptance record: same pattern, confirmed by `app/opportunity_routes.py` having 3 `@router.get`, 0 write verbs | Yes — `GET /opportunities`, `GET .../pipeline-board`, `GET .../{id}` | **No** | **No** | None | None | `app/opportunity_routes.py`, EPIC_11_ACCEPTANCE.md; see also §2's note on `opportunity_notes.py` |

**Cross-cutting finding**: of the ten canonical objects named in the
brief, exactly **two** (Demand, Fit) have a full HTTP create+update path,
and both of those two are also the only two with optimistic concurrency.
The other eight are either HTTP-read-only-with-Python-only-writes
(ResearchCase/Claim, TargetPlan, Sequence, EngagementEvent/Conversation,
Opportunity) or have a create route on the legacy surface only with no
update at all (Company/Person), or have neither create nor update over
HTTP by design (Signal, ProductSnapshot).

**No object anywhere in this codebase has an HTTP delete, archive, or
restore route.** This was verified with `grep -rn "@router\.\|@app\." app/*.py | grep -iE "delete"`,
which returns zero matches, and a full read of the route files above
confirms no `archive`/`restore` verb either. The only "archived" concept
in the codebase is `app/product_policy.py`'s `"archived"` lifecycle
**status value** (a field a `Product`/`ProductVersion` could in principle
be set to), which is not reachable from any route since Product has no
write route at all (see table above).

**No object anywhere has a distinct audit/history log of field-level
changes.** The two mechanisms that come closest are:
- `app/event_journal.py`'s append-only, hash-chained `EventJournal` — but
  it is wired into only seven modules (`fit_lifecycle`, `insights_routes`,
  `learning_proposals`, `product_workflow`, `research_review`,
  `run_manager`, `signal_handoff`), all Python-side lifecycle transitions,
  **not** the HTTP PATCH paths for Demand/Fit — a `PATCH /demands/{id}`
  or `PATCH /fit-assessments/{id}` call does not write an EventJournal
  entry; it only bumps `_version` and overwrites the record in place, so
  the *previous* field values are gone once a PATCH succeeds (`_write_all`
  replaces the whole JSONL file with only the new records).
- `app/authruntime/db.py`'s `ControlStore.record_audit()` — a genuine
  actor/action/target/reason audit table, but scoped to control-plane
  actions only (login, workspace creation, membership changes), not
  business objects.

This is worth naming explicitly: **updating a Demand or a Fit today loses
the prior version's field values**, keeping only the new record plus an
incrementing integer. If "what did this Fit look like before the last
edit, and who made the edit" ever becomes a real requirement (it plausibly
will, given Fit is an "explainable decision" object per its own job
description), that is a distinct, narrower gap from full CRUD and from
the artifact-library question below — worth calling out separately to the
architecture owner rather than folding into "add write routes."

## 2. One more loose end found while verifying: `opportunity_notes.py`

`app/opportunity_notes.py` (Epic 11 S03) defines `create_discovery_note`
and `record_commercial_decision` as pure functions with real validation
(role checks, length limits, mandatory evidence refs) and its own test
file (`tests/test_opportunity_notes.py`). Neither function is ever called
with a store — `grep -rn "create_discovery_note\|record_commercial_decision"
app/*.py` outside the file itself returns nothing. A "discovery note" or
"commercial decision" constructed today via these functions is returned
to whatever Python caller invoked them and then discarded; there is no
`opportunity_notes_store.py` and no route. This is smaller and more
surgical than the Pipeline write-route gap in the matrix (§1's
Opportunity row) — it looks like an Epic 11 loose end (function built,
tested in isolation, never wired to persistence) rather than a deliberate
scope boundary, but this document does not have enough evidence to say
which; flagging it for the architecture owner to confirm one way or the
other.

## 3. Can a user find/retrieve past outputs other than by knowing the ID?

**Answer: No, for the seven GTM-shell objects; partial, for two legacy
surfaces; and there is no cross-object view at all.**

Evidence:

1. **No canonical Artifact/Output object or store exists.** Confirmed
   precisely, per the task brief's instruction to check both meanings:
   - `app/artifact_store.py` — read in full. Its own docstring: "Atomic,
     version-aware persistence for canonical file artifacts... The store
     deliberately does not become business truth. It only centralizes
     safe writes to the existing YAML/Markdown/JSONL artifacts." It
     exposes `ArtifactStore.read_bytes()`/`update_bytes()` only — no
     `list()`, no `search()`, no HTTP route anywhere calls it directly
     (every `app/*_store.py` in the matrix wraps it internally). This is
     the **low-level atomic-write primitive**, and it is used by every
     other store in this repo (`signal_store`, `demand_store`,
     `fit_store`, `research_case_store`, `claim_store`, `evidence_store`,
     `target_plan_store`, `reach_store`, `engagement_store`,
     `network_v1_store` all construct an `ArtifactStore` internally).
     It is **not** an artifact/output library in the "find my past
     research dossier" sense.
   - Searched for the other meaning: `grep -rln "class.*Artifact\|
     artifact_library\|output_library\|OutputStore\|dossier\|FTS" app/*.py`
     returns only `app/artifact_store.py` itself and `app/company360_view.py`
     (which merely references artifact-shaped IDs in its aggregation, not
     a library). No `app/artifact_library.py`, `app/output_store.py`, or
     equivalent exists.
   - `docs/gtm-transformation/07_WORKFLOW_HANDOFF_AND_ARTIFACT_MODEL.md`
     sketches a **planned directory convention**
     (`workspaces/<ws>/studies/<research_case_id>/`,
     `.../fits/<fit_id>/`, `.../targets/<target_plan_id>/`, etc.) but this
     is documentation-level scaffolding, not an implemented index — no
     code reads or writes to that literal layout, and no route resolves
     "give me everything under `workspaces/<ws>/`."
2. **Per-object lists exist but are siloed and filter-only.** A user can
   list Demands filtered by `status`/`company_entity_id`, Fits by
   `status`/`demand_id`, etc. (see Workstream A §0), but there is no
   query that spans object kinds — "show me everything produced for
   company X" requires opening `GET /companies/{id}/360`
   (`app/company360_view.py`), which itself only aggregates
   Signal + ResearchCase + Demand, **not** Fit, TargetPlan, Sequence,
   Conversation or Opportunity. A user cannot get "all outputs for this
   account" in one call anywhere in the API.
3. **The only free-text/full-text search in the whole codebase is scoped
   to two legacy, non-GTM-shell surfaces**, both behind the `?legacy=1`
   flag ADR-010 describes as present "for one release" and absent from
   primary navigation:
   - `app/catalog_search.py`'s `search_catalog`/`CATALOG_SEARCH.search`
     (`GET /api/catalog/search?q=...`), scoped to catalog offers.
   - `app/network_index.py`'s SQLite-backed `search_people`/
     `search_companies` (`GET /api/network/people|companies`), scoped to
     the network graph.
   Neither covers ResearchCase, Claim, Fit, TargetPlan, Sequence,
   Conversation or Opportunity content. Confirmed by reading
   `app/frontend/app.js`'s search wiring (`runCatalogSearch`,
   `runPeopleSearch`, `runCompaniesSearch` — the only three client-side
   search functions in the file) and by grepping `gtm-spaces.js` for any
   search input (none exists — every GTM-shell space is browse-only,
   filtered server-side by the single status-like field its list route
   accepts).
4. **Deep-linking by ID is the only universal retrieval path.** Every
   space's router (`router.js`'s `/w/{workspace}/{space}/{objectId}`
   pattern) and every `GET .../{id}` route works if the id is already
   known (e.g. from a prior session, a shared link, or a upstream
   object's cross-reference field). This is real and functional — it is
   not "nothing works" — but it means a user who has forgotten a research
   dossier's id, or wants to browse "Fits I closed last month across all
   accounts," has no supported path except paging through
   `GET /fit-assessments?status_filter=...` with a status they'd have to
   guess, or opening each account's 360 view one at a time (and even that
   omits Fit/Targets/Reach/Engagement/Pipeline, per point 2).

**Plain answer for the architecture owner: No — with the two narrow
exceptions of catalog-offer and network-people/company text search on the
legacy surface, a user cannot retrieve a past output without already
knowing its workspace-scoped ID or its single filterable status/owner
field. This is the concrete, evidence-based case for candidate Epic E15's
"Retrieval & Artifact Library" half.** The "Universal CRUD" half of E15's
candidate name is separately supported by §1's finding that 8 of 10
canonical objects have no HTTP write path at all.

## 4. What a next-wave Epic should conservatively target, if anything

Per the task brief's own steer ("be conservative, most gaps are probably
'defer, not urgent'"), this section separates what looks genuinely
load-bearing from what looks like accepted, already-documented scope
boundaries:

- **Genuinely worth the architecture owner's attention for E15 scoping**:
  (a) the complete absence of any cross-object retrieval/search over
  business outputs (§3) — this is a real, confirmed capability gap, not
  a documentation gap; (b) the repeated "read-only over HTTP" pattern
  across TargetPlan/Sequence/Conversation/Opportunity (§1), which five
  separate Epics each deferred individually and which a single follow-on
  Epic could resolve once, using Demand/Fit's `expected_version` pattern
  as the template, **if** the business now needs those write paths (this
  document takes no position on whether it does — that is a product
  decision, not something derivable from reading the code).
- **Worth a narrow, separate ticket, not an Epic**: the unwired
  `opportunity_notes.py` functions (§2); the loss of prior field values
  on every Demand/Fit PATCH (§1's audit finding) if change history is
  ever needed; ResearchCase/Claim specifically (Research sits upstream of
  everything else, so a write gap there has more downstream leverage
  than, say, Reach's).
- **Probably fine to defer indefinitely / not a gap at all**: Product's
  immutable-snapshot design (intentional); Signal's lack of a general
  PATCH (consistent with "evidence before inference," a signal is meant
  to stay a thin, largely immutable pointer); the absence of HTTP
  delete/archive anywhere (nothing in the researched acceptance docs or
  code comments suggests any Epic considered this a requirement it
  deferred — it appears to be a genuine non-goal so far, worth confirming
  with the architecture owner rather than assuming it is a gap).

---

## Proposal statement (required closing)

This document is a **proposal for the human/architecture-owner to
ratify**, produced as CLAUDE_01 Workstream D gap analysis. It is not
authorization to implement any write route, search index, or artifact
library. The evidence above — read directly from `app/*_routes.py`,
`app/*_store.py` and cross-checked against every `EPIC_0X_ACCEPTANCE.md`
"Known limitations" section — is offered so that candidate Epic E15
("Universal CRUD, Retrieval & Artifact Library") can be scoped from
verified facts rather than re-derived from scratch; the actual decision
to start E15, its shape, and its sequencing against the other read-only
gaps named above remain the architecture owner's to make.
