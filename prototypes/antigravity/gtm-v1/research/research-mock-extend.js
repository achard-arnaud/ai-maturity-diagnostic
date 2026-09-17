/* Research screen — local, additive extension of shared/mock-data.js.
   Isolation rule for this delivery confines edits to research/** and
   fit/**, so shared/mock-data.js itself is never modified here. Instead
   this file extends window.GtmMockData IN PLACE, after shared/mock-data.js
   has loaded, the same way that file would have been extended per
   SHELL_CONTRACT.md §4 (additive fields on existing canonical objects,
   more instances of existing shapes, same id scheme, no new canonical
   object type, no ad hoc parallel shape). fit/fit-mock-extend.js loads
   this file too, so Company/Demand/Evidence/ResearchCase data stays a
   single source between the two screens. */
(function () {
  "use strict";

  var d = window.GtmMockData;
  if (!d) {
    throw new Error("research-mock-extend.js: shared/mock-data.js must be loaded first");
  }

  function byId(list, key, id) {
    for (var i = 0; i < list.length; i++) {
      if (list[i][key] === id) return list[i];
    }
    return null;
  }

  // -- ResearchCase: `history` is additive (Research history section on
  // the Company 360 Research tab). Nautix/Verdal cases are new instances
  // of the existing ResearchCase shape, not a new object type.
  var rcAcme = byId(d.researchCases, "research_case_id", "rc_acme");
  if (rcAcme) {
    rcAcme.history = [
      { at: "2026-09-02", actor: "alex@internal", action: "Research case ouvert" },
      { at: "2026-09-10", actor: "system", action: "Signaux sig_1/sig_2 rattachés automatiquement" },
      { at: "2026-09-14", actor: "alex@internal", action: "Section Organisation mise à jour après recoupement de l'org chart" },
    ];
  }
  d.researchCases.push(
    { research_case_id: "rc_nautix", company_id: "co_nautix", status: "not_started", owner: null, opened_at: null, coverage: "0%", history: [] },
    {
      research_case_id: "rc_verdal",
      company_id: "co_verdal",
      status: "complete",
      owner: "sam@internal",
      opened_at: "2026-04-10",
      coverage: "100%",
      history: [
        { at: "2026-04-10", actor: "sam@internal", action: "Research case ouvert" },
        { at: "2026-06-01", actor: "sam@internal", action: "Recherche marquée complète" },
      ],
    }
  );

  // -- Evidence: `section` is additive, mapping each claim to one of the 12
  // Research-tab content sections (Identity, Business model, Products &
  // services, Customers/markets, Organisation, Strategic priorities,
  // Technology, AI/transformation, Recent events, Hiring, Competitive
  // environment, Risks). Sources and Research history are rendered from
  // `evidence[].source` / ResearchCase.history instead of a claim section.
  var sections = {
    ev_1: "technology",
    ev_2: "strategic_priorities",
    ev_3: "strategic_priorities",
    ev_4: "organisation",
  };
  d.evidence.forEach(function (e) {
    if (sections[e.evidence_id]) e.section = sections[e.evidence_id];
  });
  d.evidence.push(
    { evidence_id: "ev_5", research_case_id: "rc_acme", section: "identity", statement: "Acme Corp, éditeur de logiciels industriels, siège à Lyon, ~1200 salariés", claim_type: "fact", confidence: "high", freshness: "fresh", source: "Site corporate / LinkedIn" },
    { evidence_id: "ev_6", research_case_id: "rc_acme", section: "business_model", statement: "Modèle économique principalement licences perpétuelles + support, transition SaaS amorcée", claim_type: "inference", confidence: "med", freshness: "aging", source: "Rapport annuel 2025 + offres d'emploi" },
    { evidence_id: "ev_7", research_case_id: "rc_acme", section: "products_services", statement: "Suite ERP de planification production + modules add-on qualité", claim_type: "fact", confidence: "high", freshness: "fresh", source: "Site produit" },
    { evidence_id: "ev_8", research_case_id: "rc_acme", section: "customers_markets", statement: "Clientèle principale : industrie manufacturière France/Benelux", claim_type: "fact", confidence: "med", freshness: "aging", source: "Études de cas publiées" },
    { evidence_id: "ev_9", research_case_id: "rc_acme", section: "organisation", statement: "Organisation R&D récemment réorganisée autour d'une VP Engineering unique", claim_type: "inference", confidence: "med", freshness: "fresh", source: "Signal: promotion Dubosc + org chart LinkedIn" },
    { evidence_id: "ev_10", research_case_id: "rc_acme", section: "technology", statement: "Stack data non confirmé au-delà de l'ERP legacy", claim_type: "unknown", confidence: "low", freshness: "stale", source: "—" },
    { evidence_id: "ev_11", research_case_id: "rc_acme", section: "ai_transformation", statement: "Aucune initiative IA/GenAI publique identifiée à ce jour", claim_type: "unknown", confidence: "low", freshness: "aging", source: "Veille presse + site corporate" },
    { evidence_id: "ev_12", research_case_id: "rc_acme", section: "recent_events", statement: "Promotion de la VP Engineering et 12 postes Data/Platform ouverts sur 30 jours", claim_type: "fact", confidence: "high", freshness: "fresh", source: "Signaux sig_1, sig_2" },
    { evidence_id: "ev_13", research_case_id: "rc_acme", section: "hiring", statement: "12 offres actives en Data/Platform, dont 3 postes seniors", claim_type: "fact", confidence: "high", freshness: "fresh", source: "Job boards (public)" },
    { evidence_id: "ev_14", research_case_id: "rc_acme", section: "competitive_environment", statement: "Un concurrent direct (non identifié) pourrait déjà être en cours d'évaluation", claim_type: "hypothesis", confidence: "low", freshness: "aging", source: "Non confirmé — à valider en discovery" },
    { evidence_id: "ev_15", research_case_id: "rc_acme", section: "risks", statement: "Dépendance forte à l'ERP legacy pourrait ralentir toute migration", claim_type: "inference", confidence: "med", freshness: "fresh", source: "Recoupement ev_1 + entretiens sectoriels" },
    { evidence_id: "ev_16", research_case_id: "rc_verdal", section: "identity", statement: "Verdal Énergie, opérateur énergie, ~5400 salariés, Paris", claim_type: "fact", confidence: "high", freshness: "fresh", source: "Rapport annuel 2025" },
    { evidence_id: "ev_17", research_case_id: "rc_verdal", section: "technology", statement: "Plateforme de prévision de la demande basée sur des modèles statistiques hérités", claim_type: "fact", confidence: "high", freshness: "aging", source: "Documentation technique interne partagée" },
    { evidence_id: "ev_18", research_case_id: "rc_verdal", section: "ai_transformation", statement: "Programme de modernisation IA lancé en 2025, sponsor identifié en Direction Innovation", claim_type: "fact", confidence: "high", freshness: "fresh", source: "Communiqué de presse" },
    { evidence_id: "ev_19", research_case_id: "rc_verdal", section: "risks", statement: "Périmètre réglementaire CSRD encore en discussion, pourrait retarder tout projet connexe", claim_type: "hypothesis", confidence: "med", freshness: "aging", source: "Échange commercial (non vérifié)" }
  );

  // -- Demand: `status` uses the mission's Detected/Inferred/Validated/
  // Qualified wording (lowercase, matching this fixture's other enums).
  // This progression is UI-only speculation, not a validated lifecycle —
  // see research/SCREEN_CONTRACT.md DECISION_REQUIRED #1.
  d.demands.push(
    {
      demand_id: "dem_acme_2",
      company_id: "co_acme",
      problem: "Reporting manuel multi-sites sans consolidation temps réel",
      outcome: "Consolidation du reporting mensuel en moins d'1 jour",
      status: "detected",
      confidence: "low",
      urgency: "low",
      evidence_ids: [],
      contradictions: [],
      unknowns: ["Nombre de sites concernés", "Propriétaire métier du reporting"],
    },
    {
      demand_id: "dem_nautix_1",
      company_id: "co_nautix",
      problem: "Suivi de flotte logistique sur tableurs partagés",
      outcome: "Visibilité temps réel sur les livraisons en cours",
      status: "validated",
      confidence: "high",
      urgency: "high",
      evidence_ids: [],
      contradictions: [],
      unknowns: ["Budget confirmé pour Q4"],
    },
    {
      demand_id: "dem_verdal_1",
      company_id: "co_verdal",
      problem: "Prévision de la demande énergétique sur modèles statiques hérités",
      outcome: "Prévision dynamique recalculée quotidiennement",
      status: "qualified",
      confidence: "high",
      urgency: "med",
      evidence_ids: ["ev_17"],
      contradictions: [],
      unknowns: [],
    },
    {
      demand_id: "dem_verdal_2",
      company_id: "co_verdal",
      problem: "Automatisation du reporting réglementaire CSRD",
      outcome: "Réduction du temps de reporting réglementaire de 60%",
      status: "validated",
      confidence: "med",
      urgency: "med",
      evidence_ids: ["ev_19"],
      contradictions: ["Le périmètre réglementaire exact est encore en discussion interne"],
      unknowns: ["Budget dédié"],
    }
  );
})();
