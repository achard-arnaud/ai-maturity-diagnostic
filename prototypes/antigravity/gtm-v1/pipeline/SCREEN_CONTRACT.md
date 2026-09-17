# Pipeline — Screen Contract

Per `ANTIGRAVITY_02` excerpt "Pipeline" and `SHELL_CONTRACT.md`.
Authority: NONE — UX exploration only.

## Job

Pipeline répond à *où en sont nos Opportunities et Deals ?* — sans jamais
laisser un clic non gouverné faire naître une Opportunity, et sans inventer
d'étape de board absente du mock (règle mission explicite).

## Objets affichés

`Opportunity`, `Deal`, `Company`, `Demand`, `FitAssessment`, `TargetPlan`
(stakeholders), `Artifact`, `EngagementEvent`/`Touchpoint` (activité/
engagement liés). Mock : `opp_acme_1` (stage `discovery`) et `deal_acme_1`
(stage `proposal`), tous deux liés à `co_acme` / `fit_acme_1` / `tp_acme_1`.

**`Lead` n'est pas un objet canonique** de `SHELL_CONTRACT.md` §4 — voir
DECISION_REQUIRED #1 : l'onglet "Leads" existe (mission oblige) mais reste
volontairement vide plutôt que de mapper arbitrairement un objet existant
(Demand, TargetPlan…) sur ce concept, ce qui serait une décision de modèle
de domaine hors autorité de ce prototype.

## Composants

- `index.html` — **Pipeline Home**, onglets `Leads` / `Opportunities` /
  `Deals` / `Board` (chaque onglet = une page, pattern déjà établi par
  Discover). `index.html` porte l'onglet **Leads** (état vide documenté,
  cf. ci-dessus).
- `opportunities.html` — table des `Opportunity` (compte, stage, owner,
  valeur, prochaine action, dernier engagement) → `opportunity.html`.
- `deals.html` — table des `Deal` (opportunité liée, stage, outcome) →
  `deal.html`.
- `board.html` — **Board Kanban** (`.board`/`.board-column`), une colonne
  par stage **déjà présent dans le mock** (`discovery` pour Opportunities,
  `proposal` pour Deals) — aucune colonne "future stage" inventée. Cartes :
  bloqueur, owner, valeur/priorité, prochaine action, dernier engagement,
  statut de preuve.
- `opportunity.html` — détail Opportunity : compte, Demand/Fit liés,
  stakeholders (TargetPlan), discovery, preuve, décision log, prochaine
  action commerciale, activité/engagement, artefacts, issue win/loss le cas
  échéant.
- `deal.html` — détail Deal : proposal/negotiation/decision présentés
  simplement, sans UI CPQ (le backend n'en a pas).

## États

Voir `states.html` — 8 états appliqués à la table Opportunities.

## Navigation

- Depuis Targets → Buying Committee : un plan actif alimente une
  Opportunity existante (référencée via `target_plan_id`, non créée ici).
- Depuis `opportunities.html`/`board.html` : une carte/ligne →
  `opportunity.html?opportunity_id=…`.
- Depuis `opportunity.html` : lien vers le `deal.html?deal_id=…` associé
  s'il existe.
- **Aucune CTA "+ Nouvelle Opportunity" active** : le mock ne montre que
  des Opportunities déjà existantes ; créer une Opportunity au clic serait
  la simuler comme "créée sur un clic non gouverné", interdit par la
  mission — le bouton est rendu `disabled` avec l'info-bulle nommant le
  vrai portail de création (un Fit `PURSUE` validé + TargetPlan actif).

## Responsive

| Écran | Desktop | Tablet | Mobile |
|---|---|---|---|
| Leads / Opportunities / Deals (tables) | FULL | FULL — colonnes secondaires repliées | READ — une carte par ligne |
| Board | FULL — colonnes côte à côte, scroll horizontal | FULL — scroll horizontal conservé | READ — colonnes empilées verticalement |
| Opportunity / Deal detail | FULL — 2 colonnes (corps + contexte) | FULL — colonnes empilées | READ — colonnes empilées, sections repliables |

## DECISION_REQUIRED

1. `Lead` n'existe pas dans `SHELL_CONTRACT.md` §4 / `shared/mock-data.js`.
   L'onglet "Leads" demandé par la mission reste un état vide documenté
   plutôt qu'un mapping arbitraire vers `Demand` ou `TargetPlan` — c'est une
   décision de modèle de domaine (quel objet réel devient un "Lead" avant
   de devenir une Opportunity ?) à trancher par l'équipe produit/architecture.
2. Le Board n'a qu'une colonne par objet (une pour Opportunities au stage
   `discovery`, une pour Deals au stage `proposal`) car le mock ne fournit
   pas de liste ordonnée complète des stages possibles. Un vrai Kanban
   multi-colonnes nécessite cette liste de stages canonique, non définie
   ici.
3. `opportunity.html` affiche des champs "discovery notes" / "decision log"
   qui n'existent pas sur `opp_acme_1` dans `shared/mock-data.js` — ajoutés
   localement comme overlay d'affichage UI-only (même `opportunity_id`),
   pas un nouvel objet canonique. Le vrai schéma de ces champs est une
   décision domaine.
4. Le bouton "+ Nouvelle Opportunity" est désactivé partout dans cet écran
   avec une info-bulle nommant le gate réel (Fit `PURSUE` + TargetPlan
   actif) — jamais un clic créant une Opportunity de façon non gouvernée
   (règle mission dure, cf. `SHELL_CONTRACT.md` §5).
