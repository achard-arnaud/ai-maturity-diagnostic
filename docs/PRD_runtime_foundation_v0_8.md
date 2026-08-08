# PRD — Runtime foundation v0.8

## 1. Objectif

Faire évoluer le control plane v0.7, actuellement local et mono-root, vers un runtime interne multi-utilisateur sûr et exploitable, sans créer prématurément une plateforme SaaS.

La v0.8 doit permettre à plusieurs utilisateurs de travailler dans des espaces isolés, avec une authentification légère, des droits simples, des erreurs cohérentes, des logs corrélables et des écritures fiables.

## 2. Principes non négociables

- La recherche entreprise reste product-blind jusqu'au matching.
- Les hard gates métier restent indépendants des droits techniques : un `admin` ne peut pas contourner un blocker métier.
- Les artefacts métier restent les sources de vérité gouvernées ; le store runtime ne devient pas une seconde vérité.
- Une entreprise/account métier n'est pas un tenant technique. Le terme retenu pour l'isolation est **workspace**.
- Aucun mot de passe utilisateur n'est stocké ou vérifié par l'application.
- Aucun mode sans authentification n'est autorisé hors loopback.
- Aucun secret, token, contact privé, preuve brute ou stderr executor ne doit être exposé dans les logs/API par défaut.

## 3. Modèle minimal

### User
Identité humaine issue d'un fournisseur OpenID Connect.

### Workspace
Frontière d'isolation technique et de données.

### Membership
Association `user_id + workspace_id + role`.

Rôles initiaux :
- `reader` : lecture des données et vues dérivées autorisées ;
- `reviewer` : lecture + décisions humaines de revue ;
- `contributor` : reviewer + mutations métier et exécutions autorisées ;
- `admin` : contributor + gestion du workspace et des memberships.

### RequestContext
Objet immutable construit une fois par requête :
- `request_id` ;
- `user_id` ;
- `workspace_id` ;
- `role` ;
- `auth_source`.

Tous les services manipulant des données privées/mutables reçoivent ce contexte ou un `WorkspacePaths` dérivé ; ils ne choisissent jamais eux-mêmes un tenant depuis un paramètre HTTP arbitraire.

## 4. Authentification

### Modes

`local_disabled`
- réservé au développement local ;
- accepté uniquement avec un bind loopback ;
- acteur et workspace locaux explicitement marqués comme développement.

`oidc`
- un fournisseur OIDC configurable au premier déploiement ;
- protocole géré par une librairie standard, pas par du code OAuth/OIDC maison ;
- le fournisseur peut changer sans modifier le coeur métier.

### Session navigateur

- identifiant de session opaque et aléatoire ;
- cookie HttpOnly + Secure + SameSite ;
- session révocable côté serveur ;
- tokens IdP jamais exposés au JavaScript applicatif ;
- contrôle Origin/CSRF sur les requêtes mutantes ;
- CORS same-origin par défaut.

Les transactions OIDC `state`/nonce/PKCE sont courtes, one-shot et corrélées côté serveur. Les access tokens fournisseur ne sont pas conservés après établissement de l'identité sauf besoin futur explicitement spécifié.

### Bootstrap utilisateur

Le premier déploiement n'ajoute pas un système d'invitation complet.

- un ou plusieurs administrateurs initiaux sont autorisés par configuration à partir d'un email OIDC **vérifié** ou d'un mapping opérateur explicite ;
- le bootstrap est audité et peut être désactivé une fois le premier admin créé ;
- ensuite, les memberships sont provisionnés par un admin via une action dédiée/CLI ou UI contrôlée ;
- aucune auto-inscription publique ni création automatique de workspace sur simple login.

## 5. Store de contrôle léger

Première cible : **SQLite en WAL**, un seul processus/instance applicative.

Tables runtime seulement :
- users ;
- workspaces ;
- memberships ;
- sessions ;
- audit_events ;
- métadonnées techniques minimales d'idempotence/verrou si nécessaires.

Ne pas y déplacer :
- études ;
- preuves ;
- use cases ;
- profils produit ;
- matrices de fit ;
- truth métier.

Trigger de migration PostgreSQL : multi-instance, HA, concurrence d'écriture soutenue ou besoin de requêtage opérationnel non raisonnable sous SQLite.

## 6. Isolation des fichiers

Assets globaux en lecture :
- `skills/` ;
- `contracts/` ;
- `templates/` ;
- `data/taxonomies/`.

Données workspace :

```text
workspaces/<workspace_id>/
  studies/
  data/private/
  artifacts/
  runtime/
```

Le statut de `product_catalog/` doit être décidé explicitement avant implémentation :
- global s'il représente la vérité canonique d'un fournisseur commun ;
- workspace-scoped si chaque espace possède ses propres offres.

Aucune donnée privée ne doit être adressable uniquement par un ID de ressource : toute résolution vérifie aussi le workspace courant.

La migration du mono-root v0.7 doit comporter inventaire, dry-run, hashes/counts, rapport et rollback avant de basculer en workspace-only.

## 7. Web/API

Faire évoluer uniquement l'adaptateur HTTP vers une stack ASGI légère, recommandation : FastAPI/Starlette.

Les modules métier existants restent framework-agnostic.

Le nouvel adaptateur possède :
- middleware request-id/logging ;
- résolution auth/session ;
- résolution workspace/membership ;
- autorisation ;
- validation input/output ;
- gestion centralisée des erreurs ;
- headers de sécurité ;
- liveness/readiness.

### Workspace explicite dans les routes

Ne pas conserver un seul « workspace actif » mutable dans la session navigateur : cela crée une ambiguïté lorsque l'utilisateur ouvre plusieurs workspaces dans plusieurs onglets.

Le workspace est donc explicite dans la navigation, par exemple :

```text
/w/<workspace_slug>/demand
/w/<workspace_slug>/qualification
/api/workspaces/<workspace_id>/...
```

Le slug/ID demandé est un **sélecteur**, jamais une preuve d'autorisation. Le serveur vérifie la membership à chaque requête puis construit `RequestContext`.

Bénéfices :
- deep links non ambigus ;
- multi-onglets sûrs ;
- cache frontend naturellement partitionné ;
- changement de workspace visible et auditable ;
- moins de risque de contamination de contexte caché.

### Parcours utilisateur

1. Non authentifié -> **Se connecter**.
2. Login OIDC -> résolution de l'identité puis des memberships.
3. Zéro membership -> écran d'accès non provisionné, aucune donnée métier.
4. Une membership -> ouverture directe du workspace.
5. Plusieurs memberships -> dernière route autorisée si connue, sinon sélection de workspace.
6. Header applicatif -> switcher workspace visible ; le switch change la route, vide le cache métier concerné et recharge les données.
7. Admin -> gestion membres/rôles du workspace ; pas de self-service public au premier slice.

## 8. Erreurs

Envelope public stable :

```json
{
  "error": {
    "code": "WORKSPACE_FORBIDDEN",
    "message": "You cannot access this workspace.",
    "request_id": "uuid",
    "retryable": false
  }
}
```

Mapping de base :
- 401 non authentifié ;
- 403 interdit pour une action sur un contexte déjà visible/autorisé ;
- 404 pour une ressource absente **ou une sonde cross-workspace dont l'existence ne doit pas être révélée** ;
- 409 conflit/version obsolète ;
- 422 validation ;
- 429 limitation ;
- 503 executor/service indisponible ;
- 504 timeout executor ;
- 500 inattendu.

Les erreurs inattendues génèrent un `error_id` et une stack serveur ; la réponse client reste générique.

## 9. Logs et audit

### Logs applicatifs
JSON stdout, avec au minimum :
`timestamp, level, event, request_id, workspace_id, actor_id, method, route, status, duration_ms, skill_id, error_code`.

Pas de payload métier ni de token/cookie par défaut.

### Audit
Événements append-only distincts des logs :
- login/logout/échec auth ;
- changement de workspace ;
- changement membership/rôle ;
- mutation d'un artefact protégé ;
- revue humaine ;
- cycle skill `prepared/started/completed/failed` ;
- changement de configuration privilégiée.

## 10. Executor

Avant exposition réseau :
- environnement enfant allowlisté ;
- output borné ;
- stdout/stderr bruts jamais retournés au client en production ;
- diagnostics redacted côté serveur ;
- timeout explicite ;
- workspace/context paths obligatoires ;
- statut sûr + request_id côté client.

## 11. Fiabilité des écritures

Centraliser les mutations fichiers :
- écriture temporaire ;
- flush/fsync lorsque pertinent ;
- `os.replace` atomique ;
- lock/serialization par workspace/ressource ;
- version/ETag pour les ressources éditées concurremment.

## 12. Déploiement minimal

Une seule instance au départ :
- container/service non-root ;
- code applicatif read-only ;
- volume persistent pour workspaces + control store ;
- reverse proxy HTTPS ;
- aucune exigence Kubernetes.

## 13. Critères de sortie P0

- isolation cross-workspace testée en lecture et écriture ;
- auth-disabled impossible hors loopback ;
- RBAC deny-by-default ;
- RequestContext présent sur toute route protégée ;
- multi-onglets/workspaces ne contaminent pas le contexte ;
- erreurs stables avec request_id ;
- aucune fuite de secret/stderr executor ;
- audit des actions sensibles ;
- tests de session/revocation/CSRF/origin ;
- écritures atomiques sous concurrence testée ;
- app installable/déployable indépendamment du cwd du repo ;
- couverture `app` >=80% ;
- tous invariants métier historiques toujours verts.

## 14. Gates de feedback

Avant implémentation complète :
1. confirmer si `product_catalog` est global ou workspace-scoped ;
2. choisir le premier IdP OIDC et la topologie de déploiement ;
3. confirmer qu'une instance SQLite suffit à la phase d'usage réelle ;
4. challenger la matrice des quatre rôles sur les premiers utilisateurs ;
5. ne promouvoir en non-loopback qu'après revue sécurité et tests adversariaux.
