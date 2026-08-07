---
name: corporate-ai-strategy-intelligence
description: Reconstituer la trajectoire corporate d’une entreprise avant d’interpréter ses signaux IA, puis relier priorités financées, moteurs économiques, transformations, capacités requises et preuves d’exécution au rôle réel de l’IA. Utiliser cette skill pour une analyse stratégique, une due diligence ou la passe corporate d’un diagnostic IA complet.
---

# Corporate AI Strategy Intelligence

## Établir la base corporate

1. Fixer l’entité, la période, la géographie et le modèle économique analysés.
2. Prioriser rapports annuels, résultats, présentations investisseurs, plans stratégiques, documents réglementaires et prises de parole de direction.
3. Extraire trois à six priorités assorties d’un objectif, d’un horizon et d’une preuve d’engagement.
4. Identifier croissance, marge, risque, expérience client, innovation, réglementation et transformations préexistantes.
5. Consigner sources et propositions dans `artifacts/01b_evidence_ledger.md`.

Lire [references/corporate-research-method.md](references/corporate-research-method.md) pour coder les signaux et arbitrer le rôle de l’IA.

## Acquisition avancée

Le backend sert à découvrir et trianguler, pas à remplacer les sources corporate primaires :

```bash
python scripts/advanced_research.py "<entreprise> annual results strategy AI transformation" --source web --days 730 --limit 15 --pretty
python scripts/advanced_research.py "<CEO/CIO> <entreprise> AI strategy" --source youtube --days 365 --limit 8 --enrich --pretty
python scripts/advanced_research.py "<entreprise> AI strategy" --source twitter --days 180 --limit 10 --pretty
```

`perplexity` peut accélérer la découverte si une clé first-party existe déjà, mais chaque conclusion structurante doit revenir à un rapport, une présentation investisseurs, une prise de parole datée ou une autre preuve primaire.

## Construire la chaîne d’implication

Pour chaque priorité, rendre explicite :

`priorité → moteur économique/opérationnel → capacité requise → rôle logique de l’IA → rôle déclaré → preuve d’exécution → écart`.

Séparer les capacités data, cloud, processus, produit, talent, contrôle et adoption. Ne pas déduire une stratégie IA d’une liste de cas d’usage ou d’un partenariat isolé.

## Classer le rôle réel de l’IA

Autoriser plusieurs rôles par métier ou horizon :

- pilier stratégique ;
- couche d’activation d’une transformation ;
- programme de productivité ;
- capacité en construction ;
- narration encore faiblement étayée.

Tester chaque rôle avec budgets, responsables, KPI, calendrier, produit en service, utilisateurs ou réplication. Présenter les contre-preuves et un scénario alternatif.

## Produire la sortie

Alimenter `artifacts/02_corporate_strategy.md` et transmettre aux autres passes :

- les priorités et capacités critiques ;
- les owners ou budgets non établis ;
- les transformations antérieures à l’IA ;
- les preuves discriminantes attendues dans leadership, recrutements et newsflow.

Ne proposer qu’une hypothèse préliminaire de maturité : la confirmer avec les preuves d’organisation et de delivery.
