# 08 — Plan d'implémentation BMAD / Full SDLC

## 1. Orientation

Cette évolution doit être menée **contract-first, artifact-first, storage-agnostic**.

Ne pas commencer par créer une DB, un nouveau CRM, une graph DB, refondre le frontend ou créer un agent monolithique.

Commencer par les contrats et les fixtures.

---

# Phase A — Business Analysis

## A1. Inventory

Claude doit inventorier :

- où fit est produit ;
- où target/person est produit ;
- où reach est produit ;
- où engagement hypothesis est produit ;
- où follow-up/stale state existe ;
- où blockers/unknowns sont stockés ;
- quelles sorties sont consommées par l'UI.

Deliverable :

`docs/red-team-side-story/current-state-map.md`

## A2. Gap map

Pour chaque stage :

```text
current input
current output
missing Issue support?
missing SideStory support?
missing red-team?
missing linter?
missing outcome?
```

## A3. Business outcomes

Cibles :

- moins de faux positifs de fit ;
- meilleure qualité de discovery ;
- moins de follow-ups paraphrasés ;
- meilleure réactivation ;
- objections mieux anticipées ;
- apprentissage cross-run.

---

# Phase P — Product / PRD

## P1. Personas système

- analyst/research agent ;
- qualification agent ;
- reach agent ;
- human reviewer ;
- salesperson/user ;
- QA/dreaming agent.

## P2. Functional requirements

- FR-001 Issue lifecycle
- FR-002 SideStory lifecycle
- FR-003 CounterPerspective on fit
- FR-004 ObjectionSimulation on outreach
- FR-005 Followup delta gate
- FR-006 Reactivation delta engine
- FR-007 System Red-Team bounded repair
- FR-008 Linter separation
- FR-009 Outcome capture
- FR-010 Dreaming aggregation

## P3. Non-functional

- traceability ;
- no evidence contamination ;
- storage abstraction ;
- idempotence ;
- low operational burden ;
- no mandatory external integration ;
- auditability ;
- rollback.

---

# Phase A — Architecture

## ADR-001 — shared contracts, specialized policies

Créer un noyau léger, noms à adapter après harvest réel :

```text
domain/
  issues.py
  side_stories.py
  counter_perspectives.py
  loopback.py
```

Puis policies :

```text
policies/
  fit.py
  reach.py
  outreach.py
  followup.py
  reactivation.py
```

Ne pas créer un `red_team_engine.py` qui fait tout.

## ADR-002 — ports

```python
from typing import Protocol

class IssueRepository(Protocol):
    def save(self, issue): ...
    def list_for_subject(self, subject_ref): ...

class OutcomeRepository(Protocol):
    def append(self, outcome): ...
```

L'implémentation de stockage sera décidée séparément.

## ADR-003 — artifact adapters

V1 :

- YAML/MD existants ;
- deterministic projections ;
- no second source of truth.

## ADR-004 — stable IDs

```text
ISS-
CP-
SS-
RT-
LB-
DELTA-
OUT-
WDG-
```

---

# Phase E — Epics

## Epic 1 — Contracts & Linter

Stories :

1. Issue schema.
2. SideStory business schema.
3. CounterPerspective schema.
4. RedTeamReview schema.
5. LoopbackEvent schema.
6. Deterministic linters.
7. Fixtures.

Exit : **no runtime behavior change**.

## Epic 2 — Fit / Targeting

1. Generate anti-fit issue.
2. Preserve positive fit.
3. Add validation questions.
4. Add wedge readiness.
5. Extend target qualification.

Exit : current fit behavior backwards compatible.

## Epic 3 — Reach / Outreach planning

1. ObjectionSimulation.
2. Wedge candidates.
3. Gatekeeper route policy.
4. message plan contract.
5. no outbound send.

Exit : only planning artifacts.

## Epic 4 — Follow-up / Reactivation

1. outcome state.
2. stale detection.
3. delta detection.
4. callback side story.
5. follow-up delta linter.

## Epic 5 — System Red-Team / Loopback

1. bounded red-team.
2. repair budget.
3. loopback event.
4. dreaming aggregation.
5. regression promotion gates.

---

# Phase D — Development Stories

Chaque story contient :

```text
context
input contract
output contract
invariants
code paths
negative cases
tests
migration
rollback
observability
```

Exemple :

### STORY-FUP-003 — Reject paraphrase follow-up

```gherkin
Given a prior outreach with wedge W1, sources S1 and CTA C1
When a follow-up candidate reuses W1, S1 and C1
And no new delta_id is present
Then linter emits FOLLOWUP_NO_NEW_DELTA
And the candidate cannot be promoted
```

---

# Phase Q — QA

## Contract tests
Schemas.

## Unit tests
Pure policies.

## Integration tests
Fit → target → reach → outreach.

## Regression fixtures

Au moins :

1. high fit / low authority ;
2. high fit / strong anti-fit ;
3. gatekeeper route ;
4. no-response without delta ;
5. sector RETEX reactivation ;
6. post-based callback ;
7. red-team pivot ;
8. side-story lineage failure.

## Mutation tests conceptuels

Retirer volontairement source IDs, issue IDs, delta IDs, return_to ou hard gate et vérifier que CI échoue.

---

# Phase R — Release

Feature flags :

```text
ISSUE_ENGINE_V1
SIDE_STORY_BUSINESS_V1
FIT_COUNTER_PERSPECTIVE_V1
OUTREACH_SIMULATION_V1
REACTIVATION_V1
DREAMING_LOOPBACK_V1
```

Rollout :

```text
fixture
→ dry-run
→ shadow output
→ human comparison
→ limited active
→ general
```

---

# Phase O — Operate / Learn

Monitor :

- issue resolution rate ;
- unused side stories ;
- wedge conversion ;
- repeat-message block rate ;
- predicted vs actual objections ;
- red-team pivots ;
- dreaming deltas promoted/rejected.

---

## 10. PR sequencing recommandé

### PR-1 Contracts only
No business change.

### PR-2 Issue Engine + deterministic linter
No message generation.

### PR-3 Fit Counter-Perspective
Shadow mode.

### PR-4 SideStory adapter
Notes + engagement hypotheses.

### PR-5 Wedge + ObjectionSimulation
Planning only.

### PR-6 Follow-up / Reactivation
Still no automatic outbound.

### PR-7 Outcomes + Dreaming
Learning loop.

### PR-8 UI projections
Only after contracts stable.

---

## 11. Definition of Done SDLC

- PRD approved ;
- ADRs explicit ;
- schemas versioned ;
- backwards compatibility tested ;
- migration path ;
- rollback path ;
- CI green ;
- fixtures include negative paths ;
- no hidden storage dependency ;
- no automatic outbound ;
- no evidence promotion by storytelling ;
- no system self-modification without promotion gate.
