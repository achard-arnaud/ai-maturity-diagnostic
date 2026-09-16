# 05 — Prospection : Objection Simulation, Wedge et Gatekeeper

## 1. But

Améliorer qualification du lead, pied dans la porte, anticipation des objections, routing via gatekeeper et taux de réponse utile.

Le mécanisme fonctionnel s'appelle `ObjectionSimulation`, pas `System Red-Team`.

---

## 2. Prospect Simulation

Perspectives disponibles :

```text
economic_buyer
technical_buyer
user
security_it
manager
executive
gatekeeper
```

Chaque perspective produit des **issues hypothétiques**.

```yaml
objection_simulation:
  simulation_id: OS-...
  wedge_id: WDG-...
  perspective: technical_buyer
  objections:
    - issue_id: ISS-OBJ-021
      statement: "Why not build internally?"
      evidence_status: hypothesis
      probability: unknown
      materiality: high
```

Ne pas inventer une probabilité chiffrée sans calibration.

---

## 3. Objection graph

```text
WEDGE
├── relevance
├── timing
├── trust
├── build_vs_buy
├── switching_cost
├── authority
├── budget
├── implementation_burden
└── attention
```

Le moteur choisit l'objection **la plus décisionnelle**, pas toutes.

---

## 4. Wedge pressure test

```text
INITIAL WEDGE
→ simulate strongest refusal
→ {
   survives,
   narrow,
   replace angle,
   wait
}
→ final wedge
```

Maximum :

- 3 wedges candidats ;
- 1 objection dominante par wedge ;
- 1 sélection finale.

---

## 5. Anti-pattern

Interdit :

```text
"Nous savons que vous avez probablement..."
```

si la donnée est une objection simulée.

Préférer :

```text
"Je cherche précisément à comprendre si..."
```

---

## 6. Gatekeeper

La fonction n'est pas de « contourner la secrétaire ».

La fonction est :

> rendre la demande légitime, compréhensible et routable.

Gatekeeper simulation :

```text
Pourquoi ne transmettrais-je pas ?
```

Issues types :

- unclear routing ;
- generic sales ;
- excessive time ask ;
- no visible relevance ;
- no named business topic ;
- wrong contact ;
- no credibility basis.

---

## 7. Gatekeeper response policy

Actions :

```text
ASK_ROUTE
ASK_OWNER
SEND_TWO_LINE_CONTEXT
WAIT
```

Exemple :

> Je ne sais pas si ce sujet relève directement de Mme X ou plutôt de votre responsable plateforme IA. Il concerne [sujet concret]. Si vous m'indiquez la bonne personne, je lui envoie les deux éléments précis que nous avons identifiés.

Préserver transparence, absence de faux prétexte, absence de fausse relation et absence d'urgence inventée.

---

## 8. Message compiler

Input :

```text
validated wedge
+
0..1 promoted side story
+
primary CTA
+
channel constraints
```

Output : `message draft`.

Le compiler ne décide pas du fit.

---

## 9. Outreach linter

Checks déterministes :

```text
current role valid?
fit ready?
FAIL gate?
evidence citation/path available?
message repeats previous message?
new delta exists?
CTA effort bounded?
unsupported pain asserted?
title used as authority?
newsflow used as fit?
```

Checks sémantiques :

```text
seller-centric?
generic personalization?
weak why-now?
objection ignored?
too many arguments?
gatekeeper routing unclear?
```

---

## 10. Example code

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class MessagePlan:
    wedge_id: str
    side_story_id: str | None
    cta_kind: str
    new_delta_ids: tuple[str, ...]

def validate_message_plan(plan: MessagePlan) -> list[str]:
    errors = []
    if not plan.new_delta_ids:
        errors.append("OUTREACH_NO_NEW_DELTA")
    if plan.cta_kind not in {
        "validate_question", "route_request", "short_call", "send_material"
    }:
        errors.append("OUTREACH_UNBOUNDED_CTA")
    return errors
```

---

## 11. Outcome capture

Capturer :

```text
no_response
positive_response
negative_response
routed
wrong_person
not_now
already_solved
internal_build
budget
security
other
```

L'`other` garde le verbatim autorisé et devient un Issue candidat. Ces outcomes nourrissent la calibration future.
