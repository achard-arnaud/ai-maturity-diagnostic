(function () {
  "use strict";
  const upstream = {
    home: { title: "Home", description: "Files de travail, blockers et prochaines actions.", endpoint: "/api/follow-up" },
    discover: { title: "Discover", description: "Signaux et comptes à examiner, sans inférer la demande.", endpoint: "/api/v1/workspaces/{workspace}/signals" },
    research: { title: "Research", description: "Dossiers de recherche product-blind et preuves associées.", endpoint: "/api/v1/workspaces/{workspace}/research-cases" },
    fit: { title: "Fit", description: "Décisions explicables, gates et alternatives avant tout ciblage.", endpoint: "/api/v1/workspaces/{workspace}/fit-assessments" },
    targets: { title: "Targets", description: "Plans de compte et parties prenantes autorisés par le Fit.", endpoint: "/api/v1/workspaces/{workspace}/target-plans" },
    reach: { title: "Reach", description: "Séquences, tâches et contraintes d'exécution visibles.", endpoint: "/api/v1/workspaces/{workspace}/sequences" },
  };
  const escapeHtml = value => String(value ?? "").replace(/[&<>"']/g, character => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[character]));
  const itemsFrom = payload => Array.isArray(payload) ? payload : (payload.items || []);
  const itemId = item => item.signal_id || item.research_case_id || item.id || item.study_id || item.company_id || "item";

  async function render(route, request) {
    const container = document.querySelector("#gtmSpaceContent");
    const config = upstream[route.space];
    if (!config) {
      container.innerHTML = `<div class="empty-state"><h2>${escapeHtml(route.space)}</h2><p>Cet espace arrive dans l'itération suivante.</p></div>`;
      return;
    }
    container.innerHTML = `<div class="section-head"><div><p class="eyebrow">${escapeHtml(route.workspace)}</p><h2>${config.title}</h2><p>${config.description}</p></div></div><div class="space-loading">Chargement…</div>`;
    try {
      const payload = await request(config.endpoint.replace("{workspace}", encodeURIComponent(route.workspace)));
      const items = itemsFrom(payload);
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
