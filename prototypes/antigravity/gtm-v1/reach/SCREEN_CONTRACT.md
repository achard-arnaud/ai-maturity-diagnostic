# Reach — Screen Contract

Per `ANTIGRAVITY_02` excerpt "Reach" and `SHELL_CONTRACT.md`.
Authority: NONE — UX exploration only.

## Job

Reach est l'espace d'exécution des `Sequence`/`Touchpoint` d'un `TargetPlan`
validé : *qu'est-ce qui doit partir aujourd'hui, à qui, pourquoi maintenant,
et qu'est-ce qui attend une approbation humaine ?* Reach n'invente jamais
d'automatisation qui n'existe pas réellement — en particulier, **aucun envoi
LinkedIn n'est simulé comme automatique** : c'est toujours une tâche manuelle
avec passation.

## Objets affichés

`TargetPlan`, `Sequence`, `Touchpoint`, `Person`, `Company`, `FitAssessment`
(pour le "fit context"), `Evidence` (pour la personnalisation du message).
Mock : `seq_acme_1` (2 `Touchpoint` : `tpt_1` email vers Marc Ferréol,
`tpt_2` tâche manuelle LinkedIn vers Claire Dubosc).

## Composants

- `index.html` — **Reach Home = Execution Queue** : liste priorisée par
  horaire (ex. "09:00 Email — Acme Corp / Champion", "09:05 Tâche manuelle
  LinkedIn — Acme Corp / Economic buyer"). Chaque ligne montre : target,
  compte, contexte Fit, why now, étape de séquence, canal, preuve liée,
  statut d'approbation, échéance, état retry/pause.
- `sequences.html` — liste des `Sequence` (nom, statut, canal, nombre
  d'étapes/touchpoints, plan de ciblage source).
- `messages.html` — templates/messages par étape de séquence, avec lien
  vers `message-preview.html` par ligne.
- `message-preview.html` — aperçu d'un message : texte, **les preuves/
  claims utilisées pour la personnalisation** (badges épistémiques), CTA
  Approuver / Modifier / Rejeter / Mettre en pause. Pour un touchpoint
  `linkedin_manual_task`, aucune CTA "envoyer" : uniquement "Marquer comme
  fait manuellement" — jamais un envoi simulé comme automatique.
- `tasks.html` — tâches manuelles dues (sur-ensemble des touchpoints
  `*_manual_task`).
- `calls.html` — appels planifiés/à faire (vue vide avec état "empty"
  explicite : le mock ne contient aucun touchpoint `call`).
- `meetings.html` — réunions issues d'un engagement `meeting_booked` (vue
  vide ici : aucun `EngagementEvent` de ce type dans le mock — cf.
  Engagement pour ce type d'événement).
- `history.html` — historique des `Touchpoint` (tous statuts, tri
  chronologique), lecture seule.

## États

Voir `states.html` — 8 états appliqués à l'Execution Queue. `blocked`
illustre un touchpoint dont l'approbation humaine est en attente ;
`partial-data` illustre un canal (LinkedIn) dont le statut de tâche manuelle
n'a pas encore été synchronisé.

## Navigation

- Depuis Targets → Buying Committee : CTA "Envoyer vers Reach" ouvre
  `index.html?target_plan_id=…` filtré sur ce plan.
- Depuis l'Execution Queue : une ligne → `message-preview.html?touchpoint_id=…`.
- Depuis message-preview : "Approuver" fait passer le statut affiché à
  `approved` (simulé, non persisté) ; "Rejeter"/"Mettre en pause" idem côté
  UI seulement — aucune de ces actions n'appelle une API réelle ici.
- Un touchpoint `linkedin_manual_task` ne propose jamais de CTA d'envoi
  automatique — seulement une passation de tâche manuelle vers l'opérateur
  humain (règle mission explicite).

## Responsive

| Écran | Desktop | Tablet | Mobile |
|---|---|---|---|
| Execution Queue | FULL — table complète avec toutes colonnes | FULL — colonnes preuve/retry repliées en info-bulle | READ — une carte par item de file, tri horaire conservé |
| Sequences / Messages / Tasks / Calls / Meetings / History | FULL | FULL | READ — table convertie en cartes |
| Message preview | FULL — 2 colonnes (message + preuves) | FULL — colonnes empilées | READ — colonnes empilées, CTA en pleine largeur |

## DECISION_REQUIRED

1. `calls.html` et `meetings.html` sont des coquilles "empty state" : le
   mock ne contient ni `Touchpoint` de canal `call`, ni `EngagementEvent`
   `meeting_booked`. Ajouter ces instances est une décision de contenu de
   démo, pas de structure — non tranchée ici pour ne pas fabriquer une
   donnée qui n'existe pas dans `shared/mock-data.js`.
2. Le statut "approval status" affiché par item de file (`pending_approval`,
   `scheduled`⇒considéré `approved`) est déduit localement du champ
   `Touchpoint.status` existant — aucun champ `approval_status` séparé
   n'existe dans le mock. Si le vrai modèle sépare "statut d'exécution" et
   "statut d'approbation", c'est une décision de state machine à trancher
   par l'équipe domaine.
3. L'état "retry/pause" par item (compteur de tentatives, pause manuelle)
   n'existe pas dans `shared/mock-data.js` — affiché ici via un overlay
   local UI-only (`reach/index.html`), valeurs statiques illustratives, pas
   un vrai compteur d'essais.
4. Aucune CTA de cet écran ne crée, ne modifie ni ne déclenche un envoi
   LinkedIn automatique — tout `linkedin_manual_task` reste une passation
   manuelle explicite, jamais un bouton "envoyer" actif (règle mission,
   contrainte dure — pas une simple préférence UX).
