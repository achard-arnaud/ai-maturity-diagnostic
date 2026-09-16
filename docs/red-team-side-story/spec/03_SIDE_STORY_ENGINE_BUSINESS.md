# 03 — Side Story Engine : storytelling business et orchestration commerciale

## 1. Principe

Une `SideStory` conserve une idée utile **hors du tronc principal**, avec purpose, payoff, lineage, placement, return path et lifecycle.

Elle est un artefact de composition.

> Elle ne crée jamais une preuve.

---

## 2. Kinds recommandés

### `dezoom`
Change d'échelle : d'un use case entreprise vers un pattern sectoriel.

### `method`
Explique une méthode ou une limite.

### `false_lead`
Montre une piste séduisante mais rejetée.

Exemple : « On aurait pu penser que le problème était la vitesse ; le vrai blocker était la gouvernance. »

### `comparator`
Met en regard deux mécanismes.

### `analytical_focus`
Développe une question difficile qui mérite plus qu'une phrase mais pas une nouvelle note.

### `callback`
Réactive un élément antérieur : discussion, objection, use case, post, RETEX.

### Extensions métier
Ne les ajouter au schéma qu'après validation. En V1, garder les six kinds et porter la sémantique business dans `purpose` + `issue_refs`.

---

## 3. Contrat V1 adapté

```yaml
side_story:
  id: SS-...
  kind: comparator
  status: candidate
  purpose: "Tester internal build vs repeated orchestration burden"
  payoff: "Créer une question de discovery non vendeuse"
  lineage:
    claim_ids: [C-...]
    source_ids: [SRC-...]
    issue_ids: [ISS-...]
    outcome_ids: []
  placement:
    artifact: 07_engagement_hypothesis.md
    section_anchor: discovery_angle
    return_to: primary_cta
  evidence_status: hypothesis
  content:
    takeaway: "Le sujet à tester est la répétition du coût, pas le choix build/buy."
    body_markdown: ""
  render:
    eligible: true
```

---

## 4. Lifecycle

```text
candidate
→ validated
→ promoted
→ retired
```

- **Candidate** : angle détecté mais non prêt.
- **Validated** : lineage et utilité confirmées.
- **Promoted** : autorisé dans un output/action donné.
- **Retired** : ne doit plus être proposé.

---

## 5. Promotion rules

Une side story peut être promue si :

- payoff explicite ;
- delta réel ;
- evidence status honnête ;
- aucun besoin inventé ;
- pas de duplication du trunk ;
- `return_to` clair.

Rejeter si :

- personnalisation = seulement nom du prospect ;
- hypothèse transformée en fait ;
- détour sans payoff ;
- volume sans décision ;
- répétition d'une relance précédente.

---

## 6. Dans les artefacts de fit

```text
TRUNK:
Produit X ↔ besoin Y ↔ personne Z

SIDE STORY / false_lead:
"Le titre de Z ressemble à un sponsor, mais aucune preuve d'autorité."

SIDE STORY / dezoom:
"Dans plusieurs entreprises du secteur, la douleur apparaît à la mise en production, pas au PoC."

SIDE STORY / comparator:
"Internal build vs external platform : le point à tester est le coût récurrent."
```

---

## 7. Dans la prospection

Le message final ne contient pas toutes les side stories.

Budget :

```text
1 trunk
+
0..1 primary side story
+
1 CTA
```

---

## 8. Gatekeeper

Objectif : rendre l'intention routable.

Side story utile : `method`.

> « Je ne sais pas si cela relève de X ou de la plateforme IA ; voici en une phrase le sujet. »

Interdit : fausse relation, faux contexte, fausse urgence.

---

## 9. Réactivation

Le `callback` devient central.

```text
previous_issue
+
new_delta
→ callback
```

Exemple :

> Lors de notre dernier échange, le point ouvert était la supervision. Depuis, nous avons clôturé un cas comparable où le vrai problème s'est déplacé vers X.

Le callback est légitime si la conversation précédente existe, le RETEX est sourcé et le lien au prospect reste hypothétique s'il n'est pas démontré.

---

## 10. Materialization

```python
def materialize_side_story(story):
    assert story["status"] == "promoted"
    assert story["lineage"]["issue_ids"] or story["lineage"]["claim_ids"]
    assert story["content"]["takeaway"].strip()
    return {
        "label": story["kind"],
        "takeaway": story["content"]["takeaway"],
        "return_to": story["placement"]["return_to"],
    }
```

Le renderer/générateur peut simplifier le wording mais ne change jamais evidence status, caveat matériel ou arguments.
