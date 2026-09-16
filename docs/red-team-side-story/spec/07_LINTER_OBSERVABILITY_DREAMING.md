# 07 — Linter, observabilité et Dreaming

## 1. Rôle du linter

Le linter doit rester **plus déterministe que génératif**.

Il vérifie forme, contrat, provenance, états, transitions, interdits, duplication, staleness et boundaries.

Le red-team cherche une cause d'échec. Le dreaming cherche un apprentissage réutilisable.

---

## 2. Linter layers

### Static Contract Linter

```text
MISSING_SOURCE_ID
INVALID_STATUS_TRANSITION
TITLE_USED_AS_AUTHORITY
NEWSFLOW_USED_AS_FIT
SIDE_STORY_WITHOUT_LINEAGE
PROMOTED_SIDE_STORY_WITHOUT_PAYOFF
FOLLOWUP_WITHOUT_NEW_DELTA
SECOND_AUTOMATIC_REPAIR
```

### Semantic Linter

LLM-assisted mais borné :

```text
GENERIC_FIT
SELLER_CENTRIC
WEAK_WHY_NOW
UNSUPPORTED_PAIN
RECYCLED_ANGLE
NO_RETURN_TO_TRUNK
SIDE_STORY_DOMINATES_TRUNK
```

Les semantic findings deviennent `Issue candidates`, pas faits.

---

## 3. Severity

```text
ERROR
WARNING
INFO
```

Hard errors :

- preuve inventée ;
- fuite donnée privée ;
- FAIL hard gate bypass ;
- title-as-authority ;
- invalid promotion ;
- second repair pass ;
- outbound write action non autorisée si la politique actuelle reste inchangée.

Warnings :

- weak angle ;
- stale trigger ;
- low evidence coverage ;
- duplicate side story.

---

## 4. Linter contract

```yaml
finding:
  finding_id: LINT-...
  rule_id: FOLLOWUP_NO_NEW_DELTA
  severity: ERROR
  artifact_id: ...
  path: ...
  message: ...
  autofix_allowed: false
  issue_candidate: true
```

---

## 5. Linter ↔ Issue Engine

```text
finding
→ if deterministic defect:
    fix/block
→ if semantic uncertainty:
    Issue candidate
```

Pour « message trop similaire », V1 peut comparer wedge_id, source IDs, delta IDs et CTA kind avant d'introduire embeddings.

---

## 6. Run observability

```json
{
  "event": "stage.completed",
  "run_id": "RUN-...",
  "stage": "outreach_plan",
  "artifact_id": "ENG-...",
  "metrics": {
    "issue_open": 3,
    "side_story_candidates": 2,
    "side_story_promoted": 1,
    "linter_errors": 0,
    "red_team_verdict": "SURVIVES_WITH_NARROWING"
  }
}
```

Pas besoin d'une stack d'observabilité lourde en V1.

---

## 7. Dreaming tiers

- Tier 0 : `NO_REUSABLE_DELTA`
- Tier 1 : inspection légère du run.
- Tier 2 : pivot, hidden gate, issue structurelle, objection inattendue, successful pattern.
- Tier 3 : cross-run / multi-template.

---

## 8. Dreaming input

```text
red-team events
+
linter recurring findings
+
actual outcomes
+
issue resolution history
+
side-story performance
```

---

## 9. Dreaming delta contract

```yaml
dreaming_delta:
  delta_id: DR-...
  recurrence_key: "followup-no-new-delta"
  observations: 5
  affected_stages: [followup, reactivation]
  proposed_change:
    type: linter_rule
    description: "Require delta_ids on all follow-ups"
  evidence:
    run_ids: [...]
    outcome_ids: [...]
  regression_fixture:
    required: true
  promotion:
    status: candidate
```

---

## 10. Commercial performance telemetry

Ne pas optimiser seulement sur « réponse ».

Mesures :

```text
reply
positive reply
meaningful negative reply
routing success
discovery booked
validation resolved
wrong-person detected
wait signal
reactivation success
retire correctness
```

Une objection explicite est une donnée utile.

---

## 11. Calibration predicted vs actual objection

| predicted | actual | interpretation |
|---|---|---|
| build | timing | timing under-modeled |
| budget | already-solved | capability harvest weak |
| relevance | routed | person selection wrong |
| security | security | good prediction |

Après un volume suffisant, dreaming peut proposer une policy change.

---

## 12. CI/CD

Minimum :

```text
schema validation
→ deterministic linters
→ unit tests
→ fixture tests
→ integration tests
→ no forbidden boundary regression
```

CI échoue si :

- side story sans lineage ;
- follow-up sans delta ;
- objection hypothétique devenue fait ;
- repair budget dépassé ;
- hard gate contourné.
