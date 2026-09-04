---
name: prospection-principes
description: Concevoir et exécuter une prospection B2B amplifiée par IA à partir d'un ICP comportemental, de nids à prospects, d'un scoring explicite, d'un CRM à états, de messages contextualisés et de relances à valeur ajoutée. À utiliser pour qualifier une cible, transformer un signal marché en prospection, construire un outbound story-led, ou industrialiser un process de prospection sans automatiser aveuglément la vente.
status: todo
---

# Prospection principes

## Objectif

Transformer une stratégie de prospection en **process opérable par un humain + IA** :

`ICP comportemental → nids à prospects → acquisition/enrichissement → scoring → base à états → message → relances → feedback → contenu/use case`

La règle mère est : **l'IA exécute ; le process décide**.

Cette skill ne remplace ni une stratégie d'offre ni les outils d'acquisition. Elle orchestre les décisions et délègue la collecte à des skills/outils spécialisés (`linkedin-search`, `youtube-search`, web, GitHub, CRM, etc.).

## Principes non négociables

1. **Cibler par comportement, pas seulement par métier.** Un titre de poste ne suffit jamais à définir un ICP.
2. **Chercher des nids, pas des individus au hasard.** Densité + contexte commun + signal d'intention > liste générique.
3. **Scorer avant d'enrichir cher.** Utiliser d'abord les données déjà visibles ; ne payer/approfondir l'enrichissement que pour le haut du panier.
4. **Une ligne = un prospect + un état.** La base, les statuts et les timestamps pilotent la suite ; la mémoire humaine ne doit pas être le workflow.
5. **Un bon message cible un problème.** Ne jamais déballer la solution avant que le prospect ait une raison de s'y intéresser.
6. **Réaction → piédestal → problème → demande.** C'est la forme de base du premier contact.
7. **La relance réengage ; elle ne répète pas.** Chaque relance apporte de la valeur ou une nouvelle raison de répondre.
8. **Process-first.** La différenciation vient de la qualité de la méthode, du scoring, des preuves, du tone of voice et des règles d'arrêt — pas de l'automatisation elle-même.
9. **Preuve avant narration.** Un signal, un commentaire, un cas client ou un benchmark doit être sourcé avant d'être utilisé comme story.
10. **Aucun faux contexte.** Ne jamais inventer une relation commune, une familiarité, un problème individuel non observé ou une preuve sociale.

---

# 1. Clarifier l'ICP

## 1.1 Définition comportementale

Décrire l'ICP avec au minimum :

- **comportement actuel** : ce qu'il fait déjà ;
- **situation / contexte** : dans quel environnement il agit ;
- **friction observable** : ce qui lui coûte du temps, de l'argent, de la coordination ou du risque ;
- **couche 1 — frustration** : douleur de surface ;
- **couche 2 — peur / risque** : conséquence qu'il veut éviter ;
- **couche 3 — désir** : état aspirationnel ;
- **verbatim** : mots qu'il emploie réellement ;
- **anti-ICP** : comportements qui indiquent qu'il faut exclure ou scorer bas.

Format préféré :

```yaml
icp:
  segment_label: ""
  current_behavior: ""
  context: ""
  surface_frustration: ""
  deeper_risk: ""
  aspiration: ""
  verbatim: []
  anti_icp: []
```

## 1.2 Les 5 niveaux de conscience

Classer chaque prospect ou nid selon :

1. `unaware` — ne perçoit pas encore le problème ;
2. `problem_aware` — ressent la douleur mais ne sait pas précisément comment la traiter ;
3. `solution_aware` — sait qu'une catégorie de solution existe ;
4. `your_solution_aware` — connaît l'approche spécifique / le produit ;
5. `most_aware` — connaît l'offre et peut décider maintenant.

**Règle de message :** ne jamais parler comme à un `most_aware` si le signal observé montre seulement `problem_aware`.

---

# 2. Trouver les nids à prospects

Un **nid à prospects** est un espace où plusieurs ICP sont déjà réunis autour d'un contexte commun.

## 2.1 Critères d'un bon nid

- **densité** : assez de prospects pour justifier l'effort ;
- **contexte commun** : sujet, problème, outil, événement ou comportement partagé ;
- **contactabilité** : moyen de contact ou profil public accessible ;
- **fraîcheur** : activité récente ;
- **intention** : l'action observée dit quelque chose du niveau de conscience.

Prioriser les comportements à plus forte intention. En règle générale :

`question/commentaire précis > commentaire générique > réaction/like > simple abonnement > liste froide`

Adapter ce classement au canal et au contexte ; ce n'est pas une vérité universelle.

## 2.2 Nids typiques

- commentaires sur une annonce ou un post de concurrent ;
- personnes qui posent des questions sur un problème précis ;
- communautés et événements spécialisés ;
- GitHub issues/discussions autour d'un problème technique ;
- followers/abonnés d'un créateur très spécialisé ;
- listes d'exposants/participants à un événement pertinent ;
- entreprises publiant un signal de maturité ou de friction : recrutement, stack, migration, lancement, incident, nouveau pricing, etc.

## 2.3 Deux modes de découverte

- **IA suggère, humain valide** : l'IA propose 10–20 nids ; l'humain confirme la pertinence.
- **Humain indique, IA exécute** : l'humain connaît déjà les créateurs, communautés, concurrents ou événements à exploiter.

Ne jamais automatiser le ciblage d'un nid non validé.

---

# 3. Scraper / acquérir puis enrichir

La skill orchestre la collecte mais ne dépend d'aucun fournisseur précis.

## 3.1 Acquisition minimale

Collecter d'abord uniquement ce qui suffit pour décider si le prospect mérite une analyse plus profonde :

- nom / profil public ;
- société / rôle ;
- nid source ;
- action observée (commentaire, post, question, issue, événement) ;
- texte du signal ;
- bio / description publique ;
- date ;
- URL de preuve.

## 3.2 Score avant enrichissement coûteux

**Gater l'enrichissement** :

```text
acquisition minimale
    ↓
score ICP + awareness
    ↓
si score ≥ seuil → enrichissement professionnel public
sinon → backlog / discard
```

Le seuil de départ recommandé est **80/100** lorsque le volume le permet. Il doit être calibré par l'observation des taux de réponse et non traité comme universel.

## 3.3 Enrichissement autorisé

Pour les prospects au-dessus du seuil, compléter avec des données professionnelles publiques et pertinentes :

- site officiel ;
- rôle / équipe ;
- posts ou commentaires récents ;
- stack déclarée ;
- offres / produits ;
- recrutements ;
- conférences / interventions ;
- email professionnel public ou moyen de contact professionnel légitime.

**Interdits :** données issues de fuites, données privées non destinées à la prospection, faux profils, contournement d'accès, fausse relation commune, inférences sensibles non nécessaires.

---

# 4. Scorer les prospects

## 4.1 Grille par défaut /100

La vidéo montre une grille à quatre dimensions. La skill la généralise ainsi :

| Dimension | Poids | Question |
|---|---:|---|
| Fit comportemental ICP | 30 | Ce prospect ressemble-t-il réellement à l'utilisateur de l'offre ? |
| Comportement / usage lié au problème | 30 | Montre-t-il déjà le comportement qui rend l'offre utile ? |
| Intensité de douleur / enjeu | 25 | Le coût du problème est-il visible ou vraisemblable ? |
| Awareness + engagement | 15 | Son action montre-t-elle une intention et un niveau de conscience exploitables ? |

`score_total = A + B + C + D`

Chaque score doit avoir une **justification courte** et une **preuve URL/date** lorsque possible.

## 4.2 Calibration

La pondération `30/30/25/15` est un **default**, pas un contrat universel. Recalibrer selon l'offre :

- produit complexe → augmenter `awareness` ;
- offre réglementée / grand compte → ajouter autorité d'achat / conformité ;
- produit self-serve → augmenter comportement et timing ;
- offre premium → ajouter budget/proxy économique public et légitime.

## 4.3 Sortie scoring

```yaml
prospect_score:
  fit_behavior: 0-30
  problem_behavior: 0-30
  pain_or_stakes: 0-25
  awareness_engagement: 0-15
  total: 0-100
  awareness: unaware|problem_aware|solution_aware|your_solution_aware|most_aware
  evidence: []
  rationale: ""
  decision: enrich|contact|nurture|discard
```

---

# 5. Créer la base de prospection

## 5.1 Principe

**Une ligne = un prospect + un statut.**

Minimum de colonnes :

```text
Name | Company | Role | NidSource | SignalURL | Score | Awareness |
Channel | Status | LastActionAt | NextActionAt | Notes | Owner
```

## 5.2 State machine

Cycle de base :

`new → to_contact → contacted → followup_1 → followup_2 → followup_3 → replied → meeting → won/lost`

États optionnels : `nurture`, `not_qualified`, `do_not_contact`.

Le système lit l'état + le timestamp et propose l'action suivante. Les changements d'état doivent être tracés.

## 5.3 Automatisation

L'automatisation peut :

- détecter qui contacter / relancer ;
- préparer le message ;
- proposer le canal ;
- mettre à jour les statuts ;
- générer un rapport.

Elle ne doit pas :

- inventer une preuve ;
- envoyer automatiquement un message sensible ou ambigu sans validation humaine ;
- relancer après opt-out ;
- transformer une inférence en fait.

---

# 6. Contacter — le premier message

## 6.1 Principe premier

> Il n'y a pas de format magique ; il y a surtout des messages ennuyeux, génériques ou prématurément vendeurs.

Le premier message vise **un problème et une conversation**, pas une démonstration complète de la solution.

## 6.2 Les 4 temps

### 1. Réaction

Rebondir sur une occasion réelle et récente :

- commentaire ;
- question ;
- post ;
- lancement ;
- recrutement ;
- adoption d'un outil ;
- annonce concurrentielle à laquelle le prospect a réagi.

Le hook doit être vérifiable.

### 2. Piédestal spécifique

Valoriser un élément **concret** du travail du prospect avant de parler du problème.

Bon : référence à un produit, une méthode, une contrainte, un choix visible.

Mauvais : « impressionné par votre parcours », « entreprise innovante », « profil inspirant ».

### 3. Problème

Nommer la douleur avec les mots de l'ICP + sa conséquence.

Ne pas écrire : « vous avez ce problème » si ce n'est pas établi.

Préférer : « ce qu'on observe souvent chez des équipes qui [comportement], c'est [problème]. Est-ce aussi votre cas ? »

### 4. Demande / pied dans la porte

Faire une demande petite et claire :

- 15–20 minutes ;
- avis sur une observation ;
- retour sur un mini benchmark ;
- permission d'envoyer une ressource ;
- courte démo si le prospect est déjà solution-aware.

## 6.3 Posture

- **partage de solution, pas vente** ;
- montrer comment on traite le problème plutôt que « pitcher » ;
- donner une opportunité de conversation ;
- zéro pression ;
- supprimer tout élément personnalisé qui n'est pas réellement spécifique.

## 6.4 Template

```text
[Réaction réelle]

[Piédestal spécifique]

[Problème formulé comme observation/hypothèse + conséquence]

[Question ou début de solution]
[CTA léger]
```

---

# 7. Mettre en place les relances

## 7.1 Principe

**Pas de réponse ≠ non définitif.** Une relance doit réengager la conversation, jamais uniquement demander si le message précédent a été vu.

À bannir :

> « Avez-vous vu mon message ? Toujours intéressé ? »

## 7.2 Séquence de référence

Cadence issue du support vidéo :

- `J+1` — relance 1 : ajout de valeur ;
- `J+4` — relance 2 : question ouverte + preuve / cas proche ;
- `J+10` — relance 3 : porte de sortie élégante ;
- après cela : nurture léger seulement si pertinent et autorisé.

Adapter la cadence au canal, au marché et au contexte ; ne pas transformer ces délais en spam automatique.

## 7.3 8 angles de relance

1. amicale / prise de nouvelles contextualisée ;
2. ajout de valeur : article, template, benchmark, mini audit ;
3. rappel d'une offre si le prospect est déjà offer-aware ;
4. échéance / urgence **réelle** ;
5. reprise après un long silence ;
6. question ouverte ;
7. incitatif pertinent et légitime ;
8. demande de feedback.

Chaque relance doit apporter un nouvel élément.

---

# 8. Couche storytelling — bridges et side stories

Cette couche adapte les mécanismes du repo `tourisme-etude-historico-geographique` à la prospection et au contenu. Elle ne remplace pas les étapes 1–7 ; elle les rend plus cohérentes et réutilisables.

## 8.1 Tronc narratif

Le **tronc** est toujours :

`ICP → comportement → problème → conséquence → mécanisme → résultat attendu → CTA`

Une histoire ou un signal externe n'a de valeur que s'il renforce ce tronc.

## 8.2 Bridge

Un bridge relie une preuve externe au use case sans sauter de causalité :

`signal sourcé → mécanisme observé → implication pour l'ICP → différenciateur / use case → retour au problème`

Exemple Pragma :

`Atlassian ajoute une brique agentique → le marché reconnaît le besoin de coordination agents/travail → ce besoin valide le shared execution model → Pragma l'a by design → retour au use case agentic software delivery.`

## 8.3 Side story

Une `sales_side_story` est un détour court qui apporte :

- preuve ;
- comparaison ;
- méthode ;
- mini case study ;
- signal concurrentiel ;
- objection traitée ;
- callback lors d'une relance.

Elle ne doit jamais devenir une parenthèse autonome sans payoff.

Types recommandés :

- `competitor_signal` — mouvement concurrent comme validation de catégorie ;
- `peer_case` — cas proche de l'ICP ;
- `comparator` — alternative / avant-après ;
- `method` — explication d'un mécanisme ;
- `objection` — détour pour lever un frein ;
- `callback` — signal réutilisé dans une relance ;
- `proof_point` — donnée / preuve externe courte.

## 8.4 Contrat d'une side story

```yaml
side_story:
  id: ""
  kind: competitor_signal|peer_case|comparator|method|objection|callback|proof_point
  home_use_case: ""
  icp: ""
  source_url: ""
  source_date: ""
  observed_signal: ""
  mechanism: ""
  payoff: ""
  bridge_back: ""
  cta_role: awareness|conversation|proof|followup
  state: candidate|validated|published|retired
```

### Gate

Une side story entre dans le contenu principal seulement si elle augmente au moins un de ces éléments :

- compréhension du problème ;
- urgence / timing ;
- crédibilité ;
- différenciation ;
- projection dans le use case ;
- réponse à une objection.

Sinon : FAQ, backlog ou discard.

## 8.5 Recyclage contenu

Après publication :

- signal faible / question récurrente → **FAQ** ;
- signal fort / forte portée / forte conversion → **use case enrichi** ;
- signal utile au pipeline → **follow-up callback** ;
- preuve durable → **proof library** ;
- récit trop éloigné du tronc → retirer ou garder en backlog.

---

# 9. Workflow end-to-end

1. **Fixer l'offre / outcome** : ce que le prospect peut réellement obtenir.
2. **Définir l'ICP comportemental** + douleur + désir + verbatim + anti-ICP.
3. **Choisir le niveau de conscience visé.**
4. **Identifier 3–10 nids** à forte densité / contexte / intention.
5. **Acquérir un premier lot** de profils avec preuve du nid.
6. **Scorer /100** avant enrichissement coûteux.
7. **Enrichir le top** au-dessus du seuil.
8. **Insérer dans la base** avec état et timestamps.
9. **Préparer le message** en 4 temps à partir du contexte réel.
10. **Human review** si ambigu, sensible, nouveau segment ou premier batch.
11. **Envoyer / consigner** le statut.
12. **Relancer J+1 / J+4 / J+10** avec valeur distincte.
13. **Mesurer** : taux de qualification, réponse, conversation, meeting, conversion, opt-out.
14. **Réviser** scoring, nids, wording et seuils.
15. **Transformer les meilleurs signaux** en posts, FAQ, use cases ou side stories.

---

# 10. QA / gates

Avant toute prospection ou recommandation de campagne, vérifier :

## ICP gate
- [ ] comportement précis, pas seulement rôle ;
- [ ] douleur + peur/risque + désir ;
- [ ] verbatim ou hypothèse explicitement marquée ;
- [ ] niveau de conscience ;
- [ ] anti-ICP.

## Evidence gate
- [ ] signal source/date conservé ;
- [ ] aucun problème individuel présenté comme fait sans preuve ;
- [ ] aucune fausse relation ou faux contexte ;
- [ ] données utilisées professionnelles, publiques et pertinentes.

## Scoring gate
- [ ] poids explicites ;
- [ ] score justifié ;
- [ ] seuil d'enrichissement défini ;
- [ ] critères revus après les premiers résultats.

## Message gate
- [ ] hook réel ;
- [ ] piédestal spécifique ou supprimé ;
- [ ] problème formulé sans surclaim ;
- [ ] CTA faible friction ;
- [ ] pas de pitch générique.

## Follow-up gate
- [ ] chaque relance apporte de la valeur ;
- [ ] rythme raisonnable ;
- [ ] opt-out respecté ;
- [ ] porte de sortie après la séquence.

## Story gate
- [ ] lineage source → mécanisme → payoff ;
- [ ] side story a un home use case ;
- [ ] retour au tronc explicite ;
- [ ] pas de nouvelle preuve inventée par la narration.

---

# 11. Sorties attendues

Selon la demande, produire un ou plusieurs artefacts courts :

- `ICP_CARD` ;
- `PROSPECT_NESTS` ;
- `SCORING_RUBRIC` ;
- `PROSPECT_BATCH` ;
- `OUTBOUND_MESSAGE` ;
- `FOLLOWUP_SEQUENCE` ;
- `CRM_STATE_MACHINE` ;
- `SALES_SIDE_STORY` ;
- `LINKEDIN_POST` ;
- `FAQ_CANDIDATE` ;
- `USE_CASE_ENRICHMENT` ;
- `RETEX` avec métriques et changements de process.

Ne pas produire une longue stratégie quand l'utilisateur demande seulement un message ou un scoring : appliquer la skill en interne puis restituer l'artefact demandé.

---

# 12. Provenance méthodologique

La structure principale de cette skill est dérivée de la masterclass **« Prospection amplifiée par IA » — Eliott Meunier**, transcript officiel YouTube auto-généré fourni par l'utilisateur, et de ses captures du support Obsidian : ICP comportemental, niveaux de conscience, nids à prospects, acquisition/enrichissement, scoring, base à états, premier message en quatre temps, relances et process-first.

La couche complémentaire est adaptée du repo `achard-arnaud/tourisme-etude-historico-geographique` : arc/tronc, lineage, bridges, side stories bornées, payoff, retour au tronc, lifecycle et QA. Ces concepts sont transposés à la prospection ; ils ne sont pas des prescriptions de la vidéo originale.