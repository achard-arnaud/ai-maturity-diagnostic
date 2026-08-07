# LinkedIn Integration Architecture — target state

**Status:** Design accepted; runtime deferred
**Date:** 2026-07-23

## Position architecturale

```text
                         CORE QUALIFICATION
┌───────────────────────────────────────────────────────────────┐
│ network -> enterprise demand -> product fit -> person target │
└──────────────────────────────────┬────────────────────────────┘
                                   │ role_validation_request
                                   v
                      OPTIONAL LINKEDIN PLUGIN
                   ┌────────────────────────────┐
                   │ capability routing         │
                   │ policy check               │
                   │ approved app / MCP adapter │
                   └──────────────┬─────────────┘
                                  │
                                  v
                         connector evidence
                                  │
                         policy / merge gate
                                  │
               ┌──────────────────┴───────────────────┐
               │                                      │
               v                                      v
       relationship observation                 no canonical change
       validated / stale                         + manual validation
```

Interdictions : `matcher -> LinkedIn -> fit` et `provider payload -> people.jsonl overwrite`.

## Trust boundaries

### Zone A — Core private data

`data/private/network/` contient les IDs canoniques et relations observées.

### Zone B — Connector staging

`data/private/integrations/linkedin/` pourra contenir uniquement ce que le programme applicable autorise : audit minimal, liens externes, preuves normalisées et payloads transitoires permis.

### Zone C — Public account evidence

`studies/<account>/sources/` n’accueille pas par défaut les données LinkedIn de contacts privés.

### Zone D — Product truth

`product_catalog/` et `evidence/product/` n’acceptent aucune donnée LinkedIn relative à une personne.

## Séquence future

1. `person-opportunity-targeting` détecte une confiance de rôle insuffisante.
2. Une `role_validation_request` est émise.
3. Le routeur vérifie la capacité réellement disponible.
4. Une capacité absente renvoie `manual_validation_required`.
5. Une capacité autorisée effectue une lecture minimale.
6. La réponse est normalisée en `connector_evidence`.
7. La règle de stockage est appliquée avant persistance.
8. Le merge gate compare la preuve à la relation courante.
9. Il crée une nouvelle observation `validated | stale_candidate | unresolved`, ou aucun changement.
10. Le ciblage peut être rejoué sur l’observation canonique post-merge.

## Failure policy

| Défaillance | Comportement |
|---|---|
| Plugin absent ou désactivé | Validation manuelle |
| Utilisateur non authentifié | Aucun appel |
| Scope indisponible | Capability unavailable |
| API/rate error | État canonique inchangé |
| Identité ambiguë | `unknown`, aucun merge |
| Stockage interdit ou inconnu | Évaluation transitoire uniquement |
| Mismatch observé | Candidat stale, revue humaine |

## Action boundary

Aucune action d’écriture n’appartient à l’interface v0.1. Le design futur ne devra jamais permettre à `engagement-pilot-design` d’invoquer silencieusement une action LinkedIn.
