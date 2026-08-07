---
name: tech-leadership-org-intelligence
description: Reconstituer l’organisation dirigeante, technologique, data, IA et produit d’un groupe multi-entités à partir de sources publiques, avec niveaux de preuve, organigramme analytique, système de décision, RACI hypothétique, fiches de personnes et cartographie d’influence. Utiliser cette skill pour une stratégie de compte, une due diligence, une candidature, une analyse de gouvernance ou la production d’une note DOCX vérifiée visuellement.
---

# Tech Leadership Org Intelligence

## Cadrer la cartographie

Fixer avant recherche : groupe ou société, entités prioritaires, géographies, date de référence, profondeur, fonctions ciblées et décision à éclairer. Traiter le résultat comme une reconstitution analytique datée, jamais comme un organigramme officiel.

Lire :

- [references/research-and-evidence.md](references/research-and-evidence.md) avant la collecte ;
- [references/decision-system-and-deliverable.md](references/decision-system-and-deliverable.md) avant l’analyse et la rédaction ;
- [references/process-reconstruction.md](references/process-reconstruction.md) seulement pour reproduire ou auditer le workflow ISAGRI de référence ;
- `docs/advanced_research_backends.md` avant d’utiliser la couche d’acquisition partagée.

## Rechercher en entonnoir

1. Reconstituer holding, services mutualisés, société principale, filiales, marques et acquisitions.
2. Établir le seed set : gouvernance, direction générale, finance, RH, M&A et dirigeants légaux pertinents.
3. Identifier CTO, CIO/DSI, engineering/R&D, produit, data/IA, cloud, sécurité, architecture, opérations et adoption.
4. Descendre dans les filiales prioritaires selon leur poids dans la décision, la roadmap ou le revenu.
5. Exploiter les offres d’emploi pour révéler équipe, rattachement, stack et transformation, sans les confondre avec une capacité acquise.
6. Auditer uniquement la communication IA publique observée ; écrire `Non trouvé publiquement`, jamais une conclusion sur l’intérêt personnel.

### Acquisition avancée

```bash
python scripts/advanced_research.py "<entreprise> CIO CTO data AI leadership" --source web --days 730 --limit 15 --pretty
python scripts/advanced_research.py "<personne> <entreprise>" --source linkedin --days 730 --limit 10 --pretty
python scripts/advanced_research.py "<personne> <entreprise> AI" --source youtube --days 730 --limit 8 --enrich --pretty
python scripts/advanced_research.py "<entreprise> AI data engineering" --source github --days 365 --limit 10 --pretty
```

Pour LinkedIn, appliquer une hiérarchie **provider-first / public-fallback** : si le host dispose d’un connecteur LinkedIn read-only officiellement approuvé et que les gates `LI-G*` sont ouverts, l’utiliser d’abord. En cas d’absence, refus, panne ou couverture insuffisante, exécuter le runner public ci-dessus (`/pulse/`, `/posts/`, `/in/`). Le fallback peut identifier une piste à vérifier mais jamais établir seul un rôle courant, une identité canonique ou une relation hiérarchique. Les règles `LI-POL-*` restent supérieures aux deux tiers.

## Tenir le registre de preuve

Attribuer des identifiants stables aux sources et personnes. Séparer mandat légal, rôle opérationnel et relation organisationnelle. Appliquer les niveaux : `Confirmé`, `Probable`, `À confirmer`, `Confirmé légal`, ou une qualification explicite équivalente.

Pour une fonction critique sans titulaire établi, conserver la fonction : `DSI Groupe — titulaire non confirmé publiquement`. Ne jamais substituer un ancien titulaire ou un rôle voisin.

## Modéliser le système de décision

Produire :

- structure juridique et portefeuille ;
- registre des personnes ;
- organigramme analytique avec liens pleins confirmés et pointillés inférés ;
- lecture des pouvoirs et questions de qualification ;
- RACI explicitement hypothétique ;
- cartographie d’influence et ordre de contact reliés à l’objectif ;
- contradictions, zones inconnues et preuves discriminantes futures.

Alimenter `artifacts/03_leadership_signals.md`, `03b_org_graphs.md` et `03c_decision_system.md` lorsqu’ils existent.

## Générer un DOCX si demandé

1. Copier `assets/examples/isagri_config.json` et remplacer toutes les données par celles de la mission.
2. Valider puis générer :

```bash
python scripts/build_org_tech_note.py --config <config.json> --validate-only
python scripts/build_org_tech_note.py --config <config.json> --output <note.docx>
```

3. Rendre le DOCX en PDF/PNG avec l’outil DOCX disponible dans l’environnement.
4. Inspecter chaque page : cards non coupées, tableaux lisibles, titres attachés au contenu, graphe lisible, liens cliquables, en-têtes/pieds corrects.
5. Corriger et re-rendre jusqu’à validation complète. Ne pas revendiquer un contrôle visuel si aucun rendu n’a été inspecté.

Les contrats de données sont dans `assets/templates/`. Le DOCX d’exemple est une démonstration de mise en forme, pas une source actuelle sur ISAGRI.

## Portes de qualité

- Revalider les rôles actuels à la date de coupure.
- Sourcer chaque personne et chaque lien organisationnel.
- Trianguler les rôles sensibles et dégrader la confiance en cas de conflit.
- Distinguer explicitement hiérarchie, relation fonctionnelle et hypothèse.
- Ne pas promettre l’exhaustivité de « tous les directeurs » depuis des sources publiques.
- Relier l’influence map à la décision ; ne pas produire un annuaire nominatif décoratif.
- Conserver les inconnues susceptibles de modifier l’approche.
