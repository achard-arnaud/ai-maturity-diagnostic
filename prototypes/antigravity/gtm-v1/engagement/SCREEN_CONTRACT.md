# Engagement — Screen Contract

Per `ANTIGRAVITY_02` excerpt "Engagement" and `SHELL_CONTRACT.md`.
Authority: NONE — UX exploration only.

## Job

Engagement répond à *qu'a fait le prospect ?* (jamais *qu'avons-nous fait ?*
— c'est Activity). Le principe mission est strict : **Activité (ce que nous
avons fait)** et **Engagement (ce que le prospect a fait)** sont deux
notions séparées et **ne doivent jamais être fusionnées dans un seul flux
sans distinction de lane/filtre claire**. Cet écran gère l'inbox des
réponses entrantes et le flux d'activité à deux lanes.

## Objets affichés

`EngagementEvent`, `Touchpoint` (pour la lane "Activité sortante"),
`Sequence`, `Person`, `Company`, `FitAssessment` (contexte). Mock de base :
`eng_1` (réponse positive de Marc Ferréol). Pour illustrer les statuts
demandés par la mission (meeting booked, objection, unsubscribe, no-response,
follow-up due), `index.html`/`activity.html` ajoutent localement des
**instances supplémentaires de la même forme `EngagementEvent`** (mêmes
`sequence_id`/`person_id` déjà présents dans le mock, ex. `pe_claire`,
`pe_lina`), pas un nouvel objet canonique — voir DECISION_REQUIRED #1.

## Composants

- `index.html` — **Inbox / Conversations** : réponses entrantes, meeting
  booké, objection, réponse positive, unsubscribe/consentement retiré,
  statut no-response, follow-up dû. Chaque ligne → `conversation.html`.
- `conversation.html` — détail d'une conversation : thread, séquence/
  touchpoints liés, compte, target, contexte Fit, objections, prochaine
  action, CTA stop/pause de la séquence.
- `activity.html` — **Activity Feed**, deux lanes explicitement
  distinctes : **Activité sortante** (envoyé/appelé/tâche faite, dérivé de
  `Touchpoint`) vs **Engagement externe** (répondu/cliqué/booké/participé/
  objecté, dérivé de `EngagementEvent`) — jamais mélangées dans une même
  liste sans filtre.

## États

Voir `states.html` — 8 états appliqués à l'Inbox.

## Navigation

- Depuis Reach : un `Touchpoint` envoyé peut générer un `EngagementEvent`
  (non simulé comme automatique — voir règle mission "jamais d'engagement
  inféré d'un email envoyé").
- Depuis Inbox : une ligne → `conversation.html?engagement_id=…`.
- Depuis Conversation : CTA "Stopper la séquence" / "Mettre en pause" —
  action UI uniquement, non persistée.
- Depuis Activity Feed : bascule Outbound / External / Les deux, jamais un
  mélange par défaut sans lane visible.

## Responsive

| Écran | Desktop | Tablet | Mobile |
|---|---|---|---|
| Inbox | FULL — table complète | FULL — colonnes secondaires repliées | READ — une carte par conversation |
| Conversation detail | FULL — 2 colonnes (thread + contexte) | FULL — colonnes empilées | READ — colonnes empilées, CTA pleine largeur |
| Activity Feed | FULL — 2 lanes côte à côte | FULL — 2 lanes empilées | READ — bascule d'une lane à la fois via filtre |

## DECISION_REQUIRED

1. `shared/mock-data.js` ne contient qu'un seul `EngagementEvent` (`eng_1`,
   `replied`). Pour montrer les statuts demandés par la mission (meeting
   booked, objection, unsubscribe, no-response, follow-up due), `index.html`
   et `activity.html` ajoutent des instances **locales** supplémentaires de
   la même forme d'objet, non persistées dans `shared/mock-data.js` (règle
   d'isolation : ce prototype ne modifie pas `shared/**`). Si ces cas
   doivent devenir des fixtures partagées, c'est une décision pour l'agent
   propriétaire de `shared/mock-data.js`, pas pour cet écran.
2. Le mapping "quel `Touchpoint.status` compte comme Activité sortante
   affichable" (`scheduled` → affiché comme "envoyé" dans la démo) est une
   simplification d'affichage locale ; le vrai statut d'envoi effectif
   (vs. planifié) est une décision de state machine du domaine Reach.
3. Aucune CTA de cet écran ne transforme un envoi (`Touchpoint`) en
   `EngagementEvent` automatiquement — l'ajout d'un événement d'engagement
   simulé nécessiterait toujours une source externe réelle (webhook email/
   CRM), jamais un bouton "marquer comme engagé" côté opérateur.
