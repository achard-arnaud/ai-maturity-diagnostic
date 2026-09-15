# 10 — Matrice de tests et critères d'acceptation

## 1. Invariants

| ID | Invariant |
|---|---|
| INV-001 | SideStory ne crée jamais de preuve |
| INV-002 | Objection simulée reste hypothesis |
| INV-003 | Title ne prouve jamais authority |
| INV-004 | Newsflow ne change jamais le fit |
| INV-005 | FAIL hard gate bloque progression |
| INV-006 | Follow-up exige un delta |
| INV-007 | Red-team = max 1 repair + 1 verify |
| INV-008 | Dreaming ne promeut pas automatiquement |
| INV-009 | Storage reste abstrait |
| INV-010 | Aucun outbound automatique sans PRD/ADR dédié |

---

## 2. Fit tests

### FIT-01 Strong fit, weak authority
Expected : `VALIDATION_READY`, pas `OUTREACH_READY`.

### FIT-02 Strong fit, strong anti-fit
Issue créée, validation question, pas de faux downgrade en FAIL sans gate prouvé.

### FIT-03 Newsflow only
`why_now` populated, fit inchangé.

---

## 3. Side-story tests

- SS-01 No lineage → Fail.
- SS-02 No payoff → Fail.
- SS-03 False lead → Allowed if evidence-bounded.
- SS-04 Callback stale → Warn/fail selon freshness policy.
- SS-05 Story changes evidence status → Fail.

---

## 4. Outreach tests

- OUT-01 Generic wedge → Semantic warning.
- OUT-02 Unsupported pain → Fail.
- OUT-03 Gatekeeper fake urgency → Fail policy.
- OUT-04 Gatekeeper routing request → Pass.
- OUT-05 Too many side stories → Fail composition budget.

---

## 5. Follow-up tests

- FUP-01 Same wedge/source/CTA, new wording only → Fail `FOLLOWUP_NO_NEW_DELTA`.
- FUP-02 New sector RETEX → Pass if sourced.
- FUP-03 New post but no analytical link → Fail/warn.
- FUP-04 New person routing → Pass as routing delta.

---

## 6. Reactivation tests

- REA-01 stale + no delta → WAIT.
- REA-02 stale + fresh trigger + useful callback → REACTIVATE.
- REA-03 stale + repeated refusal mechanism → RETIRE or WAIT.

---

## 7. Red-team tests

- RT-01 No credible attack → SURVIVES.
- RT-02 Narrowing → 1 repair, verify pass.
- RT-03 Pivot → Decision changes.
- RT-04 Targeted reopen → Only named dimension reopened.
- RT-05 Second repair → Forbidden.

---

## 8. Dreaming tests

- DR-01 local mistake → NO_REUSABLE_DELTA.
- DR-02 recurring missing-delta followups → candidate linter rule.
- DR-03 predicted vs actual objection mismatch repeated → candidate qualification policy.
- DR-04 one surprising success → Tier 1 candidate only, no promotion.

---

## 9. End-to-end scenario

```text
Company demand observed
→ offer fit PURSUE
→ contact target current
→ anti-fit issue "internal build"
→ wedge "repeated orchestration cost"
→ technical-buyer objection simulation
→ wedge survives with narrowing
→ side story comparator promoted
→ outreach plan passes linter
→ outcome "not now"
→ timing issue resolves/updates
→ 90 days later sector RETEX appears
→ callback side story
→ reactivation candidate
→ linter confirms new delta
→ response received
→ predicted-vs-actual comparison
→ loopback event
→ dreaming
```

Chaque transition doit être inspectable.

---

## 10. CI quality gates

```text
contracts
→ unit
→ integration
→ regression fixtures
→ semantic smoke tests
→ privacy/boundary tests
```

CI échoue sur :

- schema drift ;
- unlineaged promoted story ;
- invalid evidence promotion ;
- follow-up without delta ;
- gate bypass ;
- recursive repair ;
- forbidden outbound action.

---

## 11. Release acceptance

Feature peut quitter shadow mode seulement si :

- zero evidence-boundary regression ;
- no unexpected state mutation ;
- negative fixtures pass ;
- human reviewers comprennent pourquoi une issue/story a été générée ;
- storage backend swappable sans domain change ;
- rollback = disable feature flag + ignore optional artifacts.
