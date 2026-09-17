# Admin / Automation & Settings — Screen Contract

Per `ANTIGRAVITY_03` excerpt "Admin / Automation & Settings" and
`SHELL_CONTRACT.md`. Authority: NONE — UX exploration only.

## Job

Un point d'entrée structurant vers la configuration et l'automatisation —
**pas** une réécriture des pages `/admin/*` réelles qui fonctionnent déjà
(`app/authruntime/app.py`, `app/server.py`). Par lecture de
`USE_CASE_PLATFORM_GAP_MATRIX.md` §1 (ligne Admin) et
`AUTH_LOGIN_GAP.md` §11 : les pages admin réelles
(`/admin/workspaces`, `/admin/memberships`, `/admin/users`, `/admin/audit`,
`/admin/overrides`, `/admin/network/rebuild-index`,
`/admin/network/companies/{id}/reassign`) sont déjà correctement gérées
(`require_role("admin")`, testées, "reference pattern" selon l'audit). Ce
mockup les **linke**, il ne les duplique pas.

## Objets affichés

Aucun objet canonique de `SHELL_CONTRACT.md` §4 n'est modifié ici — Admin
affiche des **entrées de navigation structurantes** (Workflows, Scoring/
policies, Enrichment, Integrations, Data model, Users/workspace,
Compliance, Skills/Assets diagnostics) et un sous-écran `Artifact` en
lecture seule (`artifact-library.html`, utilisant les `Artifact` mock de
`shared/mock-data.js`).

## Composants

- `index.html` — grille de 8 groupes structurants (cf. Job). Chaque groupe
  est une carte avec : description courte, statut d'implémentation réel
  (`Existe déjà → lien réel` / `Pas encore construit → placeholder
  désactivé`), sourcé sur `USE_CASE_PLATFORM_GAP_MATRIX.md` et
  `OPERATIONS_OBSERVABILITY_GAP.md` (jamais inventé).
  - **Users / workspace** → lien réel vers `/admin/workspaces`,
    `/admin/memberships`, `/admin/users` (existant, cf. gap matrix).
  - **Compliance** → lien réel vers `/admin/audit`.
  - **Data model (admin-only)** → lien réel vers
    `/admin/network/rebuild-index` / `/admin/network/companies/{id}/reassign`
    (existant), présenté en lecture/admin-only conformément à la mission.
  - **Workflows, Scoring/policies, Enrichment, Integrations** → aucune
    page admin réelle trouvée pour ces groupes dans le code lu ; cartes
    affichées avec CTA `disabled` et tooltip "pas encore construit côté
    produit réel" plutôt qu'un faux écran qui laisserait croire à une
    capacité existante.
  - **Skills/Assets diagnostics** → pas de page admin dédiée trouvée
    (le skill executor existe, `POST /api/skills/{id}/invoke`, mais sans
    tracing/diagnostic visible per `OPERATIONS_OBSERVABILITY_GAP.md` §7
    AgentTrace gap) ; carte `disabled` avec le même tooltip, citant le gap.
- `artifact-library.html` — placeholder conceptuel V1 de la bibliothèque
  d'outputs (cf. mission "Artifact/Output Library placeholder"), repliée
  ici en sous-page d'Admin faute de slot de nav dédié.

## États

Voir `states.html` — 8 états appliqués à la grille de groupes admin.
`blocked` illustre un groupe dont le lien réel est temporairement
inaccessible (droits insuffisants — cf. `require_role("admin")` réel).

## Navigation

- Chaque carte "existe déjà" pointe vers l'URL réelle du produit
  (chemin absolu, ex. `/admin/workspaces`) — ce sont des liens de
  navigation vers l'application réelle, pas des fichiers dupliqués sous
  `prototypes/**` (aucune règle d'isolation n'interdit un lien `<a href>`
  vers l'app réelle, seule l'édition de fichiers hors périmètre est
  interdite).
- `artifact-library.html` : accessible depuis `index.html` (carte dédiée)
  et depuis Insights (lien "voir aussi Admin" pour l'observabilité — pas
  pour la bibliothèque d'artefacts, qui reste un sujet Admin séparé).

## Responsive

| Écran | Desktop | Tablet | Mobile |
|---|---|---|---|
| Admin Home (8 groupes) | FULL — grille 3-4 colonnes | FULL — grille recolonnée à 2 | READ — 1 colonne, groupes non construits repliés sous "Bientôt" en fin de liste |
| Artifact Library (liste/grille + filtres) | FULL — table/grille + filtres latéraux | FULL — filtres en tiroir au-dessus de la liste | READ — cartes empilées, filtres en feuille modale, aperçu plein écran |

Cohérent avec le statut "visuellement secondaire" d'Admin dans la sidebar
quotidienne (`SHELL_CONTRACT.md` §1) — Admin n'a pas de traitement mobile
prioritaire au-delà du recolonnage standard.

## DECISION_REQUIRED

1. Quatre des huit groupes demandés par la mission (Workflows, Scoring/
   policies, Enrichment, Integrations) n'ont **aucune** page admin réelle
   trouvée dans `app/` — ce mockup ne tranche pas s'ils doivent devenir de
   nouvelles pages `/admin/*` réelles, des vues purement produit
   (ex. Scoring/policies pourrait vivre dans Fit plutôt qu'Admin), ou
   rester hors scope V1 ; décision d'architecture, pas UX.
2. "Skills/Assets diagnostics" recoupe le gap AgentTrace confirmé par
   `OPERATIONS_OBSERVABILITY_GAP.md` §7 (candidate Epic E20) — ce mockup
   ne préempte pas si ce diagnostic doit vivre dans Admin ou dans un futur
   espace d'observabilité dédié (E20 le suggère explicitement séparé
   d'Insights, mais reste ambigu vis-à-vis d'Admin).
3. La bibliothèque d'artefacts (`artifact-library.html`) n'a aucune
   contrepartie de stockage réelle (`USE_CASE_PLATFORM_GAP_MATRIX.md`
   confirme l'absence totale d'index/recherche d'artefacts, candidate
   Epic E15) — toutes les actions Edit/Export/Version history y sont donc
   rendues `disabled` par construction, jamais simulées comme
   fonctionnelles.
4. Aucune règle de visibilité par rôle n'est simulée ici (ex. un
   `standard_user` verrait-il Admin du tout ?) — la sidebar partagée
   affiche toujours Admin (SHELL_CONTRACT §1), la question RBAC-par-item
   reste ouverte, cf. `AUTH_LOGIN_GAP.md` §10.
