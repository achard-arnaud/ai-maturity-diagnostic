# PRD — LinkedIn Qualification Plugin v0.1

**Status:** Deferred design / not scheduled
**Decision date:** 2026-07-23
**Primary use case:** Validation de l’identité, de l’employeur et du rôle actuel de contacts déjà connus
**Core-system dependency:** None
**Write actions:** Out of scope

## 1. Problème

Le système v0.3 connaît des personnes, entreprises et relations privées, puis sélectionne les contacts seulement après le product fit. La faiblesse à mesurer est la fraîcheur : les fonctions importées ne sont pas datées, une personne peut avoir changé de rôle ou d’entreprise et un titre ne prouve jamais l’autorité.

Le futur plugin doit répondre à une question étroite :

> Réduire l’incertitude sur l’identité, l’employeur et le rôle actuel d’un contact déjà connu, via une capacité LinkedIn officiellement autorisée, sans transformer LinkedIn en base canonique ni en moteur de prospection.

## 2. Principe produit

LinkedIn est une source externe optionnelle autour du ciblage personne :

```text
person target
-> identity / role uncertainty
-> authorized LinkedIn adapter
-> connector evidence
-> policy + merge gate
-> validated / stale relationship observation
```

Le connecteur ne participe jamais à la recherche de demande entreprise, à l’ICP produit ou au product fit.

## 3. Pourquoi un plugin

La documentation Codex actuelle décrit un plugin comme un package installable pouvant inclure des skills, une app adossée à MCP, une configuration MCP ou ces éléments ensemble. Cette frontière isole les permissions et permet un déploiement ou retrait indépendant du cœur.

Le plugin cible donc, après validation des gates :

```text
linkedin-qualification-adapter/
├── .codex-plugin/plugin.json
├── skills/
│   ├── linkedin-capability-routing/
│   └── linkedin-role-validation/
├── .app.json or .mcp.json
└── references/
    ├── capability_matrix.md
    ├── retention_policy.md
    └── merge_rules.md
```

Cette arborescence est une cible documentaire. Elle ne doit pas être créée avant LI-G3.

Les outils MCP futurs devront décrire fidèlement leurs effets avec les annotations de sécurité OpenAI, notamment `readOnlyHint: true` et aucune indication destructive pour les seules capacités admises en phase 1. L’annotation complète la policy interne `action_class: read`; elle ne la remplace pas.

## 4. Contraintes de plateforme

### Accès LinkedIn

- utiliser uniquement un programme, une licence, des scopes et une authentification explicitement approuvés;
- ne jamais supposer un accès Sales Navigator futur;
- ne pas détourner des données Marketing/Community vers un enrichissement commercial incompatible;
- appliquer les restrictions de stockage propres au programme avant toute persistance.

### Automation

Le scraping, les cookies utilisateur détournés, les extensions navigateur non autorisées et l’automatisation de l’engagement sont exclus.

## 5. Objectifs

1. Confirmer ou invalider une observation personne–entreprise–fonction.
2. Réduire collisions homonymes et erreurs de rattachement.
3. Préserver provenance, date, capacité, programme d’autorisation et limites.
4. Continuer à fonctionner sans accès LinkedIn.
5. Mesurer la valeur incrémentale sur la qualité du ciblage.

## 6. Hors périmètre

- découverte massive de prospects;
- enrichissement générique d’un CRM;
- copie d’une base de profils;
- social listening individuel;
- lead scoring LinkedIn;
- décision de maturité, demande ou product fit;
- inférence automatique de sponsor ou budget owner;
- message, invitation, InMail, commentaire, post ou engagement automatique;
- contournement de restrictions de licence, API ou stockage.

## 7. Utilisateurs

| Utilisateur | Besoin |
|---|---|
| Commercial | Vérifier qu’un contact ciblé est encore pertinent |
| Analyste | Fermer une incertitude avant reach |
| Data steward | Tracer source, statut, rétention et suppression |
| Admin workspace | Contrôler installation, accès et permissions |
| Mainteneur | Désactiver ou remplacer le connecteur sans casser le cœur |

## 8. Exigences fonctionnelles

| ID | Exigence | Priorité |
|---|---|---|
| LI-FR-001 | Capability discovery before any call | Must |
| LI-FR-002 | Approved authentication only | Must |
| LI-FR-003 | Read-only phase 1 | Must |
| LI-FR-004 | Structured connector evidence | Must |
| LI-FR-005 | Evidence linked to internal canonical candidates | Must |
| LI-FR-006 | Internal IDs remain canonical | Must |
| LI-FR-007 | Complete provenance metadata | Must |
| LI-FR-008 | Retention decision before persistence | Must |
| LI-FR-009 | Merge gate before canonical observation | Must |
| LI-FR-010 | Graceful manual fallback | Must |
| LI-FR-011 | Role-validation result with confidence and date | Should |
| LI-FR-012 | Employer or role mismatch detection | Should |
| LI-FR-013 | Audit metadata for every connector call | Must |
| LI-FR-014 | Optional dependency | Must |
| LI-FR-015 | Targeting consumes only post-merge canonical observations | Must |

La matrice exécutable de traçabilité vit dans `artifacts/linkedin_prd_traceability.yaml`.

## 9. Exigences non fonctionnelles

- secrets et payloads privés hors Git;
- minimisation des champs demandés et conservés;
- timestamp pour chaque résultat;
- panne sans corruption du cœur;
- résultat explicable avec limites et confiance;
- traitement idempotent des preuves répétées;
- audit de la capacité, du sujet, du résultat et de la policy;
- moindre privilège;
- retrait du plugin sans incohérence canonique.

## 10. Contrats

### Entrée

`contracts/role_validation_request.schema.yaml` décrit une demande ciblée sur un `person_id` canonique et, si disponible, un `company_id` et un `relationship_id`.

### Sortie connecteur

`contracts/linkedin_connector_evidence.schema.yaml` contient une observation externe, un statut `match | mismatch | unknown | unavailable`, une confiance, les limites et la décision de stockage.

### Merge

`contracts/relationship_observation.schema.yaml` décrit la seule sortie admise du merge gate. Une preuve fournisseur ne remplace jamais silencieusement une relation.

## 11. Hiérarchie de sources

Pour le rôle courant :

1. observation actuelle validée par un humain;
2. système interne approuvé, lorsqu’il existe;
3. preuve actuelle d’un connecteur autorisé;
4. information utilisateur récente;
5. ancien fichier de contacts;
6. inférence.

Une source supérieure crée une nouvelle observation datée; elle n’efface pas la provenance historique.

## 12. Expérience attendue

### Capacité absente

```text
result: manual_validation_required
canonical_change: none
```

### Match autorisé

```text
connector_evidence -> merge review -> canonical relationship observation
```

### Mismatch

```text
expected employer X != observed employer Y
-> stale candidate
-> human review
-> reach blocked pending decision
```

## 13. Gates

| Gate | Condition |
|---|---|
| LI-G0 | Les études réelles démontrent que les rôles obsolètes dégradent matériellement le ciblage |
| LI-G1 | Licence, programme, scopes et disponibilité workspace documentés |
| LI-G2 | Finalités, base légale, rétention, suppression, champs et combinaisons approuvés |
| LI-G3 | POC read-only limité aux capacités explicitement permises |
| LI-G4 | Évaluation contrôlée sur au moins 30 contacts connus |
| LI-G5 | Gain commercial et précision justifient le coût et les contraintes |
| LI-G6 | Toute action d’écriture dispose d’un PRD et ADR séparés |

## 14. Mesures

- identity precision;
- current-role precision;
- employer-mismatch precision;
- false-merge rate;
- stale-data detection rate;
- human-correction rate;
- manual-validation-required rate;
- connector-unavailable rate;
- targeting-decision-change rate;
- incremental target precision.

KPI directeur :

> Incremental improvement in correct contact targeting after company × product fit.

## 15. Déploiement

1. **Phase 0 — actuelle** : aucun connecteur; validation manuelle et mesure du Gold Set.
2. **Phase 1 — design validation** : au moins 30 contacts, stratifiés par cas de fraîcheur et ambiguïté.
3. **Phase 2 — access POC** : uniquement si une capacité officielle existe.
4. **Phase 3 — read-only trial** : petit périmètre, audit actif, aucune écriture.
5. **Phase 4 — production read-only** : après privacy, précision et valeur incrémentale.
6. **Phase 5 — actions éventuelles** : décision produit distincte.

## 16. Décision

Le design est accepté; l’implémentation reste différée. La priorité projet est de produire le Gold Set d’études réelles et de mesurer LI-G0 avant de créer le package plugin.

## 17. Références officielles consultées le 23 juillet 2026

- OpenAI Codex manual — [Build plugins](https://learn.chatgpt.com/docs/build-plugins)
- OpenAI Codex manual — [Build apps](https://learn.chatgpt.com/docs/build-app)
- OpenAI — [Codex manual](https://developers.openai.com/codex/codex-manual.md)
- LinkedIn — [User Agreement](https://www.linkedin.com/legal/user-agreement)
- LinkedIn — [Profile API](https://learn.microsoft.com/en-us/linkedin/shared/integrations/people/profile-api)
- LinkedIn — [Sales Navigator Application Platform](https://learn.microsoft.com/en-us/linkedin/sales/)
- LinkedIn — [Restricted Uses of Marketing APIs and Data](https://learn.microsoft.com/en-us/linkedin/marketing/restricted-use-cases)
