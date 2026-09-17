# Export / Editor V1 — Screen Contract

Per `ANTIGRAVITY_03` excerpt "Export/editor V1" and `SHELL_CONTRACT.md`.
Authority: NONE — UX exploration only.

## Job

Uniquement le **flux d'expérience** : aperçu d'un artefact → édition →
revue → choix de template → aperçu du rendu → export. Ne décide **aucune**
technologie/format réel — ces choix appartiennent à l'architecture owner,
informés par `docs/research/next-wave/RICH_EDITOR_ADR_OPTIONS.md` (options
d'éditeur : Markdown/JSON structuré/ProseMirror) et
`DOCUMENT_COMPOSITION_EXPORT_OPTIONS.md` (options de composition/rendu :
`nice-output-engine` HTML/PDF/PNG déjà présent dans le repo,
`build_org_tech_note.py` DOCX déjà présent) — ce mockup illustre le
parcours sans présumer laquelle de ces options sera retenue.

## Objets affichés / manipulés

Le flux part d'un `Artifact` (`shared/mock-data.js`) — ex. `art_1`
"Acme — Note de recherche v1". Aucune nouvelle forme d'objet n'est
inventée ; le contenu édité pendant le flux reste un texte illustratif
statique (pas de moteur d'édition réel), et le "template" choisi est une
énumération fermée illustrative, pas un objet persistable.

## Composants

- `index.html` — stepper à 6 étapes, une visible à la fois (bascule via
  boutons Précédent/Suivant, pattern similaire au sélecteur d'états) :
  1. **Aperçu artefact** — carte artefact + métadonnées (source, version,
     auteur).
  2. **Édition** — zone de texte illustrative pré-remplie (pas d'éditeur
     riche réel — voir `RICH_EDITOR_ADR_OPTIONS.md`), avec bandeau
     rappelant que la mise en forme réelle n'est pas encore décidée.
  3. **Revue** — diff simplifié texte avant/après + CTA "Approuver" (une
     décision humaine, jamais auto-approuvée).
  4. **Choix de template** — 3 templates illustratifs (Note interne / One-
     pager / Export client), aucun rendu réel derrière.
  5. **Aperçu du rendu** — placeholder visuel du document final avec
     bandeau "rendu simulé — technologie non tranchée".
  6. **Export** — choix de format illustratif (PDF/DOCX/HTML — énumération
     non engageante), CTA final `disabled` avec tooltip renvoyant aux deux
     documents de recherche cités ci-dessus.
- `states.html` — 8 états adaptés au flux (voir ci-dessous).

## États

| État requis | Interprétation Export |
|---|---|
| `default` | Étape 1 (aperçu artefact) normale |
| `loading` | Génération de l'aperçu de rendu en cours (étape 5) |
| `empty` | Aucun artefact sélectionné pour démarrer le flux |
| `error` | Échec de génération du rendu |
| `blocked` | Revue (étape 3) non approuvée — impossible d'avancer au choix de template tant qu'un humain n'a pas validé |
| `stale` | L'artefact source a été modifié ailleurs depuis le début de l'édition — reprise à confirmer |
| `partial-data` | Aperçu de rendu généré mais une section (ex. pièce jointe) manque |
| `success` | Export terminé (téléchargement simulé) |

## Navigation

- Étape 1 accessible depuis `../admin/artifact-library.html` (CTA "Exporter",
  aujourd'hui `disabled` là-bas — ce flux est la proposition UX pour le
  jour où il sera branché, pas une fonctionnalité déjà live) et depuis
  toute future carte "Exporter" côté Fit/Research/Pipeline (non implémenté
  ici, hors périmètre des 5 écrans de cette mission).
- Chaque étape n'avance que via un CTA explicite (jamais de skip
  automatique) ; l'étape Revue bloque l'étape suivante tant que
  "Approuver" n'a pas été cliqué (cf. §5 SHELL_CONTRACT — décision
  humaine, jamais implicite).

## Responsive

| Écran | Desktop | Tablet | Mobile |
|---|---|---|---|
| Stepper (étapes 1-2-4-6) | FULL — panneau large, stepper horizontal | FULL — stepper horizontal, panneau pleine largeur | READ — stepper vertical compact (étape courante + libellé), panneau plein écran |
| Revue (diff) | FULL — deux colonnes avant/après | FULL — colonnes empilées | READ — avant/après en accordéon, pas de scroll horizontal |
| Aperçu du rendu | FULL — aperçu large centré | FULL | READ — aperçu réduit avec zoom tactile simulé (pas de vraie interaction) |

## DECISION_REQUIRED

1. La technologie d'édition réelle (Markdown / blocs JSON structurés /
   ProseMirror) n'est pas tranchée — voir `RICH_EDITOR_ADR_OPTIONS.md` §6.
   Ce mockup utilise un simple `<textarea>` illustratif à l'étape 2, sans
   présumer du choix final.
2. Le pipeline de rendu/export réel (`nice-output-engine` HTML/PDF/PNG vs
   `build_org_tech_note.py` DOCX vs autre) n'est pas tranché — voir
   `DOCUMENT_COMPOSITION_EXPORT_OPTIONS.md` §3. L'étape 6 liste 3 formats
   à titre illustratif, CTA final désactivé.
3. Le mécanisme de "revue" (qui approuve, quelles permissions, trace
   d'audit) n'est pas défini par cette exploration — le CTA "Approuver"
   est un bouton simple sans workflow d'approbation réel derrière,
   cohérent avec ARCHITECTURAL_AUTHORITY: NONE.
4. Aucune persistance n'est simulée entre les étapes (rafraîchir la page
   revient à l'étape 1) — à décider si un futur brouillon doit être
   sauvegardé côté serveur, hors scope V1.
