# Discover — Screen Contract

Per `ANTIGRAVITY_01_DISCOVER_RESEARCH_FIT_V1.md` §1 and `SHELL_CONTRACT.md`.
Authority: NONE — UX exploration only.

## Job

Répond à quatre jobs : *Who do I know?* (réseau), *Who matches?* (comptes
correspondant à des critères), *What changed?* (signaux récents), *Why
now?* (contexte de priorisation). Discover ne calcule et n'affiche **aucun**
score de Fit/demande — c'est une frontière volontaire avec l'espace Fit.

## Objets affichés

`Company`, `Person`, `Signal` (mock : `shared/mock-data.js` — comptes
`co_acme`/`co_nautix`/`co_verdal`, signaux liés). Aucun objet Demand ou Fit
n'apparaît dans Discover, conformément à la règle "aucun Fit/demand score
direct dans Discover" de la mission.

## Composants

- `index.html` — Discover Home : comptes prioritaires (research non
  complète) sous forme de cards avec badge fraîcheur, + recherches
  sauvegardées/watchlists.
- `people.html` — table personnes avec statut de rôle vérifié/non vérifié
  visuellement distinct (jamais promu en autorité par défaut).
- `companies.html` — table comptes avec filtre secteur/statut recherche ;
  aucun score Fit/demand n'apparaît sur cette vue (frontière explicite).
- `signals.html` — table signaux avec statut, fraîcheur, source cliquable
  et CTA `queue research` par ligne.
- `lists.html` — cards People list / Company list / Smart list, règle de
  membership d'une Smart List toujours affichée en clair.
- Chaque vue utilise le vocabulaire épistémique partagé
  (`.badge.epi-*`, `.freshness-*`, `.source-badge`).

## États

Voir `states.html` — galerie interactive des 8 états
(`default/loading/empty/error/blocked/stale/partial-data/success`)
appliqués à la grille de comptes prioritaires. `blocked` illustre un compte
dont la research est bloquée (CTA "Résoudre" vers Research, pas résolu ici).

## Navigation

- Depuis Home : card "priority prospects" → Discover.
- Depuis Discover : card compte → `research/index.html?company_id=…`
  (Company 360, cf. contrat Research) ; CTA "queue research" sur un signal
  → transition d'état du Signal (simulée, pas persistée) plutôt qu'une
  création de ResearchCase implicite.
- Handoff explicitement **non simulé comme vérité** : un signal ne devient
  jamais un Demand automatiquement au clic (règle mission §"interaction
  rules").

## Responsive

| Écran | Desktop | Tablet | Mobile |
|---|---|---|---|
| Discover Home | FULL — grille de cards + sidebar recherches sauvegardées | FULL — grille recolonnée à 2 | READ — liste 1 colonne, recherche globale masquée (icône seule) |
| People/Companies (tables) | FULL | READ — colonnes secondaires masquées | READ — carte au lieu de table |
| Signals | FULL | FULL | READ |

Aucun graphe/board complexe dans Discover — pas de contrainte mobile forte
au-delà du recolonnage standard.

## DECISION_REQUIRED

1. Quel champ distingue "candidate account" (mission doc) de "target
   account" affiché ailleurs (Discover vs Company 360 vs Targets) —
   Antigravity/Claude ne tranche pas cette taxonomie, c'est une question
   de modèle de domaine pour l'architecture owner.
2. La CTA "queue research" doit-elle exister à la fois sur un Signal
   individuel ET en bulk-select sur la table Signals ? Le mock ne montre
   que le cas individuel.
3. `lists.html` ne montre que 3 cards statiques — la V1 de la mission ne
   précise pas si Smart List est éditable en V1 ou lecture seule ; ici
   traité comme lecture seule (pas de builder de règles).
