# Research — Screen Contract

Per `ANTIGRAVITY_01_DISCOVER_RESEARCH_FIT_V1.md` §2 (Research) and
`SHELL_CONTRACT.md`. Authority: NONE — UX exploration only, taking over the
Antigravity mission after Antigravity itself did not deliver it.

## Job

Répond à deux jobs : *Où concentrer l'effort de recherche maintenant ?*
(Research Home — une queue de travail, pas un simple listing) et *Que
sait-on vraiment de ce compte, et avec quel degré de certitude ?*
(Company 360 — vue exhaustive par compte, organisée en onglets). Research
ne calcule et n'affiche **aucune** décision de Fit — la synthèse Fit
n'apparaît qu'en lecture seule dans l'onglet Fits, jamais recalculée ici.

## Objets affichés

`Company`, `ResearchCase`, `Evidence`, `Signal`, `Person`, `Demand`,
`FitAssessment` (lecture seule, onglet Fits), `Artifact` — mock :
`shared/mock-data.js` + `research/research-mock-extend.js` (extension
locale additive : `Evidence.section`, `ResearchCase.history`, et des
instances supplémentaires de `Demand`/`ResearchCase` pour Nautix et
Verdal — voir l'en-tête de ce fichier pour pourquoi l'extension vit ici et
non dans `shared/mock-data.js`).

## Composants

- `index.html` — Research Home : queue de travail (assigné / bloqué /
  périmé), priorité compte, couverture/complétude, dernier run, CTA
  Reprendre / Ouvrir / Revoir par ligne.
- `company.html?company_id=…` — Company 360, 9 onglets : **Overview,
  Research, Signals, People, Demands, Fits, Engagement, Activity,
  Artifacts**. Navigation par onglets côté client (pas de rechargement de
  page), état de l'onglet actif reflété dans `?tab=…` pour rester
  partageable.
  - Onglet **Research** : 14 sections (Identity, Business model, Products &
    services, Customers/markets, Organisation, Strategic priorities,
    Technology, AI/transformation, Recent events, Hiring, Competitive
    environment, Risks, Sources, Research history). Les 12 premières
    distinguent visuellement observation/inférence/hypothèse/inconnu via
    les badges partagés `.epi-fact/.epi-inference/.epi-hypothesis/
    .epi-unknown` ; une section sans evidence associée affiche un état
    "inconnu" explicite plutôt qu'une absence silencieuse. Sources liste
    les provenances (dédupliquées depuis `Evidence.source`) ; Research
    history rejoue `ResearchCase.history`.
  - Onglet **Demands** : une card par `Demand` du compte — problème /
    outcome, nombre de preuves (`evidence_ids.length`), mix de sources,
    confiance, statut, urgence, inconnus, contradictions, Fits liés.
- `states.html` — galerie des 8 états appliqués à la queue Research Home.

## États

Voir `states.html`. `blocked` illustre une research bloquée en attente de
validation humaine (CTA "Résoudre" vers l'action réelle, non résolue ici) ;
`stale` illustre une couverture jugée périmée après un signal récent non
encore intégré ; `partial-data` illustre une source indisponible pendant le
run (ex. LinkedIn).

## Navigation

- Depuis Discover : card compte / lien table → `company.html?company_id=…`.
- Depuis Research Home : ligne de queue → `company.html?company_id=…`
  (CTA Reprendre/Ouvrir positionne l'onglet Research actif ; CTA Revoir
  positionne l'onglet Fits actif quand une assessment attend une revue
  humaine).
- Depuis l'onglet Fits d'un compte → `../fit/detail.html?fit_id=…` (lecture
  seule côté Research ; toute action de décision se passe dans l'espace
  Fit, jamais ici).
- Onglet Demands → carte Demand affiche les Fits liés en lien vers
  `../fit/detail.html?fit_id=…`, jamais une création de Fit implicite.

## Responsive

| Écran | Desktop | Tablet | Mobile |
|---|---|---|---|
| Research Home (queue) | FULL — table complète avec toutes colonnes | READ — colonnes secondaires (dernier run, propriétaire) masquées | READ — carte par compte au lieu de table |
| Company 360 — barre d'onglets | FULL — 9 onglets en ligne | FULL — onglets scrollables horizontalement | READ — sélecteur d'onglet en menu déroulant |
| Company 360 — onglet Research (14 sections) | FULL — 2 colonnes | FULL — 1 colonne | READ — 1 colonne, sections repliables |
| Company 360 — onglet Demands (cards) | FULL — grille de cards | FULL — grille recolonnée à 2 | READ — liste 1 colonne |

## DECISION_REQUIRED

1. La progression `Detected → Inferred → Validated → Qualified` affichée
   sur `Demand.status` est une spéculation UI de ce prototype, pas un
   cycle de vie métier validé — Antigravity/Claude ne tranche pas ce
   modèle d'état, c'est une décision pour l'architecture owner (transitions
   autorisées, qui les déclenche, réversibilité).
2. Aucune méthode de calcul n'est définie pour la "priorité" de compte ni
   pour le "% de couverture/complétude" affichés en Research Home — ce
   prototype les traite comme des chaînes mockées statiques, pas un score
   réel ; la vraie formule (et son statut de fait/inférence) reste à
   définir par l'architecture owner.
3. Frontière de propriété entre Research et Fit sur l'onglet Fits du
   Company 360 : ce prototype le traite en lecture seule pure (aucune
   action de décision Fit n'y est exposée), mais la mission ne précise pas
   si un raccourci d'action devrait exister ici en V1.
4. Navigation par onglets en `?tab=…` côté client (pas de route par
   onglet) : choix de prototype pour rester dans un seul fichier HTML
   statique ; l'architecture réelle pourrait vouloir des routes profondes
   par onglet (ex. `/companies/co_acme/demands`), non tranché ici.
5. Sur l'onglet Demands, une `Demand` sans `FitAssessment` lié affiche un
   CTA "Lancer une évaluation Fit" volontairement `disabled` (tooltip :
   "nécessite une ProductSnapshot publiée, se crée dans l'espace Fit") —
   per SHELL_CONTRACT.md §5, ce prototype ne simule jamais un Fit sans
   ProductSnapshot. Le vrai parcours de déclenchement d'une Fit Assessment
   depuis Research (qui la déclenche, sur quel critère) reste à définir
   par l'architecture owner.
