# 02 — Issue Engine : tensions, inconnues, objections et questions ouvertes

## 1. Pourquoi un Issue Engine

Le projet possède déjà des blockers, unknowns, hard gates, contradictions et falsifiers. Ils restent distribués.

L'Issue Engine ne les remplace pas. Il fournit un **index transversal et temporaire** pour les éléments qui exigent résolution, validation, arbitrage, changement d'angle, réouverture ciblée ou follow-up.

Il s'inspire du mécanisme de pending questions : une question peut être ouverte, partiellement résolue ou promue en claim sans disparaître artificiellement.

---

## 2. Types d'issues

```text
evidence_gap
contradiction
anti_fit
hidden_gate
role_uncertainty
authority_uncertainty
objection_hypothesis
timing_uncertainty
stale_signal
message_risk
gatekeeper_routing
followup_failure
reactivation_trigger
market_delta
sector_retex
process_defect
system_defect
```

Une `objection_hypothesis` n'est pas une objection réelle.

---

## 3. Lifecycle

```text
OPEN
→ TRIAGED
→ {
    RESOLVED,
    PARTIALLY_RESOLVED,
    PROMOTED_TO_ACTION,
    WAITING_EVIDENCE,
    RETIRED
  }
```

Contrairement à un blocker, toutes les issues ne bloquent pas. Certaines enrichissent la décision, certaines deviennent une side story, certaines servent uniquement au dreaming.

---

## 4. Contrat

```yaml
issue:
  issue_id: ISS-...
  kind: objection_hypothesis
  owner_stage: reach
  subject_refs:
    study_id: STUDY-...
    company_id: CMP-...
    person_id: PER-...
    offer_id: OFF-...
  statement: "Le prospect peut préférer internal build."
  epistemic_status: hypothesis
  lineage:
    claim_ids: []
    source_ids: []
    artifact_paths: []
  decision_impact:
    can_change_fit: false
    can_change_reach: true
    can_change_angle: true
    severity: medium
  resolution:
    status: OPEN
    required_evidence: []
    owner_skill: iterative-reach-matchmaking
    action: "Discovery question"
    falsifier: "Prospect confirms repeated build burden"
  story_candidate:
    eligible: true
    suggested_kind: comparator
```

---

## 5. Règles anti-contamination

1. `Issue.epistemic_status=hypothesis` ne peut pas alimenter un claim `fact`.
2. Une issue business ne modifie pas un product profile canonique.
3. Une objection simulée ne modifie pas l'historique du prospect.
4. Un silence ne prouve pas un motif.
5. Une issue résolue par réponse réelle conserve la source/outcome.
6. Une issue peut influencer confidence, next validation, message angle, wave, wait/reactivate ; elle ne peut pas créer la preuve manquante.

---

## 6. Relation avec les Blockers

Le blocker répond :

> Pourquoi ne peut-on pas avancer ?

L'issue répond :

> Quelle tension faut-il comprendre ou exploiter ?

Conversion possible :

```text
Issue(hidden_gate)
→ evidence confirms critical gate
→ Blocker
```

mais pas l'inverse automatiquement.

---

## 7. Issue triage

```python
def triage_issue(issue, decision_context):
    if issue.kind == "hidden_gate" and issue.decision_impact["severity"] == "critical":
        return "RESOLVE_BEFORE_ADVANCE"
    if issue.kind in {"objection_hypothesis", "timing_uncertainty"}:
        return "USE_IN_DISCOVERY"
    if issue.kind in {"market_delta", "sector_retex", "reactivation_trigger"}:
        return "SIDE_STORY_CANDIDATE"
    if issue.kind == "system_defect":
        return "LOOPBACK"
    return "KEEP_OPEN"
```

---

## 8. Issue Graph Light

Ne pas créer de graph DB.

```text
ISSUE --challenges--> DECISION
ISSUE --qualifies--> CLAIM
ISSUE --blocks--> ACTION
ISSUE --suggests--> SIDE_STORY
OUTCOME --resolves--> ISSUE
ISSUE --reopens--> DECISION_SCOPE
ISSUE --feeds--> LOOPBACK_EVENT
```

---

## 9. Exemple fit

```text
Fit score élevé
↓
ISS-ANTI-001
"Le problème est peut-être déjà résolu en interne."
↓
CounterPerspective
↓
required_validation:
"internal build deliberate vs repeated burden"
↓
Reach discovery
↓
Outcome:
"repeated burden confirmed"
↓
Issue RESOLVED
↓
fit confidence ↑
```

---

## 10. Exemple lead stale

```text
No response 60 days
↓
ISS-STALE-009
kind=followup_failure
statement="L'angle initial n'a produit aucun signal."
↓
No assumption on WHY
↓
search delta
↓
ISS-REACT-011
kind=sector_retex
↓
SideStory candidate
↓
new outreach
```
