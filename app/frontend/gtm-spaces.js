(function () {
  "use strict";
  const upstream = {
    home: { title: "Home", description: "Files de travail, blockers et prochaines actions.", endpoint: "/api/follow-up" },
    discover: { title: "Discover", description: "Signaux et comptes à examiner, sans inférer la demande.", endpoint: "/api/v1/workspaces/{workspace}/signals" },
    research: { title: "Research", description: "Dossiers de recherche product-blind et preuves associées.", endpoint: "/api/v1/workspaces/{workspace}/research-cases" },
    fit: { title: "Fit", description: "Décisions explicables, gates et alternatives avant tout ciblage.", endpoint: "/api/v1/workspaces/{workspace}/fit-assessments" },
    targets: { title: "Targets", description: "Plans de compte et parties prenantes autorisés par le Fit.", endpoint: "/api/v1/workspaces/{workspace}/target-plans" },
    reach: { title: "Reach", description: "Séquences, tâches et contraintes d'exécution visibles.", endpoint: "/api/v1/workspaces/{workspace}/sequences" },
    engagement: { title: "Engagement", description: "Conversations entrantes, objections et prochaines actions.", endpoint: "/api/v1/workspaces/{workspace}/conversations" },
    pipeline: { title: "Pipeline", description: "Opportunities gouvernées de discovery à won/lost.", endpoint: "/api/v1/workspaces/{workspace}/opportunities/pipeline-board", board: true },
    insights: { title: "Insights", description: "Funnel, qualité, coûts et apprentissage gouverné, sans mutation de la vérité métier.", endpoint: "/api/v1/workspaces/{workspace}/insights", insights: true },
  };
  const escapeHtml = value => String(value ?? "").replace(/[&<>"']/g, character => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[character]));
  const itemsFrom = (payload, config) => {
    if (config.board && payload.stages) return Object.entries(payload.stages).flatMap(([status, items]) => items.map(item => ({ ...item, status })));
    return Array.isArray(payload) ? payload : (payload.items || []);
  };
  const itemId = item => item.signal_id || item.research_case_id || item.id || item.study_id || item.company_id || "item";

  async function renderInsights(container, route, request, projection) {
    const proposals = await request(`/api/v1/workspaces/${encodeURIComponent(route.workspace)}/learning-proposals`);
    const metrics = Object.fromEntries((projection.metrics || []).map(metric => [metric.metric_id, metric]));
    const value = (id, fallback = "—") => metrics[id] ? escapeHtml(Number(metrics[id].value).toLocaleString(undefined, { maximumFractionDigits: 3 })) : fallback;
    const proposalCards = (proposals.items || []).map(proposal => `<article class="card"><p class="eyebrow">${escapeHtml(proposal.origin)} · ${escapeHtml(proposal.status)}</p><h3>${escapeHtml(proposal.target.kind)} · ${escapeHtml(proposal.target.ref)}</h3><p>${escapeHtml(proposal.hypothesis)}</p><div class="meta">${proposal.experiment_id ? `Expérience ${escapeHtml(proposal.experiment_id)}` : "Revue humaine requise"}${proposal.result_ref ? ` · Résultat ${escapeHtml(proposal.result_ref)}` : ""}</div></article>`).join("");
    container.innerHTML = `<div class="section-head"><div><p class="eyebrow">${escapeHtml(route.workspace)} · projection reconstruisible</p><h2>Insights</h2><p>Funnel, qualité et coût de la cohorte. Les seuils et dimensions source, secteur et produit restent explicites.</p></div></div>
      <div class="legend"><span class="badge">${escapeHtml(projection.source_event_count)} événements</span><span class="badge">k ≥ ${escapeHtml(projection.privacy.minimum_cohort_size)}</span><span class="badge">${projection.authoritative ? "autorité" : "projection uniquement"}</span></div>
      ${projection.privacy.suppressed ? '<div class="warning-box">Cohorte masquée : volume inférieur au seuil de confidentialité.</div>' : `<div class="grid result-grid"><article class="card"><p class="eyebrow">Funnel</p><h3>${value("funnel_completion_rate")}</h3><p>Taux de complétion</p></article><article class="card"><p class="eyebrow">Qualité</p><h3>${value("quality_pass_rate")}</h3><p>Taux de passage</p></article><article class="card"><p class="eyebrow">Coût</p><h3>${value("execution_cost")}</h3><p>Unités consommées</p></article></div>`}
      <div class="section-head"><div><p class="eyebrow">LearningProposal</p><h2>Améliorations gouvernées</h2><p>Accepter autorise un test borné ; aucune règle, skill ou prompt n'est auto-modifié.</p></div><a class="primary" href="/admin/workspaces">Revoir et décider</a></div>
      <div class="grid result-grid">${proposalCards || '<div class="empty-state">Aucune proposition à examiner.</div>'}</div>`;
  }

  async function render(route, request) {
    const container = document.querySelector("#gtmSpaceContent");
    const config = upstream[route.space];
    if (!config) {
      container.innerHTML = `<div class="empty-state"><h2>${escapeHtml(route.space)}</h2><p>Cet espace arrive dans l'itération suivante.</p></div>`;
      return;
    }
    container.innerHTML = `<div class="section-head"><div><p class="eyebrow">${escapeHtml(route.workspace)}</p><h2>${config.title}</h2><p>${config.description}</p></div></div><div class="space-loading">Chargement…</div>`;
    if (!config.endpoint) {
      container.querySelector(".space-loading").outerHTML = '<div class="empty-state"><p>Les projections E13 ne modifieront aucune vérité métier.</p><a class="primary" href="/admin/workspaces">Administration workspace</a></div>';
      return;
    }
    try {
      const payload = await request(config.endpoint.replace("{workspace}", encodeURIComponent(route.workspace)));
      if (config.insights) {
        await renderInsights(container, route, request, payload);
        return;
      }
      const items = itemsFrom(payload, config);
      const cards = items.map(item => {
        const gates = (item.gates || []).map(gate => `<span class="badge ${gate.passed ? 'status-ready' : 'status-stale'}">${escapeHtml(gate.name || gate.gate_id)} · ${gate.passed ? 'pass' : 'bloqué'}</span>`).join("");
        return `<article class="card"><p class="eyebrow">${escapeHtml(item.status || item.kind || "à traiter")}</p><h3>${escapeHtml(item.name || item.title || item.company_name || itemId(item))}</h3><p>${escapeHtml(item.summary || item.reason || item.next_action || "")}</p><div class="meta">${gates}</div></article>`;
      }).join("");
      container.querySelector(".space-loading").outerHTML = `<div class="grid result-grid">${cards || '<div class="empty-state">Aucun élément dans cette file.</div>'}</div>`;
    } catch (error) {
      container.querySelector(".space-loading").outerHTML = `<div class="error" role="alert">${escapeHtml(error.message)}</div>`;
    }
  }
  window.GtmSpaces = { render };
})();
