# Fit — Screen Contract

Per `ANTIGRAVITY_01_DISCOVER_RESEARCH_FIT_V1.md` §3 (Fit) and
`SHELL_CONTRACT.md`. Authority: NONE — UX exploration only, taking over the
Antigravity mission after Antigravity itself did not deliver it.

## Job

Répond à *Cette Demand mérite-t-elle une proposition, et pourquoi ?* — une
évaluation qualitative et traçable, jamais un score qui remplace le
jugement. Fit ne redéfinit ni la Demand ni le ProductSnapshot qu'il évalue
— il les cite, exactement, par id/version. Un score peut exister comme
résumé mais ne doit **jamais** dominer l'explication (mission) : partout
où `need_coverage` apparaît, il est rendu en petit badge secondaire, jamais
en titre ni en grand chiffre.

## Objets affichés

`Company`, `Demand`, `Product`, `ProductSnapshot`, `FitAssessment`,
`Evidence` — mock : `shared/mock-data.js` + `research/research-mock-extend.js`
(Company/Demand/Evidence/ResearchCase, chargé pour que Research et Fit
partagent une seule source) + `fit/fit-mock-extend.js` (extension locale
additive propre à Fit : champs `reviewer`, `decision_history`, `blockers`,
`hard_gates`, `icp_fit`, `timing`, `integration_fit`,
`commercial_unknowns`, `next_best_action` sur `FitAssessment`, et
`status`/`changelog` sur `ProductSnapshot`, plus des instances
supplémentaires de ces mêmes formes — voir l'en-tête de ce fichier pour
pourquoi l'extension vit ici et non dans `shared/mock-data.js`).

## Composants

- `index.html` — Fit Home/Queue : assessments en attente (`pending_review`),
  bloquées par hard gate (`blocked`), périmées par changement de Demand/
  ProductSnapshot (`stale`), en attente de revue humaine
  (`needs_human_review`), approuvées/déclinées (`approved`/`declined`).
  Filtres par Company / Product / décision / fraîcheur (implémentés côté
  client sur les mêmes `<select>`, pas de recalcul serveur simulé).
- `detail.html?fit_id=…` — Fit Detail :
  - **Header** : Company, Demand, Product, ProductSnapshot exacte
    (id + version, badge `.version-badge`), version/statut de l'assessment.
  - **Body** : Overall decision, Need coverage (badge secondaire — jamais
    un gros chiffre), ICP fit, Timing, Integration fit, Commercial
    unknowns, puis MATCHES / GAPS / CONTRADICTIONS / UNKNOWNS /
    ALTERNATIVES / EVIDENCE / HARD GATES.
  - **Right rail** : blockers + CTA resolver, reviewer, historique de
    décision, prochaine meilleure action.
- `products.html` — Product Library (vue secondaire) : Products → Versions
  → Snapshots → Evidence/changelog, diff entre deux snapshots consécutives,
  état publié/immuable toujours visible.
- `states.html` — galerie des 8 états appliqués à la Fit Queue.

## États

Voir `states.html`. `blocked` illustre une assessment arrêtée par un hard
gate non levé (CTA "Résoudre" pointant vers l'action réelle — jamais un
contournement du gate). `stale` illustre une assessment dont la
ProductSnapshot ou la Demand a changé depuis son calcul.

## Navigation

- Depuis Research (onglet Fits, ou Research Home "revue humaine") →
  `detail.html?fit_id=…`, lien direct, jamais une re-création implicite.
- Depuis la Fit Queue → `detail.html?fit_id=…` par ligne/carte.
- Depuis Fit Detail → `products.html?product_id=…&snapshot_id=…` pour
  vérifier la ProductSnapshot exacte citée dans le header.
- Fit Detail n'expose **aucun** lien "Créer un Target" tant que
  `overall_decision` n'est pas une approbation humaine effective
  (`reviewer` renseigné) — per SHELL_CONTRACT.md §5, un Target ne se
  simule jamais avant un Fit valide.

## Responsive

| Écran | Desktop | Tablet | Mobile |
|---|---|---|---|
| Fit Queue | FULL — table avec tous les filtres visibles | FULL — filtres empilés au-dessus de la table | READ — carte par assessment au lieu de table |
| Fit Detail | FULL — 2 colonnes (corps + right rail) | FULL — right rail passe sous le corps | READ — sections repliables, right rail en bas de page |
| Product Library | FULL — 4 colonnes (Products/Versions/Snapshots/Evidence) | FULL — 2 colonnes, Evidence en dessous | READ — liste verticale, une entité à la fois |

## DECISION_REQUIRED

1. Aucune formule n'est définie pour `need_coverage` (le "score résumé") —
   ce prototype le traite comme une chaîne mockée statique par assessment,
   jamais recalculée en live ; le calcul réel, sa fraîcheur et son statut
   epistemic (fait/inférence) restent à définir par l'architecture owner.
2. La distinction entre "hard gate" (bloquant, non contournable ici) et
   "commercial unknown" (n'empêche pas la décision mais doit être visible)
   est un classement de ce prototype, pas une taxonomie validée — quelles
   conditions sont de vrais hard gates au sens produit/légal reste à
   trancher par l'architecture owner.
3. Le passage `stale` → réévaluation n'est pas déclenché automatiquement
   ici (le CTA "Relancer l'évaluation" est un lien vers l'assessment
   courante, pas une régénération simulée) — le vrai déclencheur (cron,
   webhook sur nouvelle ProductSnapshot, action manuelle) n'est pas décidé.
4. Fit Detail n'affiche aucun CTA de création de Target — la mission
   interdit de simuler un Target avant un Fit valide, mais ce prototype ne
   tranche pas non plus à quel moment exact (quel statut d'assessment,
   quelle validation) une telle action deviendrait disponible ; c'est un
   DECISION_REQUIRED pour l'espace Targets, pas pour Fit.
5. Product Library : un seul `Product` existe dans le mock partagé
   (`prod_platform`) — la vue montre donc Products → Versions → Snapshots
   → Evidence sur un seul produit avec 3 snapshots. Le comportement à
   plusieurs produits (regroupement, comparaison croisée) n'est pas
   exploré ici faute de second `Product` dans le mock partagé, que ce
   prototype ne peut pas ajouter (isolation : `shared/mock-data.js` n'est
   pas modifiable depuis cette livraison).
