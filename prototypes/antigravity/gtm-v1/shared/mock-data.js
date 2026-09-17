/* GTM V1 prototype — shared, cross-linked mock data. One coherent demo
   account ("Acme Corp") threads through every screen so a reviewer can
   follow Discover -> Research -> Fit -> Targets -> Reach -> Engagement ->
   Pipeline on the same story, plus a couple of secondary accounts for
   list/table screens that need more than one row.

   Every object shape matches the canonical objects named in
   ANTIGRAVITY_00_UI_V1_MISSION.md. No new canonical object is invented
   here — where a screen needs a field this mock doesn't have, that is a
   DECISION_REQUIRED for the screen's own contract, not a silent addition
   here. See SHELL_CONTRACT.md §4. */
(function () {
  "use strict";

  var companies = [
    { company_id: "co_acme", name: "Acme Corp", sector: "Industrial software", size: "1200 employees", location: "Lyon, FR", research_status: "in_progress" },
    { company_id: "co_nautix", name: "Nautix", sector: "Logistics", size: "340 employees", location: "Nantes, FR", research_status: "not_started" },
    { company_id: "co_verdal", name: "Verdal Energie", sector: "Energy", size: "5400 employees", location: "Paris, FR", research_status: "complete" },
  ];

  var people = [
    { person_id: "pe_claire", company_id: "co_acme", name: "Claire Dubosc", title: "VP Engineering", role_status: "unverified", relationship_distance: "2nd degree" },
    { person_id: "pe_marc", company_id: "co_acme", name: "Marc Ferréol", title: "Head of Data Platform", role_status: "verified", relationship_distance: "1st degree" },
    { person_id: "pe_lina", company_id: "co_acme", name: "Lina Ouedraogo", title: "Procurement Lead", role_status: "unverified", relationship_distance: "3rd degree" },
  ];

  var signals = [
    { signal_id: "sig_1", company_id: "co_acme", kind: "job_change", summary: "Claire Dubosc promue VP Engineering", observed_at: "2026-09-01", event_date: "2026-08-15", freshness: "fresh", status: "new", source: "LinkedIn (public)" },
    { signal_id: "sig_2", company_id: "co_acme", kind: "hiring", summary: "12 offres ouvertes en Data/Platform", observed_at: "2026-09-10", event_date: "2026-09-08", freshness: "fresh", status: "reviewed", source: "Job boards (public)" },
    { signal_id: "sig_3", company_id: "co_nautix", kind: "funding", summary: "Levée Série B 22M€", observed_at: "2026-08-20", event_date: "2026-08-18", freshness: "aging", status: "new", source: "Presse" },
  ];

  var researchCases = [
    { research_case_id: "rc_acme", company_id: "co_acme", status: "in_progress", owner: "alex@internal", opened_at: "2026-09-02", coverage: "62%" },
  ];

  var evidence = [
    { evidence_id: "ev_1", research_case_id: "rc_acme", statement: "Acme utilise un ERP legacy pour la planification production", claim_type: "fact", confidence: "high", freshness: "fresh", source: "Rapport annuel 2025" },
    { evidence_id: "ev_2", research_case_id: "rc_acme", statement: "Le passage à un data platform moderne semble motivé par la promotion de C. Dubosc", claim_type: "inference", confidence: "med", freshness: "fresh", source: "Recoupement signal + org chart" },
    { evidence_id: "ev_3", research_case_id: "rc_acme", statement: "Un budget de transformation IT pourrait être débloqué au Q1", claim_type: "hypothesis", confidence: "low", freshness: "aging", source: "Non confirmé" },
    { evidence_id: "ev_4", research_case_id: "rc_acme", statement: "Sponsor budgétaire réel", claim_type: "unknown", confidence: "low", freshness: "stale", source: "—" },
  ];

  var demands = [
    {
      demand_id: "dem_acme_1",
      company_id: "co_acme",
      problem: "Planification production sur ERP legacy, cycles de décision lents",
      outcome: "Réduire le délai de replanification de 3 semaines à 3 jours",
      status: "inferred",
      confidence: "med",
      urgency: "med",
      evidence_ids: ["ev_1", "ev_2"],
      contradictions: [],
      unknowns: ["Sponsor budgétaire réel"],
    },
  ];

  var products = [{ product_id: "prod_platform", name: "Data Platform Suite" }];

  var productSnapshots = [
    { snapshot_id: "snap_platform_v3", product_id: "prod_platform", version: "v3.2", published_at: "2026-07-01", immutable: true },
  ];

  var fitAssessments = [
    {
      fit_id: "fit_acme_1",
      demand_id: "dem_acme_1",
      company_id: "co_acme",
      product_id: "prod_platform",
      snapshot_id: "snap_platform_v3",
      version: 2,
      status: "pending_review",
      overall_decision: "PURSUE (draft)",
      need_coverage: "70%",
      hard_gates_passed: true,
      matches: ["Réplanification temps réel", "Connecteurs ERP legacy"],
      gaps: ["Pas de module prévision de la demande natif"],
      contradictions: [],
      unknowns: ["Volume de données réel à ingérer"],
      alternatives: ["Module tiers de prévision en complément"],
    },
  ];

  var targetPlans = [
    {
      target_plan_id: "tp_acme_1",
      company_id: "co_acme",
      fit_id: "fit_acme_1",
      status: "draft",
      members: [
        { person_id: "pe_claire", stakeholder_role: "economic_buyer", influence: "high", authority_confidence: "med" },
        { person_id: "pe_marc", stakeholder_role: "champion", influence: "high", authority_confidence: "high" },
        { person_id: "pe_lina", stakeholder_role: "procurement", influence: "med", authority_confidence: "low" },
      ],
    },
  ];

  var sequences = [
    { sequence_id: "seq_acme_1", target_plan_id: "tp_acme_1", name: "Acme — Champion intro", status: "active", channel: "email" },
  ];

  var touchpoints = [
    { touchpoint_id: "tpt_1", sequence_id: "seq_acme_1", person_id: "pe_marc", channel: "email", step: 1, scheduled_at: "2026-09-18T09:00:00", status: "scheduled", why_now: "Signal: promotion Claire Dubosc" },
    { touchpoint_id: "tpt_2", sequence_id: "seq_acme_1", person_id: "pe_claire", channel: "linkedin_manual_task", step: 1, scheduled_at: "2026-09-18T09:05:00", status: "pending_approval", why_now: "Signal: promotion" },
  ];

  var engagementEvents = [
    { engagement_id: "eng_1", sequence_id: "seq_acme_1", person_id: "pe_marc", kind: "replied", occurred_at: "2026-09-18T14:00:00", sentiment: "positive" },
  ];

  var opportunities = [
    {
      opportunity_id: "opp_acme_1",
      company_id: "co_acme",
      demand_id: "dem_acme_1",
      fit_id: "fit_acme_1",
      target_plan_id: "tp_acme_1",
      stage: "discovery",
      owner: "alex@internal",
      value: "€120k ARR (estimate)",
      next_action: "Cadrer un pilote avec M. Ferréol",
      last_engagement: "2026-09-18",
    },
  ];

  var deals = [{ deal_id: "deal_acme_1", opportunity_id: "opp_acme_1", stage: "proposal", outcome: null }];

  var artifacts = [
    { artifact_id: "art_1", type: "research_note", company_id: "co_acme", title: "Acme — Note de recherche v1", author: "alex@internal", updated_at: "2026-09-12", version: 1 },
    { artifact_id: "art_2", type: "fit_export", company_id: "co_acme", title: "Acme — Export Fit v2", author: "system", updated_at: "2026-09-15", version: 2 },
  ];

  window.GtmMockData = {
    companies: companies,
    people: people,
    signals: signals,
    researchCases: researchCases,
    evidence: evidence,
    demands: demands,
    products: products,
    productSnapshots: productSnapshots,
    fitAssessments: fitAssessments,
    targetPlans: targetPlans,
    sequences: sequences,
    touchpoints: touchpoints,
    engagementEvents: engagementEvents,
    opportunities: opportunities,
    deals: deals,
    artifacts: artifacts,
  };
})();
