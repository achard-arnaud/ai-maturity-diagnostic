# Insights — Screen Contract

Per `ANTIGRAVITY_03` excerpt "Insights" and `SHELL_CONTRACT.md`.
Authority: NONE — UX exploration only.

## Job

Répondre à "comment le moteur GTM performe" à un niveau métrique/
projection — jamais "quelle est la vérité sur ce compte/ce Fit" (ça, c'est
Discover/Research/Fit/Targets/Pipeline). Aligné conceptuellement avec le
vrai Epic 13 (déjà livré) : funnel, qualité/coût de projection, revue des
`LearningProposal`. Insights ne mute jamais la vérité métier — c'est une
frontière testée dans le produit réel
(`test_gtm_downstream_spaces.py::test_insights_boundary_and_admin_link_are_explicit`)
que ce mockup respecte visuellement.

**Distinction volontaire, cf. `OPERATIONS_OBSERVABILITY_GAP.md` §5** :
Insights = métriques business (funnel, qualité, coût projeté, engagement)
calculées sur des `BusinessEvent`s, à destination des décideurs produit/
GTM. L'observabilité opérationnelle (santé système, erreurs, run traces,
budget réel) est un **espace différent** (candidate Epic E20, pas encore
construit) — ce mockup ne les confond pas : la tuile "Coût / rate-limit"
ci-dessous est explicitement labellisée comme une **projection de coût
métier** (issue de `insights_metrics.py`), pas un dashboard d'ops (qui
n'existe pas encore côté produit réel).

## Objets affichés

Projections en lecture seule sur `Signal`, `FitAssessment`, `Sequence`/
`Touchpoint`, `EngagementEvent`, `Opportunity`, `Artifact` (agrégées, pas
listées ligne à ligne — Insights n'est pas une table brute) + `LearningProposal`
en tant qu'objet propre avec un vrai flux de revue (seul objet d'Insights
avec une action, pas juste une métrique).

## Composants

- `index.html` — tableau de bord à 8 sections (une par sujet de la
  mission) : Funnel, Fit quality/performance, Outreach activity,
  Engagement, Sources, Product performance, Cost/rate-limit usage,
  Learning proposals (résumé + lien vers la revue dédiée). Chaque tuile
  métrique porte un badge `.epi-inference` (dérivée de faits, jamais un
  fait en soi) — jamais fondue visuellement avec une tuile "vérité métier"
  (qui, elle-même, resterait `.epi-fact`/`.human-decision-badge` si jamais
  affichée ici).
- `learning-proposals.html` — file de revue dédiée des `LearningProposal`
  (seul sous-écran avec une action réelle : transition de statut, pas une
  simple lecture de métrique).
- Bandeau permanent en haut de `index.html` rappelant la frontière
  "projection, pas vérité" (texte, pas seulement une couleur).

## États

Voir `states.html` — 8 états appliqués au tableau de bord. `partial-data`
illustre une source de métrique indisponible (ex. coût) pendant que les
autres tuiles restent à jour — cohérent avec le fait que chaque tuile est
une agrégation indépendante, pas une requête unique.

## Navigation

- Tuile Funnel/Fit quality/Outreach/Engagement/Sources/Product → pas de
  lien de drill-down vers un objet individuel (ce sont des agrégats,
  conformément à "jamais dupliquer les données sous-jacentes" — un
  agrégat n'a pas d'équivalent 1:1 à ouvrir) sauf mention explicite.
- Tuile "Learning proposals" → `learning-proposals.html`.
- Bandeau "voir aussi Admin" (lien secondaire, texte seul) vers
  `../admin/index.html` pour toute question d'observabilité opérationnelle
  — jamais une fusion des deux dans la même vue, cf. §5 de
  `OPERATIONS_OBSERVABILITY_GAP.md`.

## Responsive

| Écran | Desktop | Tablet | Mobile |
|---|---|---|---|
| Dashboard (8 sections) | FULL — grille de tuiles 3-4 colonnes par section | FULL — grille recolonnée à 2 | READ — 1 colonne, sections repliables ; le bandeau "projection ≠ vérité" reste toujours visible, jamais replié |
| Learning proposals | FULL — table + détail | FULL | READ — cartes empilées, action de transition conservée (pas juste lecture) |

## DECISION_REQUIRED

1. `mock-data.js` ne fournit aucun objet d'agrégat prêt à l'emploi pour
   les 8 sections (funnel, coût, etc.) — les tuiles ci-dessous sont donc
   des nombres illustratifs calculés côté client à partir des objets
   existants (ex. compter les signaux/Fits/touchpoints mock), pas des
   métriques réelles. À remplacer par de vraies projections issues de
   `insights_metrics.py`/`insights_projection.py` lorsque l'intégration
   sera décidée — aucune nouvelle forme d'objet canonique n'est inventée
   ici, seulement des agrégats d'affichage.
2. La mission ne précise pas si `LearningProposal` doit avoir sa propre
   nav-id ou rester un sous-écran d'Insights — traité ici comme sous-écran
   (pas de 11e item de nav), cohérent avec le produit réel où
   `learning-proposals` est une route sous `insights`, pas un espace à
   part.
3. Le seuil de suppression de confidentialité (`MINIMUM_COHORT_SIZE = 3`
   dans le produit réel) n'est pas simulé visuellement ici faute de volume
   de données mock suffisant — à traiter comme un état `partial-data`
   explicite dans une itération future plutôt qu'un silence.
4. `LearningProposal` n'apparaît **pas** dans la liste d'objets canoniques
   de `SHELL_CONTRACT.md` §4, alors que la mission demande explicitement
   sa revue dans Insights. Ce prototype ne l'ajoute donc pas à
   `shared/mock-data.js` (qui resterait alors incohérent avec le contrat
   qu'il cite) — `learning-proposals.html` définit un petit jeu d'exemples
   illustratifs en local à la page (même pattern que `savedSearches` dans
   `discover/index.html`), en attendant une décision de l'architecture
   owner sur l'ajout formel de `LearningProposal` à la liste canonique
   partagée.
