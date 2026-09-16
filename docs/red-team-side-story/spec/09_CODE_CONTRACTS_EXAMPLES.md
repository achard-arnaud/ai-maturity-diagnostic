# 09 — Contrats et exemples de code

## 1. Domain models

```python
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Protocol

class EpistemicStatus(str, Enum):
    VERIFIED = "verified"
    VENDOR_CLAIM = "vendor_claim"
    INFERENCE = "inference"
    HYPOTHESIS = "hypothesis"
    UNKNOWN = "unknown"

class IssueStatus(str, Enum):
    OPEN = "OPEN"
    TRIAGED = "TRIAGED"
    PARTIAL = "PARTIALLY_RESOLVED"
    RESOLVED = "RESOLVED"
    WAITING = "WAITING_EVIDENCE"
    PROMOTED = "PROMOTED_TO_ACTION"
    RETIRED = "RETIRED"

@dataclass(frozen=True)
class Lineage:
    claim_ids: tuple[str, ...] = ()
    source_ids: tuple[str, ...] = ()
    issue_ids: tuple[str, ...] = ()
    artifact_paths: tuple[str, ...] = ()

@dataclass(frozen=True)
class Issue:
    issue_id: str
    kind: str
    statement: str
    epistemic_status: EpistemicStatus
    owner_stage: str
    status: IssueStatus
    lineage: Lineage
    can_change_decision: bool = False

@dataclass(frozen=True)
class SideStory:
    side_story_id: str
    kind: str
    status: str
    purpose: str
    payoff: str
    evidence_status: EpistemicStatus
    lineage: Lineage
    section_anchor: str
    return_to: str | None
```

---

## 2. No-proof-from-story invariant

```python
def validate_side_story(story: SideStory) -> list[str]:
    errors = []

    if not story.lineage.claim_ids and not story.lineage.source_ids:
        errors.append("SIDE_STORY_NO_EVIDENCE_LINEAGE")

    if not story.payoff.strip():
        errors.append("SIDE_STORY_NO_PAYOFF")

    if story.status == "promoted" and story.evidence_status == EpistemicStatus.UNKNOWN:
        errors.append("PROMOTED_UNKNOWN_REQUIRES_EXPLICIT_UNKNOWN_RENDER")

    return errors
```

---

## 3. CounterPerspective

```python
@dataclass(frozen=True)
class CounterPerspective:
    cp_id: str
    domain: str
    target: str
    hypothesis: str
    issue_id: str
    can_reverse_decision: bool
    evidence_status: EpistemicStatus = EpistemicStatus.HYPOTHESIS
```

---

## 4. Wedge

```python
@dataclass(frozen=True)
class Wedge:
    wedge_id: str
    prospect_id: str
    proposition: str
    trigger_ids: tuple[str, ...]
    issue_ids: tuple[str, ...]
    side_story_ids: tuple[str, ...]
    cta_kind: str
    status: str
```

---

## 5. Follow-up delta

```python
@dataclass(frozen=True)
class ContactAttempt:
    attempt_id: str
    wedge_id: str
    delta_ids: tuple[str, ...]
    source_ids: tuple[str, ...]
    cta_kind: str

def is_materially_new(previous: ContactAttempt, current: ContactAttempt) -> bool:
    return any([
        current.wedge_id != previous.wedge_id,
        set(current.delta_ids) - set(previous.delta_ids),
        set(current.source_ids) - set(previous.source_ids),
        current.cta_kind != previous.cta_kind,
    ])
```

Changer uniquement le wording ne satisfait pas ce test.

---

## 6. Issue repository port

```python
from typing import Iterable, Protocol

class IssueRepository(Protocol):
    def upsert(self, issue: Issue) -> None: ...
    def get(self, issue_id: str) -> Issue | None: ...
    def list_open(self, *, subject_id: str | None = None) -> Iterable[Issue]: ...
```

Adapters possibles plus tard :

```text
YamlIssueRepository
SqlIssueRepository
ExternalAdminIssueRepository
```

Le domaine ne dépend d'aucun.

---

## 7. Orchestration example

```python
def prepare_reach(context, repos):
    fit = context.fit
    target = context.target

    issues = []

    if not target.current_role_validated:
        issues.append(make_role_issue(target))

    anti_fit = generate_counter_fit(fit, context.evidence)
    if anti_fit:
        issues.append(anti_fit)

    wedge_candidates = build_wedges(
        fit=fit,
        target=target,
        issues=issues,
        triggers=context.newsflow,
    )

    selected = pressure_test_wedges(wedge_candidates)

    return {
        "issues": issues,
        "selected_wedge": selected,
        "status": "ready" if selected else "validate",
    }
```

---

## 8. Side-story selection

```python
def select_side_story(stories, message_budget=1):
    valid = [
        s for s in stories
        if s.status == "promoted"
        and s.payoff.strip()
        and (s.lineage.claim_ids or s.lineage.source_ids)
    ]
    return valid[:message_budget]
```

---

## 9. Loopback event

```python
@dataclass(frozen=True)
class LoopbackEvent:
    event_id: str
    run_id: str
    stage: str
    kind: str
    local_fix: str | None
    reusable_hypothesis: str | None
    recurrence_key: str | None
```

---

## 10. Outcome

```yaml
outcome:
  outcome_id: OUT-...
  attempt_id: MSG-...
  occurred_at: ...
  kind: not_now
  source:
    type: human_recorded
    raw_ref: private
  resolves_issue_ids: [ISS-TIME-...]
  creates_issue_ids: []
  notes: "..."
```

---

## 11. Schema strategy

Chaque nouveau contrat doit :

- déclarer `schema_version`;
- avoir un validator ;
- avoir au moins un fixture positif ;
- avoir au moins deux fixtures négatifs ;
- documenter migration ;
- rester extensible via version plutôt que via `additionalProperties` illimité sur les objets critiques.

---

## 12. Suggested paths

À confirmer après inspection du repo :

```text
contracts/
  issue.schema.yaml
  side_story_business.schema.yaml
  counter_perspective.schema.yaml
  wedge.schema.yaml
  contact_attempt.schema.yaml
  outcome.schema.yaml
  loopback_event.schema.yaml

app/
  issues.py
  side_stories.py
  counter_perspective.py
  outreach_planning.py
  reactivation.py

tests/
  test_issue_contract.py
  test_side_story_business.py
  test_fit_counter_perspective.py
  test_outreach_planning.py
  test_reactivation.py
  test_loopback.py
```

Ne pas créer tous les modules si l'architecture existante offre déjà un owner plus naturel.
