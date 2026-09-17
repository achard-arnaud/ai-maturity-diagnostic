# Home / My Day — Screen Contract

Per `ANTIGRAVITY_03` excerpt "Home/My Day" and `SHELL_CONTRACT.md`.
Authority: NONE — UX exploration only.

## Job

Réduire le coût de navigation quotidien : répondre à "qu'est-ce qui a besoin
de moi maintenant, et où est-ce que je clique pour agir". Home n'est pas un
dashboard décoratif — chaque carte est une porte d'entrée vers le vrai
contexte de travail (Research/Fit/Reach/Engagement/Pipeline/Discover),
jamais une duplication des données sous-jacentes. Aucune donnée n'est
recalculée ni stockée ici ; tout est lu depuis `shared/mock-data.js` et
projeté en résumé court + lien.

## Objets affichés

Projection en lecture seule sur `Signal`, `ResearchCase`/`Evidence`,
`FitAssessment`, `TargetPlan`/`Touchpoint`, `EngagementEvent`,
`Opportunity` (tous depuis `shared/mock-data.js`, compte démo Acme +
secondaires). Home n'est le système de vérité d'aucun de ces objets — comme
le confirme `USE_CASE_PLATFORM_GAP_MATRIX.md` pour l'espace Home réel
(projection pure sur `/api/follow-up`, sans stockage propre).

## Composants

- `index.html` — My Day : file de travail agrégée (queue prioritaire toutes
  sources confondues), puis sections dédiées : Priority prospects/accounts,
  Signals requiring review, Research blockers, Fit reviews, Reach tasks,
  Follow-ups, Recent engagement, Opportunities at risk, Next best actions.
- Chaque carte affiche : titre, 1 ligne de contexte, badge épistémique/
  fraîcheur si pertinent, et un unique CTA de navigation vers l'écran
  propriétaire de la donnée. Aucune carte n'expose de champ éditable.
- Vocabulaire épistémique partagé (`.epi-*`, `.freshness-*`,
  `.blocker-badge`) réutilisé tel quel — Home ne définit pas de nouveau
  badge.

## États

Voir `states.html` — galerie des 8 états
(`default/loading/empty/error/blocked/stale/partial-data/success`)
appliqués à la queue My Day. `empty` = aucune tâche prioritaire (jour
"calme") ; `blocked` = agrégation elle-même bloquée (une source amont — ex.
Research — indisponible) ; `partial-data` = certaines sections chargées,
d'autres non (une source amont indisponible, pas toutes).

## Navigation

- Chaque carte de chaque section route vers l'écran propriétaire :
  Priority prospects → `../discover/index.html` ; Signals →
  `../discover/signals.html` ; Research blockers → `../research/index.html`
  ; Fit reviews → `../fit/index.html` ; Reach tasks → `../reach/index.html`
  ; Recent engagement → `../engagement/index.html` ; Opportunities at risk
  → `../pipeline/index.html`.
- "Next best actions" : CTA vers l'écran d'action réel ; toute action qui
  franchirait une ligne interdite (§5 SHELL_CONTRACT — ex. créer une
  Opportunity depuis un clic non gouverné) est rendue `disabled` avec
  tooltip explicite.
- Aucune action n'est exécutée depuis Home elle-même (pas d'édition
  inline) — Home ne fait que qualifier "où aller".

## Responsive

| Écran | Desktop | Tablet | Mobile |
|---|---|---|---|
| My Day (toutes sections) | FULL — grille 2-3 colonnes par section | FULL — grille recolonnée à 2, sections empilées | READ — 1 colonne, sections repliables (accordéon), queue agrégée en tête |
| Next best actions | FULL — rangée de CTA | FULL | READ — CTA empilés pleine largeur |

Home mobile priorise la queue agrégée (le "quoi faire maintenant") en haut
de page ; les sections détaillées passent en accordéon replié par défaut
pour limiter le scroll — cohérent avec le rôle de triage quotidien de
l'écran (pas un espace d'exploration profonde, réservé à Discover/Research).

## DECISION_REQUIRED

1. Le critère "opportunity at risk" (seuil de staleness sur
   `last_engagement`, règle de stagnation de stage) n'est défini nulle
   part dans la mission ni dans `mock-data.js` — ce prototype affiche un
   badge `Hypothèse` sur le risque plutôt qu'un score calculé, en attendant
   une définition métier de l'architecture owner.
2. La composition exacte de la "queue" My Day (ordre de priorité entre
   Fit review vs Research blocker vs Reach task en attente) n'est pas
   spécifiée — ici triée par ordre d'apparition des sections, pas par un
   score de priorité inventé.
3. Home réel (`app/dashboard.py`'s `FollowUpCockpit`) n'a pas de route
   HTTP dédiée par section (une seule projection `/api/follow-up`) — ce
   mockup suppose que chaque section future aura son propre lien profond
   vers l'écran cible ; à confirmer avec l'architecture owner si la
   projection réelle expose déjà ces sous-liens ou si Home devra les
   dériver côté client.
4. Un compte a zéro `Opportunity` "at risk" dans le mock (une seule
   opportunité au total) — la section est donc illustrée avec un unique
   exemple ; le comportement à plusieurs comptes/plusieurs opportunités à
   risque n'est pas testé visuellement ici.
