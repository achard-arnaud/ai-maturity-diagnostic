# Trousse de reprise après les vacances — v0.7

## Ce qui doit être vrai au retour

La v0.7 fournit un control plane local reliant :

```text
ICB / secteur
-> entreprise / étude
-> use cases
-> chaîne de valeur + causes
-> qualification produit
-> contacts
-> reach first/second wave
-> preuve / pilote
```

Le patrimoine UC est un graphe dérivé des artefacts existants. Il n’existe pas de base Zettelkasten/graph séparée.

## Première session — 60 à 90 minutes

### 1. Vérifier l’environnement

```bash
python -m pip install -e '.[docs,dev]'
python scripts/check_release.py
python -m app.server
```

Le serveur local doit rester sur `127.0.0.1` tant que les gates auth/RBAC/audit/hardening v0.5 ne sont pas fermés.

### 2. Choisir trois entreprises représentatives

Prendre idéalement :

- une entreprise avec étude/matching déjà avancé ;
- une entreprise avec contacts mais demande incomplète ;
- une entreprise dans un secteur proche du seuil de benchmark.

Ne pas chercher à couvrir tout le portefeuille lors de la première reprise.

### 3. Tester le parcours Demande

Pour chaque entreprise :

1. vérifier ICB et fraîcheur de l’étude ;
2. consolider 3 à 10 UC réellement supportés ;
3. lancer Porter/Ishikawa sur 1 à 3 UC structurants ;
4. inspecter le patrimoine UC et les liens dérivés ;
5. valider/rejeter au moins une hypothèse de workflow adjacent.

Feedback à noter :

- relation UC réellement utile ou bruit ;
- CTA manquant ;
- information affichée trop tôt/trop tard ;
- activité Porter ou cause Ishikawa qui pousse à inventer au lieu d’observer.

### 4. Tester Qualification → Reach

Sur une opportunité au fit `VALIDATE` ou `PURSUE` :

1. vérifier que les hard gates sont respectés ;
2. contrôler les contacts existants ;
3. ouvrir Reach ;
4. vérifier promoteur, prescripteur, terrain/user, technique et veto ;
5. challenger first wave vs second wave ;
6. vérifier qu’un rôle obsolète déclenche `Valider le rôle actuel` ;
7. vérifier qu’une lane manquante déclenche `Élargir le 2e tour` ;
8. vérifier que le newsflow explique seulement `why_now`.

Ne pas écrire/envoyer de campagne outbound depuis ce produit à ce stade.

### 5. Tester Nudging

Sur une entreprise avec plusieurs UC :

- productivisation : est-ce réellement moins coûteux / plus réutilisable ?
- upsell : la dépendance entre UC est-elle explicite et actuelle ?
- cross-sell : existe-t-il un vrai feedback entreprise pour raconter le package ?

Rejeter les nudges faibles ; l’objectif du Gold Set est précisément de mesurer ces faux positifs.

## Feedback log minimal

Pour chaque friction, conserver :

- objet : secteur / entreprise / UC / offre / personne ;
- écran/menu ;
- action attendue ;
- action proposée ;
- pourquoi l’utilisateur hésite ou bloque ;
- sévérité ;
- correction candidate ;
- exemple d’artefact concerné.

## Décisions à prendre après 5–10 usages réels

### A. Graphe UC

Conserver l’architecture dérivée sauf preuve d’un problème mesurable :

- recherche de relations trop lente ;
- volume de liens ingérable ;
- liens manuels trop coûteux ;
- besoin de parcours multi-hop impossible avec les fichiers.

Seulement dans ce cas, étudier graph DB/vector retrieval.

### B. Reach

Valider ou corriger :

- taxonomie promoteur/prescripteur/terrain/tech/veto ;
- seuil first wave / second wave ;
- rôle du newsflow ;
- besoin réel d’un journal de reach persistant.

### C. Historisation

Décider si les artefacts du study suffisent ou si un event log devient nécessaire pour :

- résolutions de blockers ;
- validation/rejet de nudges ;
- modifications de wave ;
- feedback de discovery.

Ne créer un store dédié qu’après cette décision.

## Gold Set v0.7

Construire au minimum :

- 15–20 UC connus avec vrais/faux workflows adjacents ;
- 20 paires de UC avec dépendance vraie/fausse ;
- 10 patterns sectoriels qui ne doivent **pas** devenir des demandes compte ;
- 15 personnes avec rôle courant / stale / ambigu ;
- 10 opportunités avec promoteur/prescripteur/terrain/veto connus ;
- 10 newsflows dont certains doivent changer le `why_now` et aucun le fit.

## Gates historiques toujours ouverts

Ne pas les confondre avec la maturité fonctionnelle v0.7 :

- auth/RBAC/audit/hardening avant exposition réseau ;
- executor de skills de production ;
- purge/rotation de tout secret historique restant à prouver ;
- Gold Set décisionnel global ;
- validation finale des vérités commerciales des offres ;
- éventuelle persistence/queue si usage concurrent.

## Ordre de reprise recommandé

```text
1. vraies données
2. UX / blockers
3. Gold Set UC + reach
4. calibration des règles
5. décision persistence
6. seulement ensuite : automatisation supplémentaire / graph infra / outbound
```

Le critère de décision n’est pas la sophistication technique : c’est la réduction du temps de qualification, la qualité des hypothèses et le nombre de faux positifs évités.
