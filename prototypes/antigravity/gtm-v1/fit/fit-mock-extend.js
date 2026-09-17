/* Fit screen — local, additive extension of shared/mock-data.js (loaded
   after it, and after research/research-mock-extend.js so Demand/Evidence/
   ResearchCase data is a single source between Research and Fit — see that
   file's header comment for why this lives outside shared/mock-data.js).
   Adds fields to the existing FitAssessment/ProductSnapshot shapes
   (reviewer, decision_history, blockers, hard_gates, icp_fit, timing,
   integration_fit, commercial_unknowns, next_best_action, changelog,
   status) plus more instances of those same shapes, so the Fit queue and
   Product Library have more than one row/version to work with. No new
   canonical object type is introduced. */
(function () {
  "use strict";

  var d = window.GtmMockData;
  if (!d) {
    throw new Error("fit-mock-extend.js: shared/mock-data.js must be loaded first");
  }

  function byId(list, key, id) {
    for (var i = 0; i < list.length; i++) {
      if (list[i][key] === id) return list[i];
    }
    return null;
  }

  // -- ProductSnapshot: `status`/`changelog` are additive, for the Product
  // Library's version/snapshot diff view. Every published snapshot is
  // immutable — only a new snapshot can supersede it.
  var v3 = byId(d.productSnapshots, "snapshot_id", "snap_platform_v3");
  if (v3) {
    v3.status = "published";
    v3.changelog = ["Ajout module d'alertes de rupture", "Amélioration de l'ingestion volumétrie"];
  }
  d.productSnapshots.unshift(
    { snapshot_id: "snap_platform_v1", product_id: "prod_platform", version: "v3.0", published_at: "2026-03-01", immutable: true, status: "superseded", changelog: ["Connecteurs ERP legacy (bêta)"] },
    { snapshot_id: "snap_platform_v2", product_id: "prod_platform", version: "v3.1", published_at: "2026-05-15", immutable: true, status: "superseded", changelog: ["Ajout réplanification temps réel", "Corrections connecteurs ERP"] }
  );

  // -- FitAssessment: additive fields support the Fit Detail body/
  // right-rail sections. `need_coverage` stays a plain string summary —
  // every Fit Detail template must render it visually secondary to the
  // qualitative sections (mission: "un score peut exister comme résumé
  // mais ne doit jamais dominer l'explication").
  var fitAcme1 = byId(d.fitAssessments, "fit_id", "fit_acme_1");
  if (fitAcme1) {
    fitAcme1.freshness = "fresh";
    fitAcme1.hard_gates = [
      { name: "ProductSnapshot publiée requise", passed: true },
      { name: "Demand au statut Validated ou plus avant décision finale", passed: false },
    ];
    fitAcme1.icp_fit = { rating: "Bon alignement", note: "Secteur industrie + taille > 500 salariés, dans le profil ICP déclaré." };
    fitAcme1.timing = { rating: "Favorable", note: "Signal récent (promotion + hiring) suggère une fenêtre active, non confirmée par le compte." };
    fitAcme1.integration_fit = { rating: "À vérifier", note: "Connecteur ERP legacy existe en v3.1+, compatibilité avec la version exacte d'Acme non confirmée." };
    fitAcme1.commercial_unknowns = ["Budget disponible non confirmé", "Cycle de décision (comité vs. sponsor unique) inconnu"];
    fitAcme1.evidence_ids = ["ev_1", "ev_2", "ev_3"];
    fitAcme1.blockers = [];
    fitAcme1.reviewer = null;
    fitAcme1.decision_history = [
      { at: "2026-09-05", actor: "system", action: "Assessment v1 générée automatiquement" },
      { at: "2026-09-15", actor: "alex@internal", action: "Assessment v2 — mise à jour après nouvelle ProductSnapshot v3.2" },
    ];
    fitAcme1.next_best_action = "Qualifier le sponsor budgétaire avant de proposer un pilote (cf. Demand.unknowns).";
  }

  d.fitAssessments.push(
    {
      fit_id: "fit_acme_2",
      demand_id: "dem_acme_2",
      company_id: "co_acme",
      product_id: "prod_platform",
      snapshot_id: "snap_platform_v3",
      version: 1,
      status: "blocked",
      freshness: "fresh",
      overall_decision: "BLOCKED",
      need_coverage: "—",
      hard_gates_passed: false,
      hard_gates: [
        { name: "ProductSnapshot publiée requise", passed: true },
        { name: "Revue sécurité du périmètre de données non complétée", passed: false },
      ],
      icp_fit: { rating: "Non évalué", note: "Bloqué avant évaluation ICP — hard gate non levée." },
      timing: { rating: "Non évalué", note: "—" },
      integration_fit: { rating: "Non évalué", note: "—" },
      commercial_unknowns: ["Non évalué tant que le hard gate n'est pas levé"],
      matches: [],
      gaps: [],
      contradictions: [],
      unknowns: ["Portée exacte des données de reporting concernées"],
      alternatives: [],
      evidence_ids: [],
      blockers: [{ label: "Hard gate : revue sécurité du périmètre de données non complétée", resolved: false, resolver_cta: "Ouvrir la demande de revue sécurité" }],
      reviewer: null,
      decision_history: [{ at: "2026-09-16", actor: "system", action: "Assessment créée, bloquée immédiatement par hard gate" }],
      next_best_action: "Ouvrir une demande de revue sécurité avant toute évaluation de fit.",
    },
    {
      fit_id: "fit_nautix_1",
      demand_id: "dem_nautix_1",
      company_id: "co_nautix",
      product_id: "prod_platform",
      snapshot_id: "snap_platform_v1",
      version: 1,
      status: "stale",
      freshness: "stale",
      overall_decision: "PURSUE (draft, périmée)",
      need_coverage: "48%",
      hard_gates_passed: true,
      hard_gates: [{ name: "ProductSnapshot publiée requise", passed: true }],
      icp_fit: { rating: "Partiel", note: "Secteur logistique hors ICP principal déclaré, à confirmer." },
      timing: { rating: "Inconnu", note: "Assessment antérieure à la Demand validée — à rejouer." },
      integration_fit: { rating: "Périmé", note: "Évalué sur ProductSnapshot v3.0, deux versions publiées depuis." },
      commercial_unknowns: ["Budget confirmé pour Q4 (cf. Demand.unknowns)"],
      matches: ["Visibilité flotte (partielle)"],
      gaps: ["Pas de connecteur logistique dédié à cette date"],
      contradictions: [],
      unknowns: [],
      alternatives: [],
      evidence_ids: [],
      blockers: [{ label: "Périmée : la ProductSnapshot a changé (v3.0 → v3.2) depuis cette évaluation", resolved: false, resolver_cta: "Relancer l'évaluation sur la snapshot courante" }],
      reviewer: null,
      decision_history: [{ at: "2026-03-20", actor: "system", action: "Assessment v1 générée sur ProductSnapshot v3.0" }],
      next_best_action: "Relancer l'évaluation sur snap_platform_v3 maintenant que la Demand est Validated.",
    },
    {
      fit_id: "fit_nautix_2",
      demand_id: "dem_nautix_1",
      company_id: "co_nautix",
      product_id: "prod_platform",
      snapshot_id: "snap_platform_v3",
      version: 2,
      status: "needs_human_review",
      freshness: "fresh",
      overall_decision: "PURSUE (à valider)",
      need_coverage: "61%",
      hard_gates_passed: true,
      hard_gates: [{ name: "ProductSnapshot publiée requise", passed: true }],
      icp_fit: { rating: "Partiel", note: "Hors ICP sectoriel déclaré (logistique) — nécessite un jugement humain, pas seulement le calcul." },
      timing: { rating: "Favorable", note: "Demand passée Validated récemment." },
      integration_fit: { rating: "Bon", note: "Connecteur logistique ajouté depuis v3.1." },
      commercial_unknowns: ["Budget confirmé pour Q4 (cf. Demand.unknowns)"],
      matches: ["Visibilité flotte temps réel", "Connecteur logistique (depuis v3.1)"],
      gaps: ["Pas de module prévision de la demande"],
      contradictions: [],
      unknowns: ["Compatibilité avec le TMS existant de Nautix"],
      alternatives: [],
      evidence_ids: [],
      blockers: [],
      reviewer: null,
      decision_history: [
        { at: "2026-03-20", actor: "system", action: "Assessment v1 générée sur ProductSnapshot v3.0 (voir fit_nautix_1)" },
        { at: "2026-09-16", actor: "system", action: "Assessment v2 régénérée sur ProductSnapshot v3.2 après passage Demand → Validated" },
      ],
      next_best_action: "Revue humaine requise : compte hors ICP sectoriel déclaré malgré un need coverage correct.",
    },
    {
      fit_id: "fit_verdal_1",
      demand_id: "dem_verdal_1",
      company_id: "co_verdal",
      product_id: "prod_platform",
      snapshot_id: "snap_platform_v3",
      version: 1,
      status: "approved",
      freshness: "fresh",
      overall_decision: "PURSUE (approuvé)",
      need_coverage: "82%",
      hard_gates_passed: true,
      hard_gates: [{ name: "ProductSnapshot publiée requise", passed: true }],
      icp_fit: { rating: "Bon alignement", note: "Grand compte énergie, sponsor Innovation déjà identifié." },
      timing: { rating: "Favorable", note: "Programme de modernisation IA déjà lancé côté client." },
      integration_fit: { rating: "Bon", note: "Volumétrie compatible avec les références existantes." },
      commercial_unknowns: [],
      matches: ["Réplanification temps réel", "Ingestion haute volumétrie"],
      gaps: [],
      contradictions: [],
      unknowns: [],
      alternatives: [],
      evidence_ids: ["ev_17", "ev_18"],
      blockers: [],
      reviewer: "sam@internal",
      decision_history: [
        { at: "2026-06-05", actor: "system", action: "Assessment v1 générée" },
        { at: "2026-06-12", actor: "sam@internal", action: "Approuvée après revue humaine", note: "Décision humaine — voir .human-decision-badge" },
      ],
      next_best_action: "Passer en Targets — un Target ne peut être créé qu'à partir de ce Fit approuvé.",
    },
    {
      fit_id: "fit_verdal_2",
      demand_id: "dem_verdal_2",
      company_id: "co_verdal",
      product_id: "prod_platform",
      snapshot_id: "snap_platform_v3",
      version: 1,
      status: "declined",
      freshness: "aging",
      overall_decision: "DECLINE",
      need_coverage: "40%",
      hard_gates_passed: true,
      hard_gates: [{ name: "ProductSnapshot publiée requise", passed: true }],
      icp_fit: { rating: "Hors périmètre produit", note: "Le produit ne couvre pas le reporting réglementaire CSRD." },
      timing: { rating: "Non pertinent", note: "—" },
      integration_fit: { rating: "Non pertinent", note: "—" },
      commercial_unknowns: [],
      matches: [],
      gaps: ["Aucun module de reporting réglementaire dans le produit"],
      contradictions: ["Le périmètre réglementaire exact est encore en discussion interne (cf. Demand.contradictions)"],
      unknowns: [],
      alternatives: ["Réorienter vers un partenaire spécialisé RegTech"],
      evidence_ids: ["ev_19"],
      blockers: [],
      reviewer: "sam@internal",
      decision_history: [
        { at: "2026-06-20", actor: "system", action: "Assessment v1 générée" },
        { at: "2026-06-25", actor: "sam@internal", action: "Déclinée après revue humaine", note: "Décision humaine — voir .human-decision-badge" },
      ],
      next_best_action: "Ne pas retenter sans nouveau Product/ProductSnapshot couvrant le reporting réglementaire.",
    }
  );
})();
