# Route, Context and API Model

## Routes UI

`/w/{workspace_slug}/{space}` puis deep links `/w/{workspace_slug}/{space}/{object_id}`. Le workspace demandé reste un sélecteur ; l'autorité vient de la membership vérifiée.

## API v1

```text
/api/v1/workspaces/{workspace_id}/signals
/api/v1/workspaces/{workspace_id}/companies
/api/v1/workspaces/{workspace_id}/research-cases
/api/v1/workspaces/{workspace_id}/demands
/api/v1/workspaces/{workspace_id}/product-snapshots
/api/v1/workspaces/{workspace_id}/fit-assessments
/api/v1/workspaces/{workspace_id}/target-plans
/api/v1/workspaces/{workspace_id}/sequences
/api/v1/workspaces/{workspace_id}/engagement-events
/api/v1/workspaces/{workspace_id}/opportunities
```

## Contrats

- Command/query separation légère : GET lit une projection, POST/PATCH émet une commande validée.
- Toute mutation accepte `Idempotency-Key`; toute édition concurrente utilise version/ETag.
- Pagination cursor, filtres et tris sont explicites ; aucun payload illimité.
- Erreurs stables : code, message sûr, request_id, retryable, resolver éventuel.
- `RequestContext` et `WorkspacePaths` sont obligatoires sur toute route protégée.
- Les routes legacy `/api/...` restent des façades de compatibilité jusqu'à E12.

## Context propagation

`request_id`, `correlation_id`, `workspace_id`, `actor_id`, `role`, `route`, `object refs`, `budget envelope` traversent HTTP → service → skill/job → audit/event. Aucun modèle métier n'importe FastAPI.
