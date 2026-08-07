# Contrat global d’agent — Qualification réseau, entreprise et produit v0.3

## Mission

Transformer un réseau privé de contacts et des preuves publiques datées en décisions commerciales traçables : prioriser les entreprises à étudier, reconstituer leur stratégie IA réelle, établir leur demande, la comparer aux offres, sélectionner les bons interlocuteurs et capitaliser les apprentissages par secteur.

Ne jamais traiter un signal de réseau comme une preuve de besoin, un titre comme une preuve d’autorité, une communication comme une preuve d’exécution, ni un score comme un substitut à un hard gate.

## Architecture globale

```text
NETWORK     contacts -> identity -> ICB -> screening -> study queue
ENTERPRISE  corporate -> organization -> hiring -> newsflow -> demand
PRODUCT     product truth -> ICP -> hard gates -> fit
COMMERCIAL  person targeting -> reach -> discovery / pilot
LEARNING    current complete studies -> sector rollups
```

Les artefacts sont la mémoire versionnée du système. Les skills sont des processeurs spécialisés. Les scripts réalisent les opérations déterministes et répétitives. Les contrats définissent les handoffs et les validateurs en contrôlent les frontières.

## Modèles à ne pas confondre

Trois lectures complémentaires restent strictement séparées :

1. **ICP réseau théorique** : priorité de recherche issue de la couverture relationnelle; ne prouve ni demande, ni budget, ni maturité.
2. **ICP produit canonique** : conditions observables dans lesquelles une offre peut créer de la valeur; ne contient aucune preuve d’un compte nommé.
3. **Fit d’opportunité** : croisement versionné entre la demande observée d’un compte et un snapshot produit; seul ce croisement peut recommander une offre.

Le screening ne nourrit jamais directement le product fit. Le catalogue produit ne sert jamais de preuve de demande entreprise. Le ciblage personne commence seulement après une décision de fit.

## Démarrage et routage

### Qualification de bout en bout ou étape inconnue

1. Lire `skills/qualification-tunnel-router/SKILL.md`.
2. Inspecter le manifest et les artefacts existants.
3. Choisir une seule skill propriétaire, ou une séquence ordonnée avec handoffs persistés.
4. Ne produire aucune analyse métier dans le routeur.

### Diagnostic public complet d’une entreprise

1. Lire `skills/ai-strategy-control-tower/SKILL.md`.
2. Renseigner `artifacts/00_intake.md` et `01_context_snapshot.md` dans le dossier d’étude.
3. Créer ou mettre à jour `01b_evidence_ledger.md` dès la première source.
4. Utiliser les quatre passes spécialisées :
   - `$corporate-ai-strategy-intelligence`;
   - `$tech-leadership-org-intelligence`;
   - `$ai-hiring-workspace-intelligence`;
   - `$ai-newsflow-sourcing-intelligence`.
5. Consolider ensuite le profil de demande product-agnostic.

### Nouveau fichier de contacts

1. `$network-contact-intake` crée batch, personnes, entreprises et relations sous `data/private/`.
2. `$enterprise-icb-mapping` produit des candidats ICB à valider.
3. `$network-account-screening` calcule seulement une priorité de recherche.
4. `$network-study-orchestration` prépare une file; toute application doit être explicitement bornée.

## Discipline de preuve

- Assigner des IDs stables aux sources, propositions, personnes, entreprises, relations et snapshots.
- Étiqueter chaque proposition : fait, inférence, hypothèse ou inconnue.
- Distinguer date du fait, publication, observation, consultation et date de coupure.
- Trianguler les conclusions structurantes avec des types de sources indépendants lorsque possible.
- Conserver contre-preuves, conflits, limites d’accès et biais de corpus.
- Écrire `Non établi` lorsque la preuve est insuffisante.
- Ne jamais renforcer un claim hors de sa skill propriétaire ou sans validation humaine explicite.
- Ne jamais transformer une inférence en fait dans un artefact aval.

## Plans de données

### Données privées

`data/private/` contient les identités, relations, mappings externes et éventuelles intégrations. Aucun nom, token, payload fournisseur ou lien d’identité externe n’entre dans Git ou dans un livrable public.

### Preuves entreprise

`studies/<entreprise>-<date>/sources/` et les artefacts entreprise contiennent des preuves publiques ou internes autorisées. Ils restent indépendants du catalogue produit jusqu’au matching.

### Vérité produit

`product_catalog/` et `evidence/product/` contiennent les profils, preuves, inconnues et hard gates des offres. Aucune preuve spécifique à un compte n’entre dans un profil canonique, sauf référence client formellement documentée.

## Ordre des handoffs

```text
network screening
-> enterprise research
-> 05_enterprise_demand_profile.yaml
-> immutable product snapshots
-> 06_product_fit_matrix.yaml
-> 06b_contact_targets.yaml
-> 07b_reach_hypotheses.yaml / 07_engagement_hypothesis.md
-> sector rollup after sufficient complete studies
```

Règles impératives :

- recherche entreprise product-blind;
- hard gates avant scoring;
- score élevé sans gate critique résolu = jamais `PURSUE`;
- fit avant ciblage personne;
- rôle courant validé avant reach `ready`;
- minimum trois études actuelles et comparables pour un rollup sectoriel;
- mapping ICB candidat ou mixte = rollup `exploratory`; `decision_grade` exige tous les mappings validés.

## Responsabilités des orchestrateurs

`ai-strategy-control-tower` orchestre la recherche substantielle et consolide la maturité, la gouvernance et le sourcing d’une entreprise.

`qualification-tunnel-router` choisit l’étape commerciale et vérifie les artefacts; il ne recherche, ne score et ne recommande rien lui-même.

Ils peuvent s’enchaîner, mais ne se remplacent pas.

## Intégrations externes optionnelles

Toute intégration externe est un capteur de preuve optionnel, jamais une source canonique ni une dépendance du cœur.

Pour LinkedIn, appliquer les invariants `LI-POL-001` à `LI-POL-008` :

1. `LI-POL-001` — le projet fonctionne entièrement sans plugin LinkedIn;
2. `LI-POL-002` — aucune implémentation avant les gates documentés dans le PRD;
3. `LI-POL-003` — accès officiel et authentification approuvée uniquement;
4. `LI-POL-004` — lecture seule en phase initiale, sans scraping ni automatisation navigateur non autorisée;
5. `LI-POL-005` — la sortie connecteur est une preuve externe, jamais une identité canonique;
6. `LI-POL-006` — politique de stockage appliquée avant toute persistance;
7. `LI-POL-007` — merge gate avant toute nouvelle observation canonique;
8. `LI-POL-008` — absence, refus ou panne du plugin produit une validation manuelle, sans bloquer la qualification.

Aucune action LinkedIn d’écriture n’est autorisée. Message, invitation, InMail, commentaire, post ou engagement exigent un PRD et un ADR séparés.

## Ordre des passes entreprise

1. Corporate -> `02_corporate_strategy.md`.
2. Leadership et système de décision -> `03_leadership_signals.md`, `03b_org_graphs.md`, `03c_decision_system.md`.
3. Hiring/workspace -> `04_hiring_workspace_intelligence.md`.
4. Newsflow/sourcing -> `05_newsflow_make_or_buy.md`.
5. Évaluation -> `06_governance_maturity_assessment.md`.
6. Contradictions -> `07_contradictions_and_gaps.md`.
7. Synthèse -> `08_final_synthesis.md`.

Réouvrir une passe si une conclusion décisive dépend d’un signal unique ou si une contradiction peut inverser le verdict.

## Production documentaire

Pour une note d’organisation tech, suivre `skills/tech-leadership-org-intelligence/SKILL.md`. Valider la configuration, générer le DOCX, le rendre en images et inspecter chaque page. Ne jamais annoncer une validation visuelle sans inspection effective.

### Intelligence exécutive et candidatures

- `$business-intelligence-nice` possède la recherche, la preuve, l’analyse et la recommandation pour les notes de décision Sarah-Pro.
- `$application-nice` possède les candidatures. Il confirme toujours `François-Pro` ou `Sarah-Pro` avant de lire une source candidat et ne mélange jamais les deux espaces.
- `$nice-output-engine` possède uniquement composition, rendu et QA visuelle. Il reçoit un contenu fonctionnel gelé et ne modifie jamais un claim, un score, un niveau de preuve ou une recommandation.
- Les CV, coordonnées, transcriptions et dossiers privés ne sont jamais versionnés dans ce dépôt public. Résoudre uniquement les actifs de la persona confirmée depuis l’environnement privé ou demander leur fourniture.

## Définition de fini

- La décision reçoit une réponse explicite.
- Les conclusions majeures renvoient à des IDs de preuve.
- Screening, demande entreprise, ICP produit, fit et ciblage personne restent séparés.
- Gouvernance, modèle opératoire, maturité et sourcing sont traités séparément.
- Les relations confirmées et inférées sont distinctes.
- Les inconnues susceptibles de changer le verdict restent visibles.
- Les données privées ne contaminent ni les preuves publiques ni la vérité produit.
- Les intégrations optionnelles peuvent être retirées sans casser le cœur.
- Les validateurs pertinents et les tests d’intégration passent avant livraison.
