# 01b — Registre central des sources et propositions

## Sources

| Source ID | Type | Titre | Émetteur | Date du fait / publication | Consultation | Référence | Limites |
|---|---|---|---|---|---|---|---|
| S001 | Direction owner / synthèse | Refonte v0.2 — Astraforge comme tunnel de qualification | Utilisateur | 2026-07-23 | 2026-07-23 | Pièce jointe `13a3e4c3…/pasted-text.txt` | Synthèse dérivée; références web non revérifiées dans cette mission |
| S002 | Direction owner | Astraforge — Pitch et positionnement v0.2 | Utilisateur | 2026-07-23 | 2026-07-23 | Pièce jointe `9c9240fc…/pasted-text.txt` | Thèses de différenciation encore à prouver |
| S003 | Direction owner / audit | Qualification Tunnel v0.2 — Architecture et audit de la v0 | Utilisateur | 2026-07-23 | 2026-07-23 | Pièce jointe `8d9f145d…/pasted-text.txt` | Diagnostic de conception fourni par le commanditaire |
| S004 | Profil produit dérivé | Astraforge OFFER-AF-01 v0.2 | Utilisateur | 2026-07-23 | 2026-07-23 | Pièce jointe `f22d4478…/pasted-text.txt` | Capacités majoritairement `P2`; plusieurs inconnues critiques |
| S005 | Cahier des charges | Patterns, migration, contrats, evals et scripts v0.2 | Utilisateur | 2026-07-23 | 2026-07-23 | Message de mission | Contenu normatif; ne constitue pas une preuve de capacité produit |
| S006 | Fichier privé utilisateur | Réseau de contacts — Name, Job title, Company, Country | Utilisateur | Non daté | 2026-07-23 | Pièce jointe `7f004de9…/pasted-text.txt` | 1 308 lignes complètes; fonctions non datées et non vérifiées |
| S007 | Référentiel officiel | Industry Classification Benchmark (Equity), v5.0 | FTSE Russell / LSEG | Mars 2026 | 2026-07-23 | `https://www.lseg.com/content/dam/ftse-russell/en_us/documents/ground-rules/icb-ground-rules.pdf` | P1 pour la taxonomie et ses règles; ne classe pas automatiquement les entreprises du réseau |
| S008 | Direction owner / recherche de conception | Références Agent Skills et patterns de routeur | Utilisateur | 2026-07-23 | 2026-07-23 | Dépôts Agent Skills, Anthropic, OpenAI, sales-skills et documentation GitHub fournis dans la mission | Sert à l’architecture des skills; evals de triggering non rejouées par modèle |
| S009 | Direction owner / contraintes intégration | PRD, ADR et matrice de traçabilité LinkedIn différés | Utilisateur | 2026-07-23 | 2026-07-23 | Matériau de mission LinkedIn | Conception uniquement; aucun accès ni connecteur validé |
| S010 | Observation locale | Audit adverse et gate de release v0.3 | Mainteneur du dépôt | 2026-07-23 | 2026-07-23 | Tests et scripts du dépôt | Prouve la cohérence logicielle locale, pas la performance commerciale |

## Propositions

| Claim ID | Proposition atomique | Statut | Portée | Sources | Contre-preuves | Confiance et motif | Consommateurs |
|---|---|---|---|---|---|---|---|
| C001 | Le tunnel doit séparer la réalité du compte de la vérité produit jusqu’au matching | Fait de conception | Architecture v0.2 | S001, S003, S005 | — | Élevée — direction répétée | Skills, contrats, docs |
| C002 | Le routeur ne doit effectuer aucune analyse métier | Fait de conception | Router | S001, S003, S005 | — | Élevée | Router, evals |
| C003 | Les quatre offres doivent être versionnées dans des fichiers indépendants | Fait de conception | Catalogue | S001, S003, S005 | — | Élevée | Catalogue, init |
| C004 | Une étude doit conserver des snapshots produit immuables | Fait de conception | Auditabilité | S001, S003, S005 | — | Élevée | Init, validate-study |
| C005 | Les primitives sandbox, multi-agent et skills ne suffisent pas seules à différencier Astraforge | Hypothèse stratégique | Produit Astraforge | S001, S002, S004 | Recherche concurrentielle non rejouée | Moyenne — matériau cohérent mais validation externe non refaite | Profil Astraforge, pitch |
| C006 | Astraforge cible un goulot collectif instrumentable après adoption préalable d’agents | Hypothèse produit | ICP Astraforge | S002, S004 | Preuves clients externes non établies | Moyenne | Profil Astraforge, matcher |
| C007 | Les capacités Astraforge listées ne dépassent pas `P2` avec les preuves disponibles | Inférence | Produit Astraforge | S004 | Documentation primaire complète absente | Moyenne à élevée | Catalogue, registre produit |
| C008 | Les descriptions de frontmatter sont le principal mécanisme de découverte à tester | Fait de méthode attribué | Conception des skills | S001, S005 | Références web non revérifiées | Moyenne | Skills, evals |
| C009 | Le fichier contient 1 308 personnes et 664 libellés d’entreprise bruts, tous associés au pays France | Fait | Intake réseau | S006 | — | Élevée — décompte déterministe | Intake, screening |
| C010 | Le fichier ne permet pas d’établir l’actualité des fonctions ni l’autorité décisionnelle | Fait / limite | Relations personnes–entreprises | S006 | — | Élevée — aucun champ de date ou mandat | Ciblage, reach |
| C011 | L’ICB v5.0 contient 11 industries, 20 supersectors et 45 sectors avant le niveau subsector | Fait | Taxonomie | S007 | — | Élevée — source officielle | Mapping, sector rollups |
| C012 | Une classification ICB doit suivre l’activité génératrice de revenus et non le titre d’un contact | Fait méthodologique | Mapping | S007 | — | Élevée | Skill ICB, validateur |
| C013 | Un nom seul fusionnait à tort des homonymes inter-entreprises | Fait logiciel reproduit | Intake réseau | S010 | — | Élevée — test adverse | Import, migration, validation |
| C014 | Un score réseau non numérique passait avant durcissement du validateur | Fait logiciel reproduit | Contrats réseau | S010 | — | Élevée — test adverse | Validateur réseau |
| C015 | Une décision top-level pouvait diverger du match sélectionné et alimenter le ciblage/reach | Fait logiciel reproduit | Coordination commerciale | S010 | — | Élevée — test adverse | Fit, ciblage, reach |
| C016 | Les candidats ICB `N0` peuvent soutenir une vue exploratoire mais pas une vue décisionnelle | Règle de conception | Consolidation sectorielle | S007, S010 | — | Élevée | Rollups, contrat secteur |
| C017 | Le gate local de release passe sur structure, tests, schemas, liens, confidentialité, DOCX et réseau privé | Fait logiciel | Milestone v0.3 | S010 | CI distante non encore observée | Élevée localement | Release |

## Conflits et limites

| ID | Sujet | Tension | Traitement |
|---|---|---|---|
| CF001 | Différenciation Astraforge | Le positionnement affirme une couche d’industrialisation, mais la supériorité concurrentielle n’est pas prouvée | Conserver comme hypothèse et lister les validations requises |
| CF002 | Validation annoncée dans S001 | S001 indique zéro erreur, mais le package n’existait pas dans ce dépôt au démarrage | Rejouer toutes les validations localement avant toute annonce |

## Couverture

| Sujet | Couverture | Résultat | Limite |
|---|---|---|---|
| Architecture cible | S001–S005 | Établie comme direction owner | Pas une validation marché |
| Vérité produit Astraforge | S002, S004 | Partiellement établie | Références, prix, architecture et résultats non établis |
| Bonnes pratiques GitHub | Résumé S001/S005 | Utilisées comme exigences de conception | Recherche externe non rejouée |
