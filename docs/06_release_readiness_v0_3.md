# Revue de readiness — milestone v0.3

## Verdict

Le dépôt est publié comme **milestone technique v0.3** sur un historique Git neuf, synchronisé sur `dev` et `main`. Il constitue un socle reproductible de qualification, pas encore une preuve de performance commerciale ni une mise en production du connecteur LinkedIn.

## Revue des cinq gates

| Gate | Résolution v0.3 | État |
|---|---|---|
| Ancien projet et historique | Snapshot neuf publié; les anciens fichiers et la clé privée ne font pas partie du nouvel arbre | Résolu dans les branches actives; purge serveur à confirmer |
| Accès Git/SSH | La passphrase de la clé désignée a été retirée à la demande de son propriétaire; lecture et push SSH vérifiés | Résolu |
| Identité, contrats et coordination | Seed personne `nom + entreprise`, migration sauvegardée, validation profonde, décision/score/gates partagés jusqu’au reach | Résolu et testé |
| ICB | Référentiel local officiel v5.0; mapping léger `pending/candidate/validated`; candidats limités aux rollups exploratoires | Résolu; validation compte par compte ouverte |
| Portabilité, CI, confidentialité | Python 3.11, dépendances racine, CI GitLab, release gate, données privées ignorées, manifeste agrégé et chemins absolus supprimés | Résolu localement; première CI distante à observer |

## Contrôles exécutés

- validation du package et du design LinkedIn différé;
- 16 tests unitaires/intégration, dont six familles adverses;
- parsing de tous les YAML/JSON et méta-validation des JSON Schema;
- vérification des liens Markdown locaux;
- scan de clés privées et chemins absolus de home;
- validation et génération du DOCX d’exemple;
- validation du réseau privé après migration d’identité;
- résultat agrégé : `0 release error(s)`.

Les branches locales et distantes `dev` et `main` ont été remplacées avec des leases exacts et partagent le nouvel historique. L’ancien reflog, la référence distante locale obsolète et les objets inaccessibles ont été purgés de ce clone. L’état de la première pipeline GitLab reste à observer avec un accès API/UI autorisé.

## Limites du milestone

- Les 220 cas de trigger sont présents et équilibrés, mais n’ont pas encore été rejoués par un modèle sur un Gold Set métier.
- Les cas de raisonnement sont structurés, sans mesure de précision commerciale réelle.
- Trois offres restent `draft`; Astraforge reste `reconstructed` avec preuves commerciales incomplètes.
- Aucun mapping ICB de compte n’est validé automatiquement; les règles de nom ne produisent que `candidate/N0`.
- Aucun rollup sectoriel réel n’est encore `decision_grade`.
- La résolution maison-mère/filiale et la fusion future d’identités multi-employeurs restent à construire.
- LinkedIn demeure une architecture différée, read-only, sans plugin ni accès officiel présumé.
- Plusieurs contrats métier v0.2/v0.3 restent des contrats YAML lisibles plutôt que des JSON Schema complets.
- Réécrire les branches distantes ne garantit pas à elle seule la purge immédiate des anciens objets, caches, forks ou sauvegardes serveur. La clé historique doit rester considérée compromise et révoquée.

Le backlog structuré de reprise est dans [`artifacts/TODO_release_v0_3.yaml`](../artifacts/TODO_release_v0_3.yaml).
