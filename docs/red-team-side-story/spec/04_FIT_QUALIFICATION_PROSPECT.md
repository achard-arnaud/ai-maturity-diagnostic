# 04 — Fit Catalogue / Use Case / Personne → Prospect

## 1. Objectif

Renforcer le passage :

```text
catalogue produit
+
use cases entreprise
+
personne
→ prospect qualifié
```

sans réduire la décision à un score de similarité.

Le système actuel sépare screening réseau, demande entreprise, vérité produit, fit opportunité et ciblage personne. Cette spec ajoute :

```text
FIT POSITIF
+
ANTI-FIT
+
ISSUES
+
TIMING
+
ROLE CONFIDENCE
+
WEDGE READINESS
```

---

## 2. Nouvelles lectures

### `CapabilityFit`
Pourquoi l'offre peut créer de la valeur.

### `AntiFit`
Meilleure raison de ne pas poursuivre.

### `AuthorityFit`
Pourquoi cette personne peut jouer un rôle utile. Ne jamais déduire l'autorité du titre.

### `TimingFit`
Pourquoi maintenant. Le newsflow peut alimenter `why_now`, jamais le fit.

### `WedgeReadiness`
Existe-t-il un angle de conversation suffisamment précis et utile ?

---

## 3. Fit matrix augmentée

```yaml
opportunity:
  fit_decision: PURSUE
  fit_score: 82
  positive_fit:
    claim_ids: [...]
    use_case_ids: [...]
    product_capability_ids: [...]
  counter_fit:
    strongest_anti_fit:
      issue_id: ISS-ANTI-003
      statement: "Internal build may already be deliberate."
      status: hypothesis
  timing:
    why_now:
      source_ids: [...]
      confidence: medium
  validation_questions:
    - "Le build interne est-il stratégique ou subi ?"
  wedge_readiness:
    status: VALIDATE
    blocker: "No evidence that repeated orchestration is painful."
```

---

## 4. Counter-Perspective métier

Ne pas appeler cela `System Red-Team`.

```yaml
counter_perspective:
  cp_id: CP-FIT-...
  domain: fit
  target: "PURSUE"
  hypothesis: "L'équipe préfère internal build."
  status: hypothesis
  source_basis: [...]
  issue_id: ISS-ANTI-...
  can_reverse_decision: true
```

---

## 5. Qualification de la personne

Lecture symétrique :

```text
why_this_person
+
why_not_this_person
```

```yaml
person_fit:
  person_id: PER-...
  roles: [technical_sponsor]
  positive:
    - "platform remit"
  issues:
    - ISS-AUTH-014
  anti_fit:
    - "No evidence of budget authority"
  action:
    "technical discovery, not commercial pitch"
```

---

## 6. Prospect state

Proposition :

```text
NOT_READY
VALIDATION_READY
OUTREACH_READY
DISCOVERY_READY
PILOT_READY
```

`OUTREACH_READY` nécessite :

- valid current role ;
- valid fit decision ;
- no FAIL hard gate ;
- au moins un why-now légitime ou un cold angle autonome ;
- primary objection hypothesis ;
- bounded CTA.

---

## 7. Wedge

Définition :

> Le plus petit angle crédible qui mérite l'attention du prospect maintenant.

```yaml
wedge:
  wedge_id: WDG-...
  prospect_id: ...
  proposition: "..."
  trigger_ids: [...]
  issue_ids: [...]
  side_story_ids: [...]
  primary_objection: ISS-OBJ-...
  ask:
    effort: low
    type: validate_question
  status: candidate|validated|retired
```

---

## 8. Wedge selection

```python
def select_wedge(candidates):
    eligible = [
        w for w in candidates
        if w["evidence_coverage"] != "none"
        and w["ask"]["effort"] == "low"
        and w["novelty"] is True
        and w["primary_objection_resolved"] is not False
    ]
    return max(eligible, key=lambda w: w["decision_relevance"], default=None)
```

Ce n'est pas un scoring absolu ; c'est une policy de sélection.

---

## 9. Do-not-contact gate

Le système peut conclure :

```text
WAIT_FOR_TRIGGER
DO_NOT_CONTACT_YET
RETIRE_TARGET
```

pour empêcher le matching de devenir une usine à messages.

---

## 10. Tests

- fit élevé + no person authority → validation only ;
- fit élevé + no why-now → cold outreach seulement si wedge autonome ;
- strong anti-fit unresolved → `VALIDATE`, pas `PURSUE` automatique ;
- title-only authority → linter fail ;
- side story hypothesis cannot become demand fact.
