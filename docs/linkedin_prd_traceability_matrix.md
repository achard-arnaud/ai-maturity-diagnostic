# LinkedIn PRD Traceability Matrix

**Design status:** specified
**Runtime status:** deferred / not implemented

| Requirement | Component | Contract / artifact | Verification |
|---|---|---|---|
| LI-FR-001 Capability discovery | future plugin routing skill | capability matrix | unavailable-capability eval |
| LI-FR-002 Approved auth | future app/MCP adapter | connector config | auth negative test |
| LI-FR-003 Read-only | plugin policy | connector evidence | schema `action_class=read` |
| LI-FR-004 Structured evidence | future adapter | `linkedin_connector_evidence.schema.yaml` | schema validation |
| LI-FR-005 Canonical candidate links | future adapter | connector evidence | ID reference test |
| LI-FR-006 Internal IDs remain canonical | merge gate | external identity mapping | architecture test |
| LI-FR-007 Provenance metadata | future adapter | connector evidence | required-fields test |
| LI-FR-008 Retention before persistence | policy gate | data policy | transient-storage test |
| LI-FR-009 Merge gate | future identity layer | relationship observation | no-direct-write test |
| LI-FR-010 Graceful fallback | future routing skill | manual validation result | no-access eval |
| LI-FR-011 Role validation | future validation skill | role validation request | Gold Set precision |
| LI-FR-012 Mismatch detection | future validation skill | connector evidence | mismatch eval |
| LI-FR-013 Audit log | future adapter | private integration audit | audit completeness test |
| LI-FR-014 Optional dependency | global architecture | `AGENTS.md` | plugin-disabled integration test |
| LI-FR-015 Feed only after merge | targeting skill | canonical relationship observation | contamination test |

Le fichier machine-readable `artifacts/linkedin_prd_traceability.yaml` indique pour chaque vérification si elle est contrôlable dès le design, sur le Gold Set ou seulement après implémentation du connecteur. Un test de schéma ne vaut pas validation d’une exigence runtime.
