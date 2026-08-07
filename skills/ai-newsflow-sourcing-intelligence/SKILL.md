---
name: ai-newsflow-sourcing-intelligence
description: Analyser le newsflow IA récent pour distinguer narration et exécution, mesurer l’évolution de la trajectoire et inférer gouvernance, maturité et posture faire, acheter ou s’allier par couche de capacité. Utiliser cette skill pour croiser annonces, partenariats, lancements, déploiements, nominations et recrutements dans une analyse stratégique.
---

# AI Newsflow Sourcing Intelligence

## Construire la chronologie

1. Fixer la date de coupure, six mois prioritaires et six mois de contexte, sauf justification.
2. Couvrir communications corporate et investisseurs, partenaires nommés, produits, cloud/data, nominations, recrutements et validations externes.
3. Dédupliquer les reprises d’un même événement.
4. Séparer systématiquement date d’annonce, de lancement, de mise en production et de résultat observable.
5. Enregistrer sources et propositions dans `artifacts/01b_evidence_ledger.md`.

Lire [references/newsflow-sourcing-method.md](references/newsflow-sourcing-method.md) pour coder les événements et la posture de sourcing.

## Acquisition avancée

Utiliser le backend selon le type de signal, sans confondre rang de recherche et force de preuve :

```bash
python scripts/advanced_research.py "<entreprise> artificial intelligence partnership deployment" --source web --days 180 --limit 15 --pretty
python scripts/advanced_research.py "<entreprise> AI" --source twitter --days 90 --limit 10 --pretty
python scripts/advanced_research.py "<entreprise> AI" --source youtube --days 180 --limit 8 --enrich --pretty
python scripts/advanced_research.py "<entreprise> AI" --source github --days 180 --limit 10 --pretty
python scripts/advanced_research.py "<entreprise> AI" --source hackernews --days 180 --limit 10 --pretty
```

Ajouter `arxiv` pour une trajectoire R&D et `perplexity` comme discovery lane lorsque pertinent. Toujours revenir à l’annonce corporate, au partenaire nommé, au dépôt, au papier ou à la source primaire avant de qualifier un événement comme preuve d’exécution.

## Interpréter chaque événement

Traiter quatre angles obligatoires :

1. priorité stratégique servie ;
2. owner, décision et contrôle ;
3. actifs faits, achetés ou co-développés ;
4. stade démontré : annonce, pilote, production, réplication ou échelle.

Identifier ce que l’entreprise conserve : données, orchestration, modèles, intégration, propriété intellectuelle, contrôle, distribution et adoption. Un partenariat ne vaut pas déploiement ; une annonce partenaire n’établit pas l’appropriation interne.

## Tester le momentum

Qualifier accélération, stabilité, recentrage, ralentissement ou non établi à partir de plusieurs types de signaux. Comparer owners/budgets, production, réplication, plateforme/run, contrôles, mesure de valeur et recrutements cohérents.

Tester convergences et contradictions entre corporate, leadership, hiring, partenaires et résultats. Évaluer le renforcement de la gouvernance séparément de la maturité de delivery.

## Produire la sortie

Alimenter `artifacts/05_newsflow_make_or_buy.md` avec une chronologie courte, la matrice à quatre angles, la posture par couche, le test de momentum, les contradictions et une watchlist à 90 jours.

Ne pas confondre volume médiatique, nouveauté et matérialité stratégique.
