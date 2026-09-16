# 06 — Follow-up et réactivation des leads stale

## 1. Principe

Le silence n'est pas une preuve de motif. C'est seulement un événement :

```text
NO_RESPONSE
```

Éviter :

```text
message A
→ paraphrase A
→ paraphrase A
```

Chaque relance nécessite un **delta identifiable**.

---

## 2. Stale lead workflow

```text
LAST CONTACT STATE
→ OUTCOME / SILENCE
→ ISSUE: followup_failure
→ RETROSPECTIVE OF OLD ANGLE
→ DELTA SEARCH
→ NEW ISSUE / SIGNAL
→ NEW SIDE STORY
→ OBJECTION SIMULATION
→ REACTIVATE | WAIT | RETIRE
```

---

## 3. Sources de delta

### Prospect-side
post, changement de poste, recrutement, nouveau produit, annonce, architecture, partenariat, réglementation, incident, event.

### Seller-side
nouveau client, RETEX, use case clôturé, nouvelle feature, pricing, intégration, benchmark, proof point.

### Market-side
concurrent, standard, régulation, incident sectoriel, nouveau pattern technologique.

### Relationship-side
intro, nouvel interlocuteur, rencontre, event commun, feedback d'un pair.

---

## 4. Delta contract

```yaml
reactivation_delta:
  delta_id: DELTA-...
  kind: sector_retex
  observed_at: 2026-09-15
  source_ids: [...]
  relevance_to_prospect:
    status: hypothesis
    rationale: "..."
  expires_at: optional
```

---

## 5. Reactivation candidate

```yaml
reactivation:
  reactivation_id: REACT-...
  prior_message_ids: [...]
  stale_days: 90
  old_issue:
    issue_id: ISS-STALE-...
  delta_ids: [DELTA-...]
  side_story_id: SS-CALLBACK-...
  pressure_test:
    likely_refusal_issue: ISS-OBJ-...
    result: SURVIVES_WITH_NARROWING
  decision:
    REACTIVATE|WAIT|RETIRE
```

---

## 6. Innovation forcée par contre-perspective

Policy :

```text
Generate 2 materially different angles
→ simulate strongest refusal for each
→ reject angles with same failure mechanism
→ select survivor
```

« Matériellement différent » signifie changer au moins une dimension : trigger, value hypothesis, evidence, perspective, persona, ask, proof point.

Simple reformulation = rejetée.

---

## 7. RETEX sectoriel

Pattern :

```text
case in same sector
→ extract unexpected mechanism
→ compare to prospect context
→ caveat
→ discovery question
```

Mauvais :

> Nous venons de travailler avec une entreprise de votre secteur.

Meilleur :

> Sur un cas comparable, nous pensions que le gain principal serait X. Le point bloquant s'est finalement déplacé vers Y. Votre contexte présente un mécanisme proche sur Z ; est-ce un sujet que vous avez rencontré ?

Le lien au prospect reste hypothétique tant qu'il n'est pas confirmé.

---

## 8. Post prospect

Le post n'est pas un prétexte.

```text
POST CLAIMS
→ issue / thesis extraction
→ retrieve relevant evidence/RETEX/use case
→ classify relationship:
   supports | contradicts | qualifies | dezooms
→ side story
→ message
```

Interdit :

```text
"Excellent post..."
```

si aucun apport substantiel ne suit.

---

## 9. Stale linter

Bloquer si :

- aucun delta ;
- même wedge ;
- même CTA ;
- même preuve ;
- « je me permets de revenir vers vous » sans nouvel apport ;
- source trop ancienne pour justifier why-now ;
- post utilisé sans lien analytique.

---

## 10. Learning

Comparer :

```text
predicted refusal
vs
actual response
```

```yaml
outcome_comparison:
  predicted: internal_build
  actual: not_now
  segment: midmarket_saas
  reusable_signal: true
```

Le dreaming peut proposer une évolution de policy seulement après plusieurs observations.
