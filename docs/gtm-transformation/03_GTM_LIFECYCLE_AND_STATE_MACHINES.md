# GTM Lifecycle and State Machines

## Flux principal

`Observed → Screened → Researching → Demand qualified → Fit decided → Targets approved → Reach active → Engaged → Opportunity → Proof/Deal → Expansion/Learning`

Ce flux n'est pas une unique state machine. Chaque objet garde son lifecycle, et les handoffs sont des événements explicites.

## États canoniques

| Objet | États minimaux |
|---|---|
| Signal | new, reviewed, linked, dismissed, expired |
| ResearchCase | queued, active, blocked, review, complete, stale |
| Demand | detected, hypothesized, qualifying, qualified, rejected, stale, archived |
| ProductVersion | draft, review, published, superseded, withdrawn |
| FitAssessment | draft, blocked, validate, pursue, reject, stale, superseded |
| TargetPlan | draft, blocked, review, ready, stale, closed |
| Sequence | draft, approved, active, paused, completed, cancelled |
| Touchpoint | planned, ready, sent, failed, cancelled |
| Engagement | received, classified, action_required, resolved, archived |
| Opportunity | lead, discovery, qualified, proof, proposal, negotiation, won, lost, dormant |
| LearningProposal | observed, drafted, reviewed, accepted, rejected, implemented |

## Transition contract

Chaque transition transporte : objet/version source, état précédent/nouveau, actor, timestamp, reason, evidence refs, policy/gates évalués, idempotency key et correlation ID. Les transitions destructrices sont interdites ; correction et rollback produisent un nouvel événement compensatoire.

## Handoffs critiques

- `ResearchCompleted` peut créer/proposer une Demand, jamais un Fit.
- `DemandQualified + ProductSnapshotPublished` permet de préparer un Fit.
- `FitPursue/Validate` permet de préparer TargetPlan.
- `TargetPlanReady` permet Reach ; currentness expirée rebloque l'envoi.
- `PositiveEngagement/MeetingBooked` peut proposer Opportunity.
- `OpportunityClosed` alimente Learning sans modifier les faits historiques.
