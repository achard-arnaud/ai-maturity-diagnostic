# Canonical Object and Event Model

## Entités

`Person`, `Company`, `Relationship`, `Signal`, `SavedSearch`, `List`, `ResearchCase`, `Claim`, `Demand`, `Product`, `ProductVersion`, `ProductSnapshot`, `FitAssessment`, `TargetPlan`, `StakeholderRole`, `Sequence`, `Task`, `Touchpoint`, `Conversation`, `EngagementEvent`, `Lead`, `Opportunity`, `Proof`, `Deal`, `Expansion`, `LearningProposal`.

## Relations cardinales

- Company possède plusieurs ResearchCases, Demands, Opportunities et Signals.
- Demand appartient à un compte et référence plusieurs Claims/Evidence.
- Product possède des ProductVersions ; une version publiée produit un ou plusieurs snapshots immuables.
- FitAssessment relie exactement une version de Demand à exactement un ProductSnapshot.
- TargetPlan référence un FitAssessment accepté et plusieurs personnes/roles.
- Sequence instancie un TargetPlan ; Touchpoint appartient à une séquence et une personne/canal.
- EngagementEvent référence un touchpoint/conversation lorsqu'ils sont connus.
- Opportunity agrège des décisions mais conserve les refs vers fit/targets/engagement.

## Enveloppe commune

```yaml
id: stable-id
workspace_id: ws-id
schema_version: semver
version: integer
status: lifecycle-state
created_at: iso-8601
updated_at: iso-8601
created_by: actor-ref
provenance: []
source_artifacts: []
supersedes: null
```

## Events prioritaires

`SignalObserved`, `ResearchQueued`, `ClaimValidated`, `DemandQualified`, `ProductSnapshotPublished`, `FitDecided`, `TargetPlanApproved`, `TouchpointSent`, `EngagementReceived`, `OpportunityOpened`, `ProofCompleted`, `DealClosed`, `LearningProposed`.

## Décision de persistance

Les artefacts YAML/Markdown demeurent canon. Le store runtime maintient IDs, index, sessions, audit, quotas, locks, idempotency et projections. Un Event Journal append-only est introduit avant toute base relationnelle métier ; SQL métier n'est envisagé qu'après mesure de volume, requêtes ou concurrence.
