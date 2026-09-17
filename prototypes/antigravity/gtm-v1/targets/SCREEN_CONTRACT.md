# Targets — Screen Contract

Per `ANTIGRAVITY_02` excerpt "Targets" and `SHELL_CONTRACT.md`.
Authority: NONE — UX exploration only.

## Job

Distingue deux notions que la mission tient volontairement séparées :
`Contacts` = personnes connues (cf. Discover/Research), `Targets` = personnes
sélectionnées pour une action commerciale au sein d'un `TargetPlan`,
uniquement après un `Fit` valide. Targets répond à : quels comptes ont un
plan de ciblage activable ? qu'est-ce qui bloque sa validation ? qui est le
comité d'achat (buying committee) et quelle est sa couverture par rôle ?

## Objets affichés

`Company`, `TargetPlan` (membres = `Person` + rôle de stakeholder),
`FitAssessment` (contexte de rattachement, jamais recalculé ici),
`Evidence` (justification d'un rôle/priorité). Mock : `tp_acme_1` (3
membres) rattaché à `fit_acme_1` / `co_acme`. `co_nautix` et
`co_verdal` n'ont **pas** de `TargetPlan` car ils n'ont pas de `Fit` dans
`shared/mock-data.js` — c'est l'illustration du principe "un Target n'existe
qu'après un Fit valide", pas une donnée manquante par oubli.

## Composants

- `index.html` — **Targets Home** : un plan de ciblage par compte (carte),
  avec bloqueurs de validation, chemin d'accès "warm" identifié, avertissement
  de fraîcheur, résumé de couverture des rôles (rôles couverts / manquants),
  CTA "Ouvrir le comité d'achat". Comptes sans Fit valide affichent une carte
  "bloquée" explicite avec CTA désactivée.
- `committee.html` — **Buying Committee** : vue table (par défaut) + bascule
  vue graphe simplifiée (regroupement visuel par rôle). Colonnes : Personne,
  **Titre** (fait, texte simple, jamais un badge) vs **Rôle de stakeholder**
  (jugement humain, badge `👤 human-decision-badge`) — **jamais fusionnés au
  même endroit visuel** ; Influence ; Confiance d'autorité ; Chemin de
  relation ; Reachability ; Priorité ; Preuve (lien vers l'Evidence source) ;
  Fraîcheur.
- Rôles couverts par le vocabulaire mission : economic buyer, champion,
  user, technical sponsor, prescriber, procurement, blocker/veto.

## États

Voir `states.html` — galerie des 8 états
(`default/loading/empty/error/blocked/stale/partial-data/success`) appliqués
à la grille Targets Home. `blocked` illustre un plan dont la validation
humaine du rôle "economic buyer" est en attente.

## Navigation

- Depuis Fit (hors périmètre de cet écran) : un Fit `PURSUE` validé peut
  faire naître un `TargetPlan` — non simulé ici, seulement référencé via
  `fit_id` (voir DECISION_REQUIRED #1 : qui déclenche cette création).
- Depuis Targets Home : carte compte → `committee.html?target_plan_id=…`.
- Depuis Buying Committee : CTA "Envoyer vers Reach" (si le plan n'est pas
  bloqué) → `../reach/index.html?target_plan_id=…`. Un bloqueur non résolu
  ne se résout pas dans Targets (résolution = validation humaine, hors
  périmètre de cet écran).
- Aucune CTA "ajouter un target" hors du flux Fit → TargetPlan : on ne crée
  jamais un Target sans Fit valide (règle mission, cf. `SHELL_CONTRACT.md`
  §5).

## Responsive

| Écran | Desktop | Tablet | Mobile |
|---|---|---|---|
| Targets Home | FULL — grille de cartes par compte | FULL — grille recolonnée à 2 | READ — liste 1 colonne, résumé de couverture réduit à un badge compact |
| Buying Committee (table) | FULL — toutes colonnes | FULL — colonnes Preuve/Fraîcheur repliées dans une info-bulle | READ — une carte par personne au lieu d'une ligne de table |
| Buying Committee (graphe) | FULL | READ — colonnes de rôle empilées verticalement | READ — liste simple, bascule graphe masquée (pas de canvas complexe en mobile) |

## DECISION_REQUIRED

1. Qui/quoi déclenche la création d'un `TargetPlan` à partir d'un Fit
   `PURSUE` — automatique après validation humaine du Fit, ou action
   manuelle explicite "Promouvoir en Target" ? C'est une décision de state
   machine du domaine, hors autorité de ce prototype.
2. La vue "graphe" du comité d'achat est ici une mise en page simplifiée
   (cartes regroupées par rôle, pas de canvas/zoom/pan) ; un vrai rendu de
   graphe relationnel (multi-degrés, edges pondérés par influence) reste à
   spécifier par l'équipe produit/design.
3. Les champs `reachability` et `priority` par membre n'existent pas dans
   `shared/mock-data.js` — affichés ici via un overlay local déclaré dans
   `committee.html` (mêmes `person_id`, même forme d'objet `TargetPlan`
   member, pas de nouvel objet canonique). Le calcul réel de `reachability`
   (degré de relation × canal disponible × consentement) est une décision
   produit non tranchée ici.
4. Le "warm path" affiché sur Targets Home (ex. "M. Ferréol → intro vers C.
   Dubosc") est un texte statique illustratif, pas un algorithme de chemin
   de relation réel — la vraie logique de calcul de chemin appartient au
   domaine Research/réseau, pas à Targets.
