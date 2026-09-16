# 01 — System Red-Team, QA et Loopback technique

## 1. But

Le `System Red-Team` est un mécanisme de **falsification de run**. Il ne doit pas être confondu avec une objection commerciale, un angle de storytelling, une side story, un simple linter ou un moteur de génération.

Il intervient lorsque la qualité d'une décision, d'un run ou d'un handoff doit être challengée.

---

## 2. Trois couches de revue

### 2.1 Conformance QA
Déterministe autant que possible : schema, champs obligatoires, source IDs, staleness, hard gates, transitions d'état, contamination entre artefacts, `title != authority`, `newsflow != fit`, invariants privacy/storage.

### 2.2 System Red-Team
Question :

> Quel est le meilleur contre-cas capable de renverser la décision actuelle ?

Attaques privilégiées : wrong framing, missing baseline, category mismatch, hidden gate, evidence asymmetry, stale evidence, control migration, operational burden, reversibility, role/authority inference, optimistic causal chain.

### 2.3 Reader / Decision QA
Question :

> Le consommateur aval comprend-il décision, incertitude, falsifier et prochaine action ?

---

## 3. Machine d'état

```text
DRAFT_DECISION
→ CONFORMANCE_CHECKED
→ RED_TEAM_SELECTED
→ RED_TEAM_EXECUTED
→ {
    SURVIVES,
    NARROW,
    PIVOT,
    REOPEN_TARGETED
  }
→ REPAIR? (0..1)
→ VERIFY? (0..1)
→ DELIVERABLE
→ LOOPBACK_EVENT
```

Hard rule : **une correction maximum + une vérification maximum par run normal**. Un second échec matériel devient `REOPEN_TARGETED` ou escalade Tier 3.

---

## 4. Contrat de review

```yaml
red_team_review:
  review_id: RT-...
  run_id: RUN-...
  scope:
    artifact_id: optional
    decision_id: optional
    stage: fit|targeting|reach|outreach|followup|reactivation|render|other
  target:
    proposition: "..."
    evidence_ids: []
    assumption_ids: []
  attack:
    lens: missing_baseline
    hypothesis: "..."
    disconfirming_evidence_ids: []
    unknown_ids: []
  verdict:
    enum:
      - SURVIVES_RED_TEAM
      - SURVIVES_WITH_NARROWING
      - PIVOT_REQUIRED
      - REOPEN_TARGETED
  repair:
    required: true
    repair_kind: scope_narrowing
    max_passes: 1
  verification:
    status: PASS|FAIL|NOT_RUN
  loopback:
    emit_event: true
    event_kind: hard_gate_discovery
```

---

## 5. Sélection adaptative de profondeur

- **QA-Lite** : une seule proposition attaquée.
- **QA-Decision** : décision + hypothèse principale + baseline/no-action.
- **QA-High** : winner/path + strongest alternative + native baseline + hard gate + reversibility.

---

## 6. Run monitoring

```json
{
  "run_id": "RUN-2026-09-15-001",
  "stage": "reach",
  "red_team": {
    "triggered": true,
    "verdict": "SURVIVES_WITH_NARROWING",
    "repair_count": 1,
    "verification": "PASS"
  }
}
```

Métriques : taux de runs challengés, taux de décision modifiée, narrowing vs pivot, réouvertures, défauts récurrents, coût de review, taux d'objections artificielles sans impact.

---

## 7. Relation Red-Team ↔ Dreaming

```text
RedTeam finding
→ LoopbackEvent
→ aggregation
→ Dreaming
→ CandidateDelta
→ regression test
→ human promotion
```

Exemple :

```yaml
loopback_event:
  event_id: LB-042
  kind: evidence_gap
  stage: fit
  local_fix: "requalifier le fit"
  reusable_hypothesis:
    "avant toute recommandation build/buy, faire un capability-harvest de l'existant"
  recurrence_key: "missing-existing-capability"
```

Une erreur locale peut légitimement produire `NO_REUSABLE_DELTA`.

---

## 8. Code de référence

```python
from dataclasses import dataclass
from enum import Enum
from typing import Sequence

class Verdict(str, Enum):
    SURVIVES = "SURVIVES_RED_TEAM"
    NARROW = "SURVIVES_WITH_NARROWING"
    PIVOT = "PIVOT_REQUIRED"
    REOPEN = "REOPEN_TARGETED"

@dataclass(frozen=True)
class Attack:
    lens: str
    hypothesis: str
    evidence_ids: tuple[str, ...] = ()
    unknown_ids: tuple[str, ...] = ()

@dataclass(frozen=True)
class RedTeamResult:
    verdict: Verdict
    rationale: str
    repair_kind: str | None = None
    reopen_scope: str | None = None

def apply_bounded_red_team(
    proposition: str,
    attacks: Sequence[Attack],
) -> RedTeamResult:
    material = [a for a in attacks if a.evidence_ids or a.unknown_ids]
    if not material:
        return RedTeamResult(
            verdict=Verdict.SURVIVES,
            rationale="No decision-relevant counter-evidence."
        )
    raise NotImplementedError("Evaluation delegated to governed reviewer")
```

La fonction pure ne connaît ni stockage ni UI.

---

## 9. Tests minimum

- no material attack → `SURVIVES_RED_TEAM`;
- material but bounded → `SURVIVES_WITH_NARROWING`;
- premise invalidated → `PIVOT_REQUIRED`;
- one dimension invalidated → `REOPEN_TARGETED`;
- repair pass 2 rejected;
- red-team output cannot mutate evidence status;
- red-team may create `Issue`, not `Fact`.
