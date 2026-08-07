# Recherche GitHub — patterns retenus pour les skills

## Statut de cette note

Cette synthèse reprend la recherche et les liens fournis par le commanditaire le 23 juillet 2026. Les dépôts n’ont pas été revérifiés pendant l’implémentation locale; traiter les conclusions externes comme attribuées à cette source jusqu’à une prochaine passe de veille.

## Sources principales

1. [Agent Skills specification — agentskills/agentskills](https://github.com/agentskills/agentskills)
   - standard ouvert;
   - chargement progressif metadata -> `SKILL.md` -> ressources;
   - séparation scripts, references et assets.
2. [Anthropic skills](https://github.com/anthropics/skills), notamment [skill-creator](https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md)
   - description comme mécanisme de triggering;
   - tests `should_trigger` et `should_not_trigger`;
   - détails déplacés dans `references/`.
3. [OpenAI skills](https://github.com/openai/skills), notamment [skill-creator](https://github.com/openai/skills/blob/main/skills/.system/skill-creator/SKILL.md)
   - séparation `scripts/`, `references/`, `assets/`;
   - absence de duplication entre procédure et références;
   - scripts réservés aux opérations déterministes et répétitives.
4. [GitHub Copilot — Agent Skills](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills)
   - skills de projet et personnelles;
   - ressources additionnelles associées;
   - prudence sur les outils shell pré-approuvés.
5. [sales-skills/sales](https://github.com/sales-skills/sales)
   - routeur mince;
   - séquençage de skills propriétaires;
   - séparation prospecting, research, discovery, lead scoring, account mapping et proposal.

## Patterns appliqués

### P1 — Thin router

Identifier l’étape, vérifier l’artefact, choisir la skill propriétaire et refuser l’analyse métier.

### P2 — One responsibility per skill

Séparer recherche demande, vérité produit, matching et pilote.

### P3 — Progressive disclosure

Garder procédure et frontières dans `SKILL.md`; déplacer taxonomies, scoring et policies dans `references/`.

### P4 — Product data is not skill logic

Versionner les offres dans `product_catalog/`.

### P5 — Account data is not product data

Conserver les preuves compte sous `studies/<account>/`.

### P6 — Contract-based handoff

Échanger par fichiers structurés versionnés, jamais par contexte implicite.

### P7 — Trigger evals

Tester déclenchement, non-déclenchement et collisions après toute modification significative de `description`.

### P8 — Reasoning evals

Tester faux positif IA, gate bloquant, besoin humain, gouvernance PMO, besoin spécifique, fit Astraforge, preuve faible, contradiction et mise à jour post-discovery.
