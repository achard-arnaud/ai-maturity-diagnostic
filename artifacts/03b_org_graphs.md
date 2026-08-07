# 03b — Graphes d'organisation et de gouvernance

## Convention

- Remplacer tous les libellés entre crochets.
- Trait plein : relation confirmée ; pointillés : relation inférée.
- Ajouter la source dans le tableau de traçabilité sous chaque graphe.
- Ne jamais inventer une personne, une instance ou un lien hiérarchique.
- Citer les `Claim ID` du registre `01b_evidence_ledger.md`.
- Utiliser une fonction sans titulaire lorsque le nom n'est pas établi.

## Organigramme simplifié

```mermaid
flowchart TB
    EX["Sponsor exécutif"]
    AI["Responsable Data / IA"]
    TECH["Technologie / Plateforme"]
    BU1["Métier / BU A"]
    BU2["Métier / BU B"]
    CTRL["Risque / Juridique / Sécurité"]
    CHANGE["Adoption / Change"]

    EX -->|"mandat confirmé"| AI
    AI --> TECH
    AI -.->|"relation inférée"| BU1
    AI -.-> BU2
    CTRL -.->|"contrôle / challenge"| AI
    CHANGE -.-> BU1

    classDef inferred stroke-dasharray: 5 5;
    class BU1,BU2 inferred;
```

### Traçabilité de l'organigramme

| Relation | Statut | Claim IDs / sources | Raisonnement | Confiance |
|---|---|---|---|---|
| À renseigner | Confirmée / inférée | C000 / S000 | À renseigner | À renseigner |

## Flux de gouvernance

```mermaid
flowchart LR
    IDEE["Opportunité métier"] --> TRI["Qualification valeur / faisabilité"]
    TRI --> ARCH["Revue données / architecture"]
    ARCH --> RISK["Revue risque / conformité / sécurité"]
    RISK --> DEC{Décision}
    DEC -->|Go| BUILD["Build / configuration"]
    DEC -->|Revoir| TRI
    DEC -->|Stop| STOP["Clôture documentée"]
    BUILD --> PROD["Mise en production"]
    PROD --> MON["Suivi valeur, performance et risques"]
    MON --> DEC
```

### Droits de décision

| Étape | Accountable | Responsible | Consulted | Informed | Preuve / confiance |
|---|---|---|---|---|---|
| À renseigner | À renseigner | À renseigner | À renseigner | À renseigner | À renseigner |

## Flux faire / acheter / s'allier

```mermaid
flowchart TB
    NEED["Besoin de capacité IA"] --> Q1{"Différenciation ou actif critique ?"}
    Q1 -->|Oui| MAKE["Faire / posséder"]
    Q1 -->|Non| Q2{"Offre de marché adaptée ?"}
    Q2 -->|Oui| BUY["Acheter / configurer"]
    Q2 -->|Non ou complémentaire| PARTNER["S'allier / co-développer"]
    MAKE --> CONTROL["Contrôles, intégration, mesure de valeur"]
    BUY --> CONTROL
    PARTNER --> CONTROL
    CONTROL --> REVIEW["Réévaluer dépendance, coût et souveraineté"]
```

### Posture par couche

| Couche | Faire | Acheter | S'allier | Propriété / contrôle conservé | Preuve | Confiance |
|---|---|---|---|---|---|---|
| Données | À renseigner | À renseigner | À renseigner | À renseigner | À renseigner | À renseigner |
| Infrastructure / cloud | À renseigner | À renseigner | À renseigner | À renseigner | À renseigner | À renseigner |
| Modèles | À renseigner | À renseigner | À renseigner | À renseigner | À renseigner | À renseigner |
| Orchestration / plateforme | À renseigner | À renseigner | À renseigner | À renseigner | À renseigner | À renseigner |
| Intégration et produits | À renseigner | À renseigner | À renseigner | À renseigner | À renseigner | À renseigner |
| Contrôle et adoption | À renseigner | À renseigner | À renseigner | À renseigner | À renseigner | À renseigner |
