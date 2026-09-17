# GTM V1 — Consolidated Responsive Matrix

Authority: NONE — UX exploration only, per `SHELL_CONTRACT.md`.

Consolidates every screen's own `SCREEN_CONTRACT.md` §Responsive into one
table, per the mission's cross-cutting responsive-matrix deliverable.
Breakpoints reused from `SHELL_CONTRACT.md` §6: **Desktop >900px · Tablet
720–900px · Mobile ≤720px**. `FULL` = same information density as
desktop, recolonnée ; `READ` = reduced density, some columns/sections
dropped or converted to an alternative layout (see "Mobile alternative").

Each screen below often has several sub-views with slightly different
mobile treatments (tables vs. graphs vs. boards) — this table gives the
dominant pattern per screen and calls out material exceptions inline.
For the full per-sub-view breakdown, see that screen's own
`SCREEN_CONTRACT.md`.

| Screen | Desktop | Tablet | Mobile | Mobile alternative |
|---|---|---|---|---|
| **Home** | FULL — grille de cards 2-3 colonnes par section (My Day, priority accounts, signals, blockers, Fit reviews, Reach tasks, follow-ups, engagement, at-risk, next best actions) | FULL — grille recolonnée à 2 colonnes, sections toujours dépliées | READ — 1 colonne ; queue My Day agrégée priorisée en tête de page | Sections détaillées repliées en accordéon (fermées par défaut) sous la queue agrégée — priorise "quoi faire maintenant" sur l'exploration |
| **Discover** | FULL — grille de cards (Home) / tables complètes (People, Companies) | FULL (Home, Signals) / READ avec colonnes secondaires masquées (People, Companies) | READ — 1 colonne | Tables People/Companies converties en 1 carte par ligne ; recherche globale réduite à une icône |
| **Research** | FULL — table complète (Research Home) ; Company 360 en 9 onglets + 2 colonnes de sections | FULL, avec colonnes secondaires masquées sur la queue et onglets scrollables horizontalement | READ | Table Research Home → 1 carte par compte ; barre d'onglets Company 360 → sélecteur déroulant ; sections Research → 1 colonne repliable |
| **Fit** | FULL — table de queue avec filtres visibles ; Fit Detail en 2 colonnes (corps + right rail) ; Product Library en 4 colonnes | FULL — filtres empilés au-dessus de la table ; right rail passe sous le corps ; Product Library en 2 colonnes | READ | Fit Queue → 1 carte par assessment ; Fit Detail → sections repliables, right rail en bas ; Product Library → liste verticale, une entité à la fois |
| **Targets** | FULL — grille de cartes par compte ; Buying Committee en table complète + option graphe | FULL — grille recolonnée à 2 ; colonnes secondaires (preuve/fraîcheur) en info-bulle ; graphe en colonnes empilées | READ | Targets Home → liste 1 colonne, couverture réduite à un badge compact ; Buying Committee table → 1 carte par personne ; graphe masqué (pas de canvas complexe en mobile), remplacé par une liste simple |
| **Reach** | FULL — table complète (Execution Queue, Sequences/Messages/Tasks/Calls/Meetings/History) ; Message preview en 2 colonnes | FULL — colonnes preuve/retry en info-bulle ; Message preview en colonnes empilées | READ | Tables converties en 1 carte par item (tri horaire conservé sur la queue) ; Message preview en colonnes empilées avec CTA pleine largeur |
| **Engagement** | FULL — Inbox en table ; Conversation detail en 2 colonnes ; Activity Feed en 2 lanes côte à côte | FULL — colonnes secondaires repliées ; colonnes/lanes empilées | READ | Inbox → 1 carte par conversation ; Conversation detail → colonnes empilées, CTA pleine largeur ; Activity Feed → bascule d'une lane à la fois via filtre |
| **Pipeline** | FULL — tables (Leads/Opportunities/Deals) ; Board en colonnes côte à côte avec scroll horizontal ; Detail en 2 colonnes | FULL — colonnes secondaires repliées ; scroll horizontal du board conservé ; colonnes empilées en detail | READ | Tables → 1 carte par ligne ; Board → colonnes empilées verticalement (pas de scroll horizontal forcé) ; Detail → sections repliables |
| **Insights** | FULL — grille de tuiles métriques 3-4 colonnes par section (8 sujets) ; Learning Proposals en table + détail | FULL — grille recolonnée à 2 | READ | Sections repliables ; bandeau "projection ≠ vérité" toujours visible, jamais replié ; Learning Proposals en cartes empilées avec action de transition conservée |
| **Admin** | FULL — grille de 8 groupes structurants ; Artifact Library en table/grille + filtres latéraux | FULL — grille recolonnée à 2 ; filtres Artifact Library en tiroir au-dessus de la liste | READ | Groupes non construits repliés sous "Bientôt" en fin de liste ; Artifact Library en cartes empilées, filtres en feuille modale, aperçu plein écran |

## Écrans supplémentaires livrés dans cette prise en charge (hors liste des 10, mais dans le périmètre de la mission)

| Screen | Desktop | Tablet | Mobile | Mobile alternative |
|---|---|---|---|---|
| **Login** | FULL — carte centrée, largeur fixe (sign-in / workspace select / onboarding) | FULL — carte centrée, largeur fluide | FULL | Pas de mode READ dégradé — écran mono-tâche déjà minimal ; carte pleine largeur avec marges, aucun contenu perdu |
| **Export / Editor** | FULL — stepper horizontal, panneau large ; Revue en 2 colonnes (diff avant/après) | FULL — stepper horizontal, panneau pleine largeur ; colonnes de diff empilées | READ | Stepper vertical compact (étape courante + libellé) ; diff avant/après en accordéon ; aperçu du rendu réduit |

## Statut de consolidation

Toutes les `SCREEN_CONTRACT.md` des 12 écrans du programme (les 10 requis
par la mission + Login + Export) existaient au moment de la construction
de cette matrice — **aucune ligne n'a dû être laissée "pending"**. Les 6
écrans non construits par cette prise en charge (Research, Fit, Targets,
Reach, Engagement, Pipeline) ont été lus directement depuis leur propre
`SCREEN_CONTRACT.md` (déjà présents dans le dépôt au moment de cette
étape) et consolidés ici sans re-dérivation ni supposition.
