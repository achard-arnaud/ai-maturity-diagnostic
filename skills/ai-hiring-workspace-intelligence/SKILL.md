---
name: ai-hiring-workspace-intelligence
description: Interpréter un corpus daté et dédupliqué d’offres d’emploi, pages carrières et signaux de recrutement pour inférer l’équipe, le delivery, la gouvernance, la plateforme, l’adoption, la maturité et le sourcing IA. Utiliser cette skill pour analyser le modèle opératoire visible par le recrutement ou pour la passe hiring d’un diagnostic de stratégie IA.
---

# AI Hiring Workspace Intelligence

## Constituer le corpus

1. Fixer une fenêtre prioritaire de six mois et une fenêtre de contexte de six mois supplémentaires, sauf justification sectorielle.
2. Rechercher d’abord le site carrière officiel, puis plateformes, cabinets et profils publics pertinents.
3. Capturer URL, titre, entité, lieu, date de première et dernière observation, statut et texte utile.
4. Dédupliquer les republications par titre, localisation, description, identifiant et temporalité.
5. Quantifier offres uniques, expirées, anonymes et doublons avant toute interprétation.

Lire [references/hiring-corpus-method.md](references/hiring-corpus-method.md) pour l’extraction et les tests d’inférence.

## Acquisition avancée

Utiliser `scripts/advanced_research.py` comme couche de découverte, puis revenir aux pages carrière et descriptions officielles avant de renforcer un claim :

```bash
python scripts/advanced_research.py "<entreprise> AI data careers hiring" --source web --days 365 --limit 15 --pretty
python scripts/advanced_research.py "<entreprise> AI hiring data platform" --source linkedin --days 365 --limit 12 --pretty
```

La voie LinkedIn est un index public, pas un connecteur. Un snippet de profil ou de post ne prouve ni rôle courant, ni rattachement, ni capacité acquise. Conserver `metadata.acquisition_method` et les `limitations` avec le corpus.

## Extraire les signaux

Coder pour chaque offre : finalité, séniorité, sponsor ou rattachement, équipe d’accueil, interactions, métiers et géographies, delivery, gouvernance, data/IA/cloud, plateforme et run, adoption, risque/sécurité/conformité et indices faire/acheter/s’allier.

Séparer :

- exigence générique du métier ;
- indice distinctif de l’entreprise ;
- information absente ;
- capacité recherchée, capacité recrutée et capacité déployée.

## Inférer le workspace

Raisonner à partir de grappes, séquences et cooccurrences, jamais d’un mot-clé isolé. Tester si le corpus indique une équipe centrale, une factory, un hub-and-spoke, une fédération, des équipes produit embarquées ou de l’externalisation.

Croiser les résultats avec dirigeants, partenariats, architecture annoncée et cas en production. Évaluer la gouvernance séparément du stade de delivery.

## Produire la sortie

Alimenter `artifacts/04_hiring_workspace_intelligence.md` avec : corpus et biais, motifs récurrents, modèle d’équipe et de collaboration, delivery/run, technologie, gouvernance, adoption, sourcing, maturité probable, contre-signaux et confiance.

Ne pas livrer une liste d’offres. Ne jamais présenter une offre ouverte comme une capacité acquise.
