# Learning Loop, Observability and QA

## Quatre boucles distinctes

- QA : vérifier qu'une sortie respecte contrats et acceptance.
- Red-team : contester une conclusion ou un choix.
- Retrospective : expliquer incidents, friction, coûts et rework.
- Dreaming/loopback : proposer une amélioration de capability, prompt, contrat ou UX.

Elles ne partagent pas un statut générique et aucune ne mute automatiquement la skill.

## Télémétrie minimale

Funnel : screened, researched, demand-qualified, fit-pursue, targets-ready, reached, engaged, opportunity, proof, won/lost.

Qualité : provenance coverage, stale ratio, gate overrides, rework, false positives, reviewer disagreement, NRT drift.

Économie : appels, tokens, coût, cache hit, coût par dossier/fit/opportunity, rate-limit blocks.

Exécution : queue age, time-in-state, error/retry, touchpoint outcomes, resolver completion.

## Test pyramid

- Schema/property tests pour objets et transitions.
- Unit tests pour gates, scoring, idempotence et permissions.
- Contract tests pour API/handoffs/adaptateurs.
- Integration tests par bounded context.
- E2E sur journeys de valeur et isolation workspace.
- Gold sets/evals pour claims, demand, fit, targeting et engagement classification.
- NRT transversal avant chaque merge `dev → main`.

## Learning proposal

Toute proposition décrit signal, cohorte, métrique, hypothèse, changement, risque, owner, test, rollback et résultat. Acceptance humaine obligatoire avant modification du système gouvernant.
