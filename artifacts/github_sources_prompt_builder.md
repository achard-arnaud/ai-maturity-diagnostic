# Générateur de prompt — Sources GitHub

## Finalité

Construire un prompt de recherche reproductible pour identifier des références GitHub publiques utiles au benchmark du pack. Ne pas utiliser un dépôt tiers comme preuve de la stratégie d'une entreprise sans lien direct et corroboré.

## Cadrage

| Champ | Valeur |
|---|---|
| Objectif du benchmark | À renseigner |
| Composant à améliorer | Master skill / sous-skill / artefact / grille |
| Questions de recherche | À renseigner |
| Types de références | Framework, prompt pack, méthode, template, outil |
| Langues | À renseigner |
| Date de coupure | À renseigner |
| Activité minimale attendue | À renseigner |
| Licences acceptables | À renseigner |
| Exclusions | Dépôts privés, forks sans apport, contenus non traçables |

## Concepts et synonymes

| Concept | Termes principaux | Synonymes / variantes | Exclusions |
|---|---|---|---|
| Stratégie IA | `AI strategy` | `enterprise AI`, `AI operating model` | Tutoriels purement techniques |
| Gouvernance | `AI governance` | `responsible AI`, `model governance` | Politiques sans méthode exploitable |
| Deepsearch | `deep research` | `research agent`, `evidence workflow` | Agents sans discipline de preuve |
| Sourcing | `make buy partner` | `build vs buy`, `vendor strategy` | Comparatifs commerciaux non sourcés |

## Plan de requêtes

| Priorité | Requête ou filtre | Résultat attendu | Risque de bruit |
|---|---|---|---|
| 1 | Termes exacts dans nom, description et README | Références directement pertinentes | Faible |
| 2 | Termes croisés gouvernance + operating model | Méthodes spécialisées | Moyen |
| 3 | Recherche par fichiers `SKILL.md`, `AGENTS.md`, templates | Packs agentiques réutilisables | Moyen |
| 4 | Recherche par organisations ou auteurs reconnus | Validation externe | Biais de notoriété |

## Prompt généré

```markdown
Recherche des dépôts GitHub publics répondant au cadrage ci-dessus. Pour chaque candidat, vérifie l'URL canonique, le propriétaire, la licence, la date de dernière activité, le statut archivé ou actif et les fichiers réellement pertinents. Distingue les faits visibles dans le dépôt de tes inférences. Évalue la pertinence pour le composant ciblé, les éléments réutilisables, les incompatibilités et les risques de licence ou de maintenance. Rejette les forks sans apport et les listes non vérifiables. Restitue une shortlist sourcée puis alimente `artifacts/skill_benchmark_github_references.md`.
```

## Contrôle avant exécution

- [ ] Objectif et composant cible explicites.
- [ ] Date de coupure définie.
- [ ] Critères d'inclusion et d'exclusion vérifiables.
- [ ] Licence et fraîcheur prévues dans l'évaluation.
- [ ] Aucune donnée privée, clé ou information sensible recherchée.
