# Harvest notes: `skills-notes-and-storytelling` for E16/E17

Status: RESEARCH ONLY. No runtime code was written or modified as part of this
note. Nothing here is authorization to build.

Source repo read at commit `c10f0d3` (branch head, 2026-09-16), local clone at
`/home/user/skills-notes-and-storytelling` (`origin` =
`https://github.com/achard-arnaud/skills-notes-and-storytelling`).

Evidence for `ai-maturity-diagnostic`'s own machinery: `app/claim_store.py`,
`app/research_case_store.py`, `app/research_orchestration.py`,
`app/research_evals.py`, `app/research_redteam.py`, `app/research_review.py`,
`app/research_policy.py`, `app/evidence_store.py`, `app/learning_proposals.py`,
`app/learning_experiments.py`, `docs/gtm-transformation/02_DOMAIN_AND_TRUTH_MODEL.md`,
`skills/tech-leadership-org-intelligence/scripts/build_org_tech_note.py`,
`scripts/check_release.py` — all read in full or in the relevant part.

---

## 1. Research/evidence-to-output patterns

`skills-notes-and-storytelling`'s pipeline (`SKILL.md`, `references/workflow.md`)
runs `MODE_SELECTED → CONTEXT_FRAMED → RESEARCHED → FRAGMENTED →
CLAIMS_GRAPHED → RERANKED → SCAFFOLDED → DRAFTED → ...`. Its contracts:

| Capability | Contract file | Shape |
|---|---|---|
| Atomic fragment | `contracts/fragment.schema.json` | `id, source_id, source_locator, content, evidence_status (verified\|vendor_claim\|inference\|hypothesis\|unknown), observed_at, confidence, tags` |
| Typed claim | `contracts/claim.schema.json` | `id, statement, claim_type (fact\|inference\|hypothesis\|recommendation\|unknown), fragment_ids, decision_relevance, evidence_strength, explanatory_power, novelty, audience_fit, hard_gate, falsifier` |
| Claims graph | `contracts/claims-graph-light.schema.json` | claims + typed edges (`supports\|contradicts\|qualifies\|causes\|depends_on\|compares_to\|answers\|motivates`, extended in workflow.md with `integrates_with\|substitutes\|complements\|enables`) |
| Scaffold | `contracts/scaffold.schema.json` | per-section `question, claim_ids, payload (prose\|bullets\|table\|diagram\|mixed), source_coverage_target, max_density_words` |
| Reranking | `references/workflow.md` | fixed weights: decision relevance 30% / evidence strength 25% / explanatory power 20% / novelty 15% / audience fit 10%; hard gates and contradictions sit outside the score |
| Sourcing | `references/workflow.md` step 9, `references/bridges-integration-and-run-memory.md` | source classification by *type* (`primary_vendor \| primary_regulatory \| primary_repo \| customer_or_partner \| analyst_or_research \| community \| supplied_context \| internal_inference`) and by *analytical role* (`account_truth \| product_truth \| market_peer \| ...`) |

**Cross-reference against `ai-maturity-diagnostic`'s own machinery — this is
the important part.**

- **Fragment vs Evidence — DUPLICATE.** `app/evidence_store.py`'s
  `CanonicalEvidenceV1` (`evidence_id`, `evidence_grade`, `entity_refs`, …) is
  already a source-addressable atomic evidence unit. It is functionally the
  same abstraction as `ResearchFragment` (source_id + locator + content +
  status + confidence). The skill's fragment schema adds nothing
  `evidence_store.py` doesn't already give you except a slightly different
  status vocabulary (`verified/vendor_claim/inference/hypothesis/unknown` vs
  a graded `evidence_grade` including a defined `N0` non-fact grade in
  `research_policy.py`). **Do not adopt a parallel "fragment" concept.**
  `REJECT` as a new object; `REFERENCE_ONLY` for the status vocabulary if a
  future contamination-style content check on evidence text is wanted.

- **Typed claim graph vs `app/claim_store.py` + `app/research_policy.py` —
  DUPLICATE, and `ai-maturity-diagnostic`'s version is stricter.**
  `research_policy.py::validate_claim_lineage` already enforces: a `fact`
  claim needs ≥1 non-`N0` evidence_id; an `inference` needs evidence or a
  parent claim; a `hypothesis` needs an explicit `hypothesis_owner` and
  `hypothesis_due_at`; and `is_claim_type_promotion` explicitly forbids any
  automated promotion toward `fact`. The skill's `claim.schema.json` has the
  same five-way typing (`fact|inference|hypothesis|recommendation|unknown`)
  and per-claim scores (`decision_relevance`, `evidence_strength`,
  `explanatory_power`, `novelty`, `audience_fit`, `hard_gate`, `falsifier`)
  but *no* code-level lineage validator and *no* explicit non-promotion
  guarantee — those live only as prose rules in `SKILL.md`/`workflow.md`.
  **Verdict: `REFERENCE_ONLY` for the graph edge vocabulary
  (`supports/contradicts/qualifies/causes/depends_on/compares_to/answers/
  motivates/integrates_with/substitutes/complements/enables`) and the 5-axis
  reranking weights (novel to `ai-maturity-diagnostic`, worth an
  `EXTRACT_PATTERN`), but the claim object and its lineage rules must stay
  owned by `research_policy.py`/`claim_store.py` — do not import a second
  claim schema.**

- **Bounded reranking — EXTRACT_PATTERN, small genuine gap.**
  `ai-maturity-diagnostic` has no equivalent of a documented, weighted
  reranking formula for claims prior to scaffolding; it has gating
  (`compute_completeness`, `can_transition_case`) and eval thresholds
  (`research_evals.py`) but nothing that ranks claims by decision relevance
  for narrative construction. The skill's 5-dimension weighted rerank
  (with hard gates kept outside the score) is a genuinely useful, small,
  copyable *pattern* (not code — the skill has no Python implementation of
  it, only doc prose) for a future document/report-composition module. This
  is squarely an **E17** (composition), not E13/research, concern.

- **Per-decision scaffolding — genuine gap, but scoped to E17, not
  research.** `contracts/scaffold.schema.json` (section → question → claim
  IDs → payload type → density/coverage target) has no equivalent anywhere
  in `ai-maturity-diagnostic`, because `ai-maturity-diagnostic` does not yet
  have a narrative/document composition layer — only data stores and a
  DOCX builder driven directly from a hand-authored JSON config
  (see §5). `EXTRACT_PATTERN` candidate for **E17** "Document Composition,
  Templates & Export"; it is not a research-pipeline gap, so it should not
  be scoped into E16 research work.

- **Sourcing / provenance — PARTIAL DUPLICATE.** `ai-maturity-diagnostic`
  already tracks evidence provenance and grading; it does not yet have the
  skill's two-axis source classification (source *type* vs analytical
  *role*) as a first-class field. This is a thin, low-risk `ADAPT` if E16
  ever needs to reason about "is this account-truth or market-peer
  evidence" — but it should be added as new fields on the existing
  `CanonicalEvidenceV1` record, never as a separate store.

**Summary for Q1:** the skill's evidence/claims layer is almost entirely a
re-description of what `research_policy.py` + `claim_store.py` +
`evidence_store.py` already implement, in most respects less strictly (no
code-enforced lineage rules, no non-promotion guarantee, no separation of
duties on review — see §3). The two things genuinely absent from
`ai-maturity-diagnostic` are (a) a weighted claim-reranking formula and (b) a
per-section document scaffold contract — both belong to composition/
storytelling (E17), not to the research pipeline (which should stay owned by
the existing `app/research_*` modules).

---

## 2. "Three lenses" (Product/Business/Technical) review pattern

Defined in `SKILL.md` ("Review lenses") for **QA** (conformance /
counter-perspective / reader-decision review — a genuinely distinct, useful
triage of *review* concerns) and separately in
`references/bridges-integration-and-run-memory.md` for the `INTEGRATION_NOTE`
template's **content structure**: every integration decision is analyzed
through a **technical**, **product** and **business** lens before a single
`BUILD | BUY | PARTNER | COEXIST | DEFER` decision is made.

These are two different "three lenses" and must not be conflated:

1. **Review-lens triage (conformance / counter-perspective / reader-decision)**
   is a process-quality pattern, not a truth-ownership pattern — it does not
   produce three parallel facts about the same object, only three checklists
   applied to one draft. This is safely reusable and has no tension with
   `ai-maturity-diagnostic`'s truth model. `EXTRACT_PATTERN` if a document/
   review module is ever built (E17), `REFERENCE_ONLY` otherwise.

2. **The technical/product/business analysis-dimension lens for
   architecture/integration notes** (`analysis_dimension` in `SKILL.md`,
   §"Analysis dimension") is different: it explicitly states "the three
   dimensions share the evidence pipeline but **do not share the same
   decision spine**" and that the *primary* dimension "governs research
   reranking, scaffold, side stories, counter-perspective and visual
   architecture." In other words, the same underlying evidence can produce
   three different decision spines/recommendations depending on which lens
   is primary, and secondary lenses are allowed to run alongside it.

   **This is the tension the task asked me to flag.** `ai-maturity-diagnostic`'s
   own `docs/gtm-transformation/02_DOMAIN_AND_TRUTH_MODEL.md` assigns each
   bounded context exactly one owned truth per object ("Vérité possédée")
   and explicitly lists what that context "never deduces alone" — the
   architecture is built around *no* competing sources of truth for the same
   object. If E16/E17 imported the "three lenses, three decision spines"
   pattern literally, and a single account/opportunity/architecture object
   ended up with a technical verdict, a product verdict and a business
   verdict that could each independently say `BUILD` vs `DEFER` for the same
   underlying question, that would be exactly the multiple-competing-truths
   situation the anchors forbid — the skill mitigates this only by picking
   one *primary* dimension per run, which is a workflow discipline, not a
   structural guarantee.
   - **Verdict:** `ADAPT`, not `REUSE_AS_IS`. If harvested, the three lenses
     must be modeled as three *evaluation facets feeding one owned decision
     record* (e.g., three scored inputs into a single
     `IntegrationDecision`/`ArchitectureDecision` object with one `status`
     field and one owning bounded context), never as three independently
     persisted decisions on the same entity. This should be an explicit ADR
     question, not an implementation default.

---

## 3. Counter-perspective / bounded falsification vs `app/research_redteam.py`

Read `app/research_redteam.py` in full (131 lines). It already implements:

- `open_side_story` / `resolve_side_story` / `dismiss_side_story`: a bounded
  side-investigation object that **must** have an owner, and that can only
  close by reconnecting to the parent claim (`supersedes_claim_id` or
  `derived_from_claim_ids` must reference the parent) or by an explicit,
  reasoned dismissal. A side story can never "silently vanish."
- `find_contradictions`: pairs of active claims that contradict each other
  via `contradicted_by_claim_ids`.
- `run_redteam_checklist`: per-claim structured checklist covering
  contradictory evidence, an open side story chasing an alternative
  explanation, and an unresolved dependency — explicitly citing
  "08_EVIDENCE_DECISION_AND_GATES.md's *Red-team fonctionnel*: every major
  decision must look for an alternative explanation, a falsifier,
  contradictory evidence, and an unresolved dependency."

The skill's counter-perspective/red-team pass
(`references/workflow.md` §"Counter-perspective / red-team QA",
`references/dreaming-self-healing.md` §"Counter-perspective contract") does,
prose-wise, the same job: name the proposition that would most damage the
conclusion, find the strongest credible counter-evidence, decide one of
`SURVIVES_RED_TEAM | SURVIVES_WITH_NARROWING | PIVOT_REQUIRED |
REOPEN_TARGETED`, allow at most one repair pass and one verification pass.

**Direct comparison:**

| Capability | `research_redteam.py` | skill |
|---|---|---|
| Contradiction detection | `find_contradictions` — code, over `contradicted_by_claim_ids` | prose instruction to "search for disconfirming evidence" |
| Bounded, owned falsification branch | `open_side_story`/`resolve_side_story` — code, enforced reconnection to trunk, enforced owner | no equivalent object; the skill's "side story" (`contracts/side-story.schema.json`) is a *narrative* insertion (`dezoom\|method\|false_lead\|comparator\|analytical_focus\|callback`) for the *document*, not a research-branch-with-owner object |
| Verdict taxonomy | none (checklist only: booleans) | 4-way verdict enum, bounded 1 repair + 1 verification pass |
| Enforcement | code (`SideStoryError` raised on missing owner/reason, on dangling resolution) | markdown discipline only, no code |

**This is the single most important finding for Q3: the two are NOT the same
capability, but they are also not fully independent — they overlap on the
"bounded, owned falsification branch" primitive, which `ai-maturity-diagnostic`
already has in code and the skill only has as narrative convention.**
What the skill genuinely adds and `ai-maturity-diagnostic` does **not** have
today is the **verdict taxonomy plus the bounded repair/verification
loop-count discipline** (`SURVIVES_RED_TEAM` etc., "at most one repair pass,
at most one verification pass, else `REOPEN_TARGETED`"). That is a real,
narrow gap: `research_redteam.py` tells you a claim *has* an open
contradiction/side-story, but never tells you what to *do* about it or how
many repair cycles are allowed before you must stop and escalate.

- **Verdict:** `REFERENCE_ONLY` for the side-story-as-narrative-detour
  concept (already covered, better, by code in `research_redteam.py` +
  `research_case_store.py`'s status machine). `EXTRACT_PATTERN` (documentation
  pattern, not code import) for the four-way verdict enum and the
  "≤1 repair + ≤1 verification, else escalate" loop-bounding rule — this
  could plausibly be layered onto `research_redteam.py`'s existing checklist
  as a new pure function, but that is an E16 implementation decision for a
  human/architecture owner, not something to build from this note.

---

## 4. Dreaming/loopback vs `app/learning_proposals.py` + `app/learning_experiments.py`

Read both files in full (108 + 62 lines). E13's mechanism:

- `LearningProposalStore`: origin restricted to
  `{"retrospective", "red_team", "dreaming"}` — **note "dreaming" is already
  a literal recognized origin value in the E13 schema**, `target_kind` in
  `{"rule","skill","prompt","offer","workflow"}`, explicit state machine
  `draft → in_review → accepted → testing → measured` (or `rejected`), every
  transition requires `actor_id` + `rationale`, every transition is journaled
  to `EventJournal`, promotion to `testing` requires an `experiment_id`,
  promotion to `measured` requires a `result_ref`. No transition can skip a
  state.
- `learning_experiments.py`: `ExperimentPlan` (baseline/canary refs, minimum
  sample size, maximum regression, drift threshold) and `evaluate_experiment`,
  which computes improvement, checks an NRT-drift gate and a
  regression-magnitude gate, and returns `decision ∈ {continue, rollback,
  promote}` — **never applies the change itself**; the docstring is explicit:
  "bounded baseline/canary experiments and NRT drift gates," and the design
  is explicitly "no auto-mutation" per the task brief.

The skill's dreaming (`references/dreaming-self-healing.md`,
`SKILL.md` §"Feedback / dreaming"):

- Tiered `Tier 0 (NO_REUSABLE_DELTA) → Tier 1 (mandatory lightweight check,
  every run) → Tier 2 (targeted red-team loopback) → Tier 3 (explicit
  FEEDBACK_DREAMING multi-run review)`.
- `loopback_event` contract: `event_type ∈ {decision_correction,
  scope_narrowing, hard_gate_discovery, evidence_gap, bridge_correction,
  reusable_success_pattern, no_system_delta}`, proposition attacked, verdict,
  repair applied, reusable hypothesis, affected template/workflow/contract,
  promotion tier, regression-fixture-needed flag, stop condition.
- Hard rule, verbatim: "The system may propose, branch, test, render, report
  and open a draft PR. A human decides promote, revise, reject or retire."
- Promotion evidence scales with tier (Tier 1 = candidate note/fixture;
  Tier 2 = candidate patch + regression fixture; Tier 3 = canonical change
  proposal with compatibility/rollback analysis).

**This is the single most important finding for Q4, and it is a genuine,
non-trivial difference, not a rename of the same thing.**

Both systems share the *hard governance invariant* — proposals are surfaced,
never auto-applied; a human/gated experiment must approve promotion; every
step is evidenced and auditable. That invariant is not new; `ai-maturity-
diagnostic`'s version of it (E13) is materially **more rigorous** on the
*promotion* side: it has a real state machine with illegal-transition
rejection, mandatory experiment/result linkage before `measured`, and a
quantitative canary/drift-gated `evaluate_experiment` function with a
concrete rollback decision. The skill has **no equivalent code** — dreaming
is entirely a documentation/workflow discipline with no `evaluate_experiment`
equivalent, no drift gate, no state machine enforcement; "promotion" in the
skill terminates at "open a draft PR," with no canary/experiment step of its
own.

Where the skill's dreaming concept is **genuinely different, not a subset**
of E13: **it operates on document/template/workflow artifacts as the unit of
learning** (a template's scaffold, a workflow's counter-perspective depth
rule, a bridge map entry, a QA fixture), continuously, *within* every single
content-generation run (Tier 1 is mandatory on every run, not periodic).
E13's `LearningProposalStore`/`target_kind` enum (`rule, skill, prompt,
offer, workflow`) already includes `"workflow"` and `"skill"` as valid
targets — so **the *target surface* the skill's dreaming would touch (a
template, a workflow rule, a QA gate) already fits inside E13's existing
`target_kind` vocabulary without needing a new kind.** What's missing is not
a new learning-lifecycle mechanism, but a **trigger discipline**: E13 today
is retrospective/red-team-triggered per its `ORIGINS` set
(`retrospective, red_team, dreaming` — "dreaming" is already a listed origin
value, currently unused by any producer in the codebase I found), whereas
the skill mandates a *lightweight* dreaming check as an automatic tail stage
of every content-generation run, tiered by signal strength.

- **Verdict: the underlying governance mechanism (`LearningProposalStore` +
  `evaluate_experiment`) is `REUSE_AS_IS` — do not build a second proposal
  store or a second canary/experiment gate for E16/E17.** What is a genuine,
  narrow gap worth a human ADR decision is a **producer**: a function that,
  at the end of an E16/E17 content run, inspects run signal (QA defects,
  counter-perspective verdict, repeated adaptation) and — only when a
  reusable delta is evidenced — calls
  `LearningProposalStore.create(origin="dreaming", target_kind="workflow"|"skill"|"rule", ...)`.
  That producer is new work; the store and experiment gate it feeds are not.
  `ADAPT` (write a thin producer against the existing E13 store), `REJECT`
  building a parallel lifecycle/state-machine.

---

## 5. Document generation / DOCX / render-QA boundary

`ai-maturity-diagnostic` already ships a DOCX pipeline:
`skills/tech-leadership-org-intelligence/scripts/build_org_tech_note.py`
(python-docx + Pillow, ~hundreds of lines, read the header and structural
validation section) takes a **hand-authored JSON config** with a fixed
required-keys contract (`REQUIRED_TOP_LEVEL`: `meta, executive_thesis,
executive_summary, method_notes, legal_structure, orgchart, power_map, raci,
people, influence_map, contact_order, unknowns, sources`, plus a
`REQUIRED_PERSON` sub-shape and ID pattern validation for node/source IDs)
and either validates it (`--validate-only`) or renders a `.docx` directly.
`scripts/check_release.py` gates every release on **exactly this**: it runs
`build_org_tech_note.py --validate-only` against the checked-in example
config (`skills/tech-leadership-org-intelligence/assets/examples/
isagri_config.json`) as "DOCX example configuration," then a full
`--output` render as "DOCX example generation." This is a **structural
schema gate**, not a visual/render-QA gate — I found no page-by-page visual
inspection, no rendered-image comparison, and no QA-report artifact anywhere
in `skills/tech-leadership-org-intelligence/` or `scripts/check_release.py`.

`skills-notes-and-storytelling` has a formally versioned, narrower boundary
contract for exactly this seam:
`contracts/docx-runtime-interface.schema.json` defines the interface as
`{input: OutputSpecification, output: DocumentQAReport}` —
i.e. **the skill does not render DOCX itself**; it hands a layout-ready
`output-spec.schema.json` (sections, sources, and a `diagrams[]` array with
`mermaid_source, orientation, native/target width & height, scale_factor,
qa_status ∈ {pending, passed, rerender_required}`) to "a runtime DOCX
creation/editing skill," and gets back a `qa-report.schema.json`
(`content_contract, source_contract, style_contract, diagram_contract,
docx_visual_contract, pages_inspected, defects[], passed`) — an explicit
**visual** QA contract, including the rule (stated in `SKILL.md`'s workflow
step 11) that "Reader-facing DOCX diagrams must be rendered images, not
source markup."

**Comparison and verdict:**

- `build_org_tech_note.py` **is** the renderer (owns python-docx calls
  directly against a bespoke JSON shape specific to org/tech notes); the
  skill's contract assumes rendering is *someone else's* job and only
  specifies the interface to it. These are different layers, not
  competing implementations — the skill's contract does not obsolete
  `build_org_tech_note.py`, because `ai-maturity-diagnostic` has no separate
  "runtime DOCX renderer" skill to plug the interface into; it would need
  one built or `build_org_tech_note.py` itself would need to become the
  renderer behind such an interface.
- The **genuine, real gap** `ai-maturity-diagnostic` has today: no visual/
  render-QA report object and no CI gate on rendered visual correctness —
  only structural JSON-shape validation before render. If E17 needs to
  generalize beyond the single org/tech-note template family, the
  `output-spec.schema.json` / `qa-report.schema.json` pair is a clean,
  reusable *pattern* (generic template_type enum, diagram QA states,
  pass/fail contract fields) worth extracting — but as a **pattern to
  redesign against `ai-maturity-diagnostic`'s own template set**, not a
  file to copy in, since its `template_type` enum is specific to the
  skill's own 8 note templates (`architecture-note, one-pager, two-pager,
  benchmarking, buy-side-gap-analysis, diagnostic-reco-sellside,
  opportunity-note-icp, integration-note`), none of which are
  `ai-maturity-diagnostic` template names today.
- **Verdict: `EXTRACT_PATTERN`** for the output-spec/QA-report interface
  shape and the "diagrams must be rendered images, checked page-by-page,
  with an explicit rerender_required state" discipline — genuinely
  complements, does not duplicate or obsolete, `build_org_tech_note.py`'s
  existing structural gate in `check_release.py`. It fills a real hole
  (no visual QA today) rather than replacing anything that ships.

---

## License / maintenance / security check

- **License:** Apache License 2.0 (`LICENSE`, verified header). Compatible
  with harvesting patterns/text/schemas into `ai-maturity-diagnostic`
  (check `ai-maturity-diagnostic`'s own license compatibility before copying
  file text verbatim; copying documented *patterns* as newly written code/
  docs sidesteps this entirely and is the recommended path per the
  `EXTRACT_PATTERN` verdicts above).
- **Maintenance:** single-author repo; `git shortlog`/`git log` show every
  commit authored by `francois.arnaud.rjc@gmail.com` — i.e., the same person
  who owns `ai-maturity-diagnostic`. Last commit `c10f0d3` dated
  2026-09-16 (one day before this review), actively developed (workflow
  version 1.3.1, 15+ recent commits iterating the counter-perspective/
  dreaming machinery). Bus factor is shared with this repo, not an
  independent third-party dependency risk.
- **CI/security:** `.github/workflows/qa.yml` runs
  `scripts/validate_contracts.py` on PR/push to `dev`/`main` — this is a
  JSON-Schema contract linter (verified `scripts/` contents), not a security
  scanner; I found no dependency-vulnerability scanning, no secrets
  scanning, and no SAST configured in the repo. `scripts/validate_contracts.py`
  itself only validates schema files and fixtures, not runtime input — low
  security surface since the skill has **no executable pipeline code at
  all** (`src/template_types.py` is 53 lines of enums; there is no
  orchestrator, no network calls, no data store). This significantly lowers
  security-privacy risk for any harvest: everything importable from this
  repo today is documentation, JSON Schemas and an enum module, not running
  code with its own attack surface.

---

## Harvest table (per capability)

### A. Atomic fragment (`contracts/fragment.schema.json`)
- **CAPABILITY:** source-addressable atomic evidence unit
- **LICENSE:** Apache-2.0
- **CURRENT MATURITY:** schema only, no implementation, no tests beyond `validate_contracts.py`'s shape check
- **REUSE SURFACE:** none recommended — status vocabulary only
- **ADAPTATION REQUIRED:** n/a
- **SECURITY-PRIVACY:** none (schema text only)
- **COUPLING:** would duplicate `app/evidence_store.py`'s `CanonicalEvidenceV1`
- **MAINTENANCE:** single-author, same person as this repo
- **TEST STRATEGY:** n/a
- **EXIT STRATEGY:** n/a
- **DECISION: REJECT** (as a new object); optional `REFERENCE_ONLY` for status enum wording

### B. Typed claim + claims graph (`contracts/claim.schema.json`, `claims-graph-light.schema.json`)
- **CAPABILITY:** typed claim with scoring fields + typed graph edges
- **LICENSE:** Apache-2.0
- **CURRENT MATURITY:** schema only
- **REUSE SURFACE:** edge-type vocabulary and 5-axis reranking weights as documentation input to a future E17 module
- **ADAPTATION REQUIRED:** must be re-expressed against `app/claim_store.py`'s existing claim shape and `research_policy.py`'s lineage rules, not layered as a parallel schema
- **SECURITY-PRIVACY:** none
- **COUPLING:** high risk of duplicating `claim_store.py`/`research_policy.py` if copied literally
- **MAINTENANCE:** single-author, same person
- **TEST STRATEGY:** if adapted, extend `research_policy.py`'s existing unit tests, do not create a parallel test suite
- **EXIT STRATEGY:** documentation-only harvest has no exit cost
- **DECISION: REFERENCE_ONLY** (claim shape/lineage — already owned and stricter in `ai-maturity-diagnostic`); **EXTRACT_PATTERN** (edge vocabulary, reranking weights) for E17 only

### C. Per-decision scaffold (`contracts/scaffold.schema.json`)
- **CAPABILITY:** section-level document skeleton contract
- **LICENSE:** Apache-2.0
- **CURRENT MATURITY:** schema only
- **REUSE SURFACE:** pattern for E17 composition layer (no equivalent exists today)
- **ADAPTATION REQUIRED:** redesign `template_type` enum against `ai-maturity-diagnostic`'s own deliverables, not the skill's 8 templates
- **SECURITY-PRIVACY:** none
- **COUPLING:** none currently — genuine gap
- **MAINTENANCE:** single-author, same person
- **TEST STRATEGY:** new fixture-based tests would be needed if implemented
- **EXIT STRATEGY:** pattern-only harvest, no runtime dependency created
- **DECISION: EXTRACT_PATTERN**, scoped to E17, pending ADR

### D. Counter-perspective / bounded falsification (`references/workflow.md`, `references/dreaming-self-healing.md`)
- **CAPABILITY:** verdict-taxonomy + bounded repair/verification loop for red-team findings
- **LICENSE:** Apache-2.0
- **CURRENT MATURITY:** documentation/workflow discipline only, no code
- **REUSE SURFACE:** four-way verdict enum + "≤1 repair, ≤1 verification, else escalate" rule, layered onto existing `research_redteam.py`
- **ADAPTATION REQUIRED:** implement as a new pure function consuming `run_redteam_checklist`'s output; the underlying bounded-branch object (side story with owner) already exists in `research_redteam.py` and must not be reimplemented
- **SECURITY-PRIVACY:** none
- **COUPLING:** overlaps `research_redteam.py`, which already covers contradiction detection and owned/bounded branches in code
- **MAINTENANCE:** single-author, same person
- **TEST STRATEGY:** extend `tests` covering `research_redteam.py`
- **EXIT STRATEGY:** additive function, removable without touching existing store/schema
- **DECISION: REFERENCE_ONLY** for the side-story-as-branch concept (duplicate of existing code); **EXTRACT_PATTERN** for the verdict enum + loop-bound rule, pending ADR

### E. Dreaming / loopback (`references/dreaming-self-healing.md`)
- **CAPABILITY:** tiered, human-gated candidate-improvement detection over content-generation runs
- **LICENSE:** Apache-2.0
- **CURRENT MATURITY:** documentation/workflow discipline only, no code, no state machine, no experiment gate
- **REUSE SURFACE:** trigger/producer logic only — feeds the existing `LearningProposalStore`/`evaluate_experiment` machinery
- **ADAPTATION REQUIRED:** write a new producer function that calls `LearningProposalStore.create(origin="dreaming", target_kind=...)` at the tail of an E16/E17 run when a reusable delta is evidenced; do **not** build a second proposal lifecycle or a second canary/experiment gate
- **SECURITY-PRIVACY:** none directly; inherits E13's existing audit-journal guarantees once wired through `LearningProposalStore`
- **COUPLING:** must couple to `app/learning_proposals.py` and `app/learning_experiments.py`, not duplicate them
- **MAINTENANCE:** single-author, same person
- **TEST STRATEGY:** extend existing E13 test coverage for `LearningProposalStore`/`evaluate_experiment` with the new producer's fixtures
- **EXIT STRATEGY:** the producer can be deleted without touching E13's store/state machine; no lock-in
- **DECISION: ADAPT** (thin producer against existing E13 store); **REJECT** any parallel lifecycle/state-machine; underlying E13 mechanism itself is **REUSE_AS_IS**

### F. Output-spec / render-QA boundary (`contracts/output-spec.schema.json`, `qa-report.schema.json`, `docx-runtime-interface.schema.json`)
- **CAPABILITY:** layout-ready spec → visual QA report interface, incl. diagram-as-rendered-image rule and page-by-page inspection gate
- **LICENSE:** Apache-2.0
- **CURRENT MATURITY:** schema only, no reference renderer/QA implementation in this repo either
- **REUSE SURFACE:** genuine gap-filler — `ai-maturity-diagnostic`'s only DOCX gate today (`check_release.py`'s two DOCX steps) is structural JSON-shape validation, not visual QA
- **ADAPTATION REQUIRED:** redesign `template_type` enum against `ai-maturity-diagnostic`'s own template set (not the skill's 8 templates); needs an actual renderer/inspector behind it, which does not exist in either repo today
- **SECURITY-PRIVACY:** none directly; a future renderer would need normal file-handling review
- **COUPLING:** complements, does not replace, `build_org_tech_note.py`'s existing structural gate in `scripts/check_release.py`
- **MAINTENANCE:** single-author, same person
- **TEST STRATEGY:** would need new CI step(s) alongside the existing "DOCX example configuration/generation" checks, not a replacement of them
- **EXIT STRATEGY:** additive CI gate; removable without touching `build_org_tech_note.py`
- **DECISION: EXTRACT_PATTERN**, scoped to E17, pending ADR

### G. "Three lenses" review pattern
- **CAPABILITY (i):** conformance / counter-perspective / reader-decision review triage
- **DECISION (i): EXTRACT_PATTERN** (E17), no truth-ownership risk
- **CAPABILITY (ii):** technical/product/business analysis-dimension lens producing per-dimension decision spines
- **DECISION (ii): ADAPT ONLY**, and only as three scored facets feeding **one** owned decision record per bounded context — never as three independently persisted verdicts on the same object. Flag explicitly for ADR: this is the one place a literal import would violate `02_DOMAIN_AND_TRUTH_MODEL.md`'s no-competing-truths anchor.
- **LICENSE / MAINTENANCE / SECURITY:** as above (Apache-2.0, single-author, no code)

---

## Headline recommendation

Treat `skills-notes-and-storytelling` primarily as a **composition/narrative
reference (E17)**, not a research-pipeline source (E16): its evidence/claims
layer mostly re-describes what `app/research_*` and `app/*_store.py` already
implement, usually with less code-level enforcement. The two capabilities
with the most standalone value — the counter-perspective verdict taxonomy
(§3) and the dreaming-producer gap against E13 (§4) — are both narrow,
additive, and should be adapted *onto* existing modules
(`research_redteam.py`, `learning_proposals.py`), never as parallel systems.
The output-spec/render-QA contract (§5) is the cleanest genuine gap-filler
because `ai-maturity-diagnostic` has no visual QA today, only structural
validation. The "three lenses" pattern for architecture/integration
decisions requires explicit adaptation to avoid producing multiple competing
sources of truth for one object, which the domain/truth-model doc forbids.

**No runtime code, module, schema or dependency should be built, imported, or
wired into `ai-maturity-diagnostic` on the basis of this note alone. Every
`ADAPT`, `WRAP` and `EXTRACT_PATTERN` decision above is a proposal for a
human/architecture-owner to ratify through an accepted ADR — this document
satisfies research/evidence gathering only, and stops at the repo's own
harvest gate G4.**
