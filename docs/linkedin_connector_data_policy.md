# LinkedIn Connector Data Policy — draft

**Status:** Required before LI-G3
**Version:** 0.1

## Finalité autorisée

Valider l’identité, l’employeur ou le rôle actuel d’un contact déjà connu lorsque cette incertitude affecte une opportunité entreprise × produit déjà qualifiée.

Ne sont pas permis : constitution d’une nouvelle base de prospects, enrichissement massif, collecte de contenus membres pour lead scoring et outreach automatique.

## Minimisation

Demander uniquement les champs nécessaires à la question de validation. Préférer une observation normalisée — employeur attendu, employeur observé, date et résultat — à la conservation d’un profil, d’une photo, d’une biographie, de posts ou de relations.

## Classes de stockage

- `transient_only`;
- `allowed_with_retention`;
- `user_owned`;
- `unknown`.

Si la classe est `unknown`, aucun payload fournisseur n’est persisté.

## Provenance minimale

- fournisseur et méthode d’acquisition;
- programme d’autorisation et sujet authentifié;
- capacité utilisée;
- date de récupération;
- référence source si autorisée;
- limites et confiance;
- classe de stockage et version de policy.

## Merge canonique

Un payload ou une preuve fournisseur ne modifie jamais directement une personne ou une relation. Le merge gate produit une nouvelle observation interne avec sa propre provenance. Les identifiants internes restent canoniques.

## Expiration et suppression

L’implémentation future devra permettre l’expiration et la suppression par lien d’identité externe, fournisseur/programme et personne lorsque requis, ainsi que le nettoyage des payloads transitoires.

## Git

Aucun nom privé supplémentaire, token, payload de profil, audit nominatif ou mapping d’identité externe n’entre dans Git.
