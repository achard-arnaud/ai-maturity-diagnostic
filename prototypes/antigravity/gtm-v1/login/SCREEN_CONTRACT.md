# Login V1 — Screen Contract

Per `ANTIGRAVITY_03` excerpt "Login V1" and `SHELL_CONTRACT.md`.

## Job

Proposition visuelle V1 du parcours de connexion : sign-in, choix de
provider, chargement, erreur, session expirée, sélection de workspace,
onboarding premier login. Authority: NONE — UX exploration only. Ne définit **aucun** protocole
d'auth réel (OIDC, mécanique de session) — ce sont des décisions produit
déjà prises dans `app/authruntime/` (`app.py`, `oidc.py`, `db.py`,
`ADR-007-multi-workspace-auth-runtime.md`). Cet écran est la couche
visuelle/UX au-dessus, jamais une réimplémentation.

Login appelle techniquement `GtmProtoShell.render("home", …)` (requis par
`checks/check_screen.py` — tout `index.html` doit utiliser le shell
partagé avec un nav-id canonique) mais **masque volontairement la
sidebar/le header produit** via une règle CSS scoped à la page : aucun
utilisateur n'est authentifié à ce stade, montrer le sélecteur de
workspace ou la nav des 9 espaces quotidiens serait trompeur. Seuls
`tokens.css`/`components.css`/la structure `#gtmMain` sont réellement
réutilisés ; `"home"` est choisi comme nav-id car c'est la destination
réelle après connexion (§Navigation), pas une affirmation qu'un menu Home
est visible ici — c'est un compromis mécanique documenté, pas une décision
de nav produit.

## Objets affichés

Aucun objet canonique de `SHELL_CONTRACT.md` §4. Login est product-neutre
vis-à-vis du domaine GTM ; les seuls "objets" affichés sont des concepts
d'auth déjà réels dans le produit (session, workspace, membership) montrés
comme texte informatif, jamais comme des champs éditables ou des données
mock inventées.

## Composants

- `index.html` — écran de sign-in par défaut : logo/texte produit, choix
  de provider (aujourd'hui un seul provider réel — Google OIDC, cf.
  `AUTH_LOGIN_GAP.md` §1 — donc un unique bouton "Se connecter avec
  Google" + un second bouton visuellement présent mais `disabled`
  ("D'autres fournisseurs — bientôt"), pour illustrer le concept de choix
  sans mentir sur ce qui existe).
- `workspace-select.html` — sélection de workspace (mission : "workspace
  selection"). Le produit réel n'a pas de sélecteur aujourd'hui
  (1 membership par utilisateur non-admin, cf. `AUTH_LOGIN_GAP.md` §6) —
  cet écran illustre le concept pour un futur multi-workspace, marqué
  explicitement comme non actif dans le produit réel.
- `onboarding.html` — premier login (mission : "first-login onboarding").
  S'inspire du ton de la vraie page `/auth/pending`
  (`app/authruntime/app.py`'s `_render_pending_page` : "authentifié mais
  pas encore de workspace, un admin doit vous accorder une adhésion") sans
  copier sa logique d'auth — reformulé en écran d'accueil V1.
- `states.html` — galerie des 8 états adaptés (voir ci-dessous).

## États

Adaptation explicite demandée par la mission (Login n'est pas un écran à
données métier) :

| État requis | Interprétation Login |
|---|---|
| `default` | Écran de sign-in normal |
| `loading` | Redirection vers le provider OIDC en cours |
| `empty` | Aucun provider configuré (503 réel aujourd'hui si OIDC non configuré, cf. `AUTH_LOGIN_GAP.md` §8) |
| `error` | Échec d'authentification (consentement annulé, provider en erreur — actuellement non géré côté produit réel, cf. §8) |
| `blocked` | Compte authentifié mais sans workspace — reflète `/auth/pending` réel |
| `stale` | Session expirée (12h fixes, sans refresh, cf. §1) — invite à se reconnecter |
| `partial-data` | Sélection de workspace en attente (illustratif — le produit réel n'a pas ce cas aujourd'hui, cf. §6) |
| `success` | Authentification réussie, transition vers Home |

## Navigation

- `index.html` → (succès) → transition conceptuelle vers `../home/index.html`
  (le produit réel redirige vers `/w/{workspace}/home`, cf. §7 — non simulé
  ici en détail, juste le point d'arrivée).
- `blocked` (pas de workspace) : CTA "Se déconnecter" — même intention que
  le vrai bouton de `_render_pending_page`, pas de nouvelle action inventée.
- `workspace-select.html` → sélection → `../home/index.html`.
- `onboarding.html` → CTA "Commencer" → `../home/index.html`.

## Responsive

| Écran | Desktop | Tablet | Mobile |
|---|---|---|---|
| Sign-in | FULL — carte centrée, largeur fixe | FULL — carte centrée, largeur fluide | FULL — carte pleine largeur avec marges, aucun contenu perdu |
| Workspace select / Onboarding | FULL — carte centrée | FULL | FULL — liste/carte empilée verticalement |

Login n'a pas de mode "READ" dégradé — c'est un écran mono-tâche déjà
minimal à toutes les tailles, donc FULL partout par nature de l'écran, pas
par choix de scope.

## DECISION_REQUIRED

1. Le produit réel n'a qu'un seul provider OIDC (Google) — le bouton
   "autres fournisseurs" est un placeholder purement illustratif de la
   mission ; l'architecture owner doit décider si un multi-provider réel
   est even envisagé avant de le construire pour de vrai.
2. `workspace-select.html` illustre un concept qui n'a pas de contrepartie
   dans le modèle de données actuel (1 membership par utilisateur non-admin,
   `PRIMARY KEY` sur `user_id`) — à ne pas construire côté réel sans une
   décision de schéma explicite (`AUTH_LOGIN_GAP.md` §6 le note déjà comme
   un changement de modèle, pas juste d'UI).
3. Le contenu exact de l'écran `error` (message, retry, contact support)
   n'existe nulle part côté réel aujourd'hui (`login.html` n'a aucune
   gestion d'erreur, cf. §8) — ce mockup propose un message générique,
   pas un texte produit validé.
4. Le "next"/retour à l'écran d'origine après reconnexion (`stale` →
   retour exact à Pipeline, pas juste Home) est un gap confirmé et non
   résolu côté réel (§9) — ce mockup montre un retour vers Home par
   simplicité, pas la vraie mécanique de redirection.
