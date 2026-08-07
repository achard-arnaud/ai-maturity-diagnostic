# Recherche et preuve organisationnelles

## Hiérarchie des sources

1. Registres légaux ou réglementaires pour les mandats et sociétés liées.
2. Sites corporate pour la structure, les dirigeants, les marques et la stratégie.
3. Profils publics directs, biographies et prises de parole récentes.
4. Offres officielles pour manager, équipe, stack, roadmap et vocabulaire interne.
5. Communiqués, conférences, podcasts et médias reconnus.
6. Pages sociales d’entreprise.
7. Annuaires secondaires uniquement comme amorces.

Un mandat légal peut être confirmé par un registre. Un rôle opérationnel actuel doit idéalement avoir une source directe récente et une corroboration. Une relation hiérarchique n’est confirmée que si une source l’explicite.

## Séquence de recherche

### 1. Périmètre juridique

Identifier holding, services mutualisés, société opérationnelle, filiales, marques, acquisitions et coentreprises. Distinguer société juridique et marque commerciale.

### 2. Seed set

Rechercher président/fondateur, direction générale, conseil, finance, RH, M&A et dirigeants des entités prioritaires. Résoudre les entités avant d’approfondir les fonctions tech.

### 3. Chaîne technologique

Rechercher systématiquement CTO/Global CTO, CIO/DSI, engineering/R&D, architecture, plateforme, cloud/FinOps, sécurité/RSSI, data/AI, produit, qualité, opérations et adoption. Qualifier centralisation, fédération, matrice, transition ou intérim.

### 4. Filières et marques

Pour chaque filiale prioritaire : direction, CTO/R&D, produit, support/services. Prioriser selon la question de décision ; ne pas viser une exhaustivité sans valeur analytique.

### 5. Offres d’emploi

Extraire manager, équipe, taille, interactions, outils, CI/CD, cloud, sécurité, qualité, IA, contraintes et programme nommé. Conserver date et statut de l’offre.

### 6. Communication IA

Catégories autorisées : communication directe ; adjacente data/cloud/automatisation ; relais corporate ; non trouvé publiquement ; non évaluable. Décrire l’observation, pas une disposition psychologique.

## Résolution d’identité

Comparer entreprise, entité, géographie, dates et parcours. Conserver mandat légal et rôle opérationnel dans des champs distincts. Documenter les titres divergents et dégrader la confiance si la récence ou l’identité restent ambiguës.

## Matrice de requêtes

```text
site:<corporate-domain> gouvernance direction <COMPANY>
site:<legal-register> <LEGAL_ENTITY> dirigeants
"DSI Groupe" "<COMPANY>"
"Directeur des systèmes d'information" "<COMPANY>"
site:linkedin.com/in <COMPANY> CTO OR DSI OR "directeur technique"
site:linkedin.com/in <SUBSIDIARY> "Directeur R&D" OR "Directeur Produit"
site:<careers-domain> <SUBSIDIARY> cloud DevOps sécurité IA
"<FULL NAME>" "<COMPANY>" nomination
site:linkedin.com/posts "<FULL NAME>" IA
```

Adapter langue, titres locaux et variantes de noms. Enregistrer les requêtes utiles et les limites d’accès.

## Registre d’une personne

Renseigner nom ou fonction inconnue, rôle, mandat légal, périmètre, ancienneté prudente, expérience pertinente, expertise, communication IA observée, confiance, sources et date de dernière validation.

## Fail closed

Ne pas inventer pour rendre un graphe complet. Utiliser une fonction sans nom, supprimer une relation non nécessaire ou afficher `Non établi`. Toute relation inférée doit garder son statut dans le texte, le graphe et le RACI.
