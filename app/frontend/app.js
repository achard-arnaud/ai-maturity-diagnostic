const state = {
  skills: [], offers: [], shelves: [], demand: { sectors: [] }, inventories: [],
  qualification: [], nudgeInventories: [], backlog: [], followUp: [], valueChain: [],
  selectedSkill: null, selectedSector: null, resolvers: {},
  executorConfigured: true, user: null, candidates: [], campaigns: []
};

async function api(path, options = {}) {
  const response = await fetch(path, { headers: { "Content-Type": "application/json" }, ...options });
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.error || `HTTP ${response.status}`);
  return payload;
}

function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, ch => ({ "&":"&amp;", "<":"&lt;", ">":"&gt;", '"':"&quot;", "'":"&#39;" }[ch]));
}

function showPanel(id) {
  document.querySelectorAll(".panel").forEach(p => p.classList.toggle("active", p.id === id));
  document.querySelectorAll("nav button").forEach(b => b.classList.toggle("active", b.dataset.target === id));
}

function statusClass(status) {
  return `status-${String(status || "unknown").replace(/_/g, "-")}`;
}

function ageBadge(item) {
  if (item.days_in_current_state === null || item.days_in_current_state === undefined) return "";
  const staleClass = item.is_stale ? "status-stale" : "";
  const label = item.is_stale ? `${item.days_in_current_state} j · en attente` : `${item.days_in_current_state} j`;
  return `<span class="badge badge-age ${staleClass}">${esc(label)}</span>`;
}

function openInvoke(skillId, input = "", contextPaths = []) {
  if (!skillId) return;
  state.selectedSkill = skillId;
  document.querySelector("#invokeTitle").textContent = skillId;
  document.querySelector("#invokeInput").value = input;
  document.querySelector("#contextPaths").value = (contextPaths || []).filter(Boolean).join("\n");
  document.querySelector("#invokeResult").textContent = "";
  document.querySelector("#invokeConfirmation").textContent = "";
  document.querySelector("#contactStructResult").textContent = "";
  // ADR-004: nothing actually runs unless AI_DIAGNOSTIC_SKILL_EXECUTOR is
  // configured server-side — surface that right where the user is about to
  // trigger a would-be write, not only as a global health-bar notice.
  document.querySelector("#executorBanner").classList.toggle("hidden", state.executorConfigured);
  document.querySelector("#structuredContactFields").classList.toggle("hidden", skillId !== "network-contact-intake");
  document.querySelector("#invokePanel").classList.remove("hidden");
  document.querySelector("#invokeInput").focus();
}

function openDataPanel(title, eyebrow, summary, html) {
  document.querySelector("#dataTitle").textContent = title;
  document.querySelector("#dataEyebrow").textContent = eyebrow || "Analyse";
  document.querySelector("#dataSummary").textContent = summary || "";
  document.querySelector("#dataContent").innerHTML = html || "";
  document.querySelector("#dataPanel").classList.remove("hidden");
}

function registerResolver(resolver) {
  if (!resolver) return null;
  const id = resolver.blocker_id || `resolver-${Object.keys(state.resolvers).length + 1}`;
  state.resolvers[id] = resolver;
  return id;
}

function resolverButton(resolver, label = null) {
  const id = registerResolver(resolver);
  if (!id) return "";
  return `<button class="resolverBtn primary" data-resolver="${esc(id)}">${esc(label || resolver.cta_label || "Résoudre")}</button>`;
}

function bindResolverButtons(root = document) {
  root.querySelectorAll(".resolverBtn").forEach(btn => btn.addEventListener("click", () => {
    const resolver = state.resolvers[btn.dataset.resolver];
    if (!resolver) return;
    if (resolver.owner_skill) {
      openInvoke(resolver.owner_skill, resolver.cta_input || resolver.message || "Résous ce blocker.", resolver.context_paths || []);
      return;
    }
    openDataPanel(
      resolver.cta_label || "Action humaine",
      "Résolution manuelle",
      resolver.message,
      `<div class="blocker-card"><strong>État requis</strong><p>${esc(resolver.required_state)}</p><strong>Après résolution</strong><p>${esc(resolver.postcondition)}</p><span class="badge">action humaine</span></div>`
    );
  }));
}

function blockerActionButtons(kind, target, step) {
  if (kind !== "qualification" || !target || !target.study_id || !step || !step.blocker) return "";
  return `<div class="blocker-actions">
    <button class="blockerActionBtn" data-step="${esc(step.id)}" data-action="cancel">Annuler l'étape</button>
    <button class="blockerActionBtn" data-step="${esc(step.id)}" data-action="step_back">Revenir en arrière</button>
    <button class="blockerActionBtn" data-step="${esc(step.id)}" data-action="force">Forcer (motif requis)</button>
  </div>`;
}

async function recordBlockerAction(studyId, stepId, action) {
  let reason = null;
  let target_step_id = null;
  if (action === "force") {
    reason = window.prompt("Motif obligatoire pour forcer cette étape :", "");
    if (reason === null || !reason.trim()) return;
  }
  if (action === "step_back") {
    target_step_id = window.prompt("Revenir à quelle étape (demand, snapshots, matching, contacts, reach, pilot) ?", "");
    if (!target_step_id) return;
  }
  // actor is no longer client-supplied: the server derives it from the
  // authenticated session (ADR-007 §7).
  await api("/api/qualification/actions", { method: "POST", body: JSON.stringify({ study_id: studyId, step_id: stepId, action, reason, target_step_id }) });
}

function bindBlockerActionButtons(root, kind, studyId) {
  if (kind !== "qualification" || !studyId) return;
  root.querySelectorAll(".blockerActionBtn").forEach(btn => btn.addEventListener("click", async () => {
    try {
      await recordBlockerAction(studyId, btn.dataset.step, btn.dataset.action);
      openWorkflow(kind, { study_id: studyId });
    } catch (error) {
      openDataPanel("Action bloquante", "Erreur", error.message, "");
    }
  }));
}

async function openWorkflow(kind, target) {
  const panel = document.querySelector("#workflowPanel");
  document.querySelector("#workflowSteps").innerHTML = "Chargement…";
  panel.classList.remove("hidden");
  try {
    const plan = await api("/api/workflows/plan", { method: "POST", body: JSON.stringify({ kind, ...target }) });
    document.querySelector("#workflowTitle").textContent = `${plan.label || plan.target} · ${kind}`;
    const current = plan.current
      ? Object.entries(plan.current).map(([key, value]) => `${key}: ${value ?? "—"}`).join(" · ")
      : (plan.stage ? `Étape actuelle : ${plan.stage}` : "Parcours guidé avec gates explicites.");
    document.querySelector("#workflowSummary").textContent = current;
    document.querySelector("#workflowSteps").innerHTML = (plan.steps || []).map((step, index) => {
      const blocker = step.blocker || null;
      const resolver = step.resolver || blocker;
      return `<div class="workflow-step ${statusClass(step.status)}">
        <div class="step-index">${String(index + 1).padStart(2, "0")}</div>
        <div class="step-body">
          <div class="step-title"><strong>${esc(step.id)}</strong><span class="badge">${esc(step.status)}</span></div>
          <div class="hint">${esc(step.gate || step.skill || "Revue humaine")}</div>
          ${blocker ? `<div class="inline-blocker"><strong>${esc(blocker.message)}</strong><small>Besoin : ${esc(blocker.required_state)}</small><small>Après : ${esc(blocker.postcondition)}</small></div>` : ""}
        </div>
        <div class="row-actions">
          ${resolver ? resolverButton(resolver) : (step.skill && step.status !== "locked" ? `<button class="workflowSkillBtn" data-skill="${esc(step.skill)}" data-target="${esc(plan.target)}">Préparer</button>` : "")}
          ${blockerActionButtons(kind, target, step)}
        </div>
      </div>`;
    }).join("");
    document.querySelectorAll(".workflowSkillBtn").forEach(btn => btn.addEventListener("click", () => openInvoke(
      btn.dataset.skill,
      `Poursuis le parcours ${kind} pour ${btn.dataset.target}. Respecte les gates et produis uniquement l'artefact de cette skill.`
    )));
    bindResolverButtons(document.querySelector("#workflowSteps"));
    bindBlockerActionButtons(document.querySelector("#workflowSteps"), kind, target && target.study_id);
  } catch (error) {
    document.querySelector("#workflowSteps").innerHTML = `<div class="error">${esc(error.message)}</div>`;
  }
}

function renderSkills(filter = "") {
  const needle = filter.trim().toLowerCase();
  const grid = document.querySelector("#skillGrid");
  grid.innerHTML = state.skills
    .filter(s => !needle || `${s.id} ${s.description}`.toLowerCase().includes(needle))
    .map(s => `<article class="card"><h3>${esc(s.id)}</h3><p>${esc(s.description || "Skill sans description.")}</p><div class="meta"><span class="badge">sha ${esc(s.sha256.slice(0, 10))}</span></div><button data-skill="${esc(s.id)}" class="invokeBtn">Appel unitaire</button></article>`).join("");
  grid.querySelectorAll(".invokeBtn").forEach(button => button.addEventListener("click", () => openInvoke(button.dataset.skill)));
}

function renderShelves() {
  const offersById = Object.fromEntries(state.offers.map(o => [o.offer_id, o]));
  document.querySelector("#shelfGrid").innerHTML = state.shelves.map(shelf => {
    const cards = (shelf.offer_ids || []).map(id => offersById[id]).filter(Boolean);
    return `<article class="card shelf-card"><p class="eyebrow">${esc(shelf.shelf_id)}</p><h3>${esc(shelf.name)}</h3><p>${esc(shelf.purpose || "")}</p>
      <div>${cards.map(o => `<div class="offer-row"><div><strong>${esc(o.name)}</strong><div class="meta"><span class="badge">${esc(o.offer_id)}</span><span class="badge">${esc(o.status)}</span><span>${esc(o.profile_version || "")}</span></div></div>
        <div class="row-actions"><button class="offerAuditBtn" data-offer="${esc(o.offer_id)}" data-file="${esc(o.file || "")}">Auditer / MAJ</button><button class="offerOppBtn" data-offer="${esc(o.offer_id)}">Opportunités</button><button class="offerEditBtn" data-offer="${esc(o.offer_id)}">Modifier ma fiche produit</button><button class="offerFlowBtn" data-offer="${esc(o.offer_id)}">Parcours complet</button></div></div>`).join("") || "<small>Aucune offre canonique.</small>"}</div></article>`;
  }).join("");
  document.querySelectorAll(".offerAuditBtn").forEach(btn => btn.addEventListener("click", () => openInvoke("product-icp-intelligence", `Audite ou mets à jour la vérité canonique de ${btn.dataset.offer} sans charger de compte nommé.`, btn.dataset.file ? [`product_catalog/${btn.dataset.file}`] : [])));
  document.querySelectorAll(".offerFlowBtn").forEach(btn => btn.addEventListener("click", () => openWorkflow("offer", { offer_id: btn.dataset.offer })));
  document.querySelectorAll(".offerOppBtn").forEach(btn => btn.addEventListener("click", () => openOfferOpportunities(btn.dataset.offer)));
  document.querySelectorAll(".offerEditBtn").forEach(btn => btn.addEventListener("click", () => openOfferEditForm(btn.dataset.offer)));
  const options = state.shelves.map(s => `<option value="${esc(s.shelf_id)}">${esc(s.name)}</option>`).join("");
  document.querySelector("#shelf").innerHTML = options;
  document.querySelector("#discoverShelf").innerHTML = options;
}

function openOfferOpportunities(offerId) {
  const rows = state.qualification.filter(row => row.offer_id === offerId);
  const html = rows.length ? rows.map(row => `<div class="data-row"><div><strong>${esc(row.company)}</strong><div class="meta"><span class="badge">${esc(row.decision || "no decision")}</span><span>${esc(row.stage)}</span></div></div><button class="jumpQualification" data-study="${esc(row.study_id)}">Ouvrir qualification</button></div>`).join("") : `<div class="empty-state">Aucune étude n’utilise actuellement ${esc(offerId)} comme offre sélectionnée.</div>`;
  openDataPanel(`Opportunités · ${offerId}`, "Produit → matching", "Cette vue lit les décisions des studies ; elle ne réécrit jamais le profil produit.", html);
  document.querySelectorAll(".jumpQualification").forEach(btn => btn.addEventListener("click", () => jumpToQualification(btn.dataset.study)));
}

function sectorActionLabel(sector) {
  return ({ add_contact: "Ajouter un contact", add_company: "Ajouter une entreprise", add_third_company: "Ajouter une 3e entreprise", launch_benchmark: "Lancer le benchmark", refresh_benchmark: "Rafraîchir le benchmark" })[sector.primary_action] || "Continuer";
}

function sectorStateLabel(sector) {
  return ({ empty: "vide", building: "construction", benchmark_edge: "2/3", benchmark_ready: "benchmark prêt", consolidated: "consolidé" })[sector.benchmark_state] || sector.benchmark_state;
}

function renderDemand(filter = "") {
  const needle = filter.trim().toLowerCase();
  const sectors = (state.demand.sectors || []).filter(sector => {
    const companyText = (sector.companies || []).map(c => c.company).join(" ");
    return !needle || `${sector.sector_code} ${sector.sector_name} ${sector.supersector_name} ${sector.industry_name} ${companyText}`.toLowerCase().includes(needle);
  });
  document.querySelector("#sectorGrid").innerHTML = sectors.map(sector => `<article class="card sector-card ${statusClass(sector.benchmark_state)}">
    <div class="sector-top"><div><p class="eyebrow">${esc(sector.industry_name)} · ${esc(sector.sector_code)}</p><h3>${esc(sector.sector_name)}</h3></div><span class="badge ${statusClass(sector.benchmark_state)}">${esc(sectorStateLabel(sector))}</span></div>
    <div class="metrics"><div><strong>${sector.eligible_study_count}</strong><span>/ 3 études</span></div><div><strong>${sector.mapped_company_count}</strong><span>entreprises</span></div><div><strong>${sector.use_case_count}</strong><span>use cases</span></div></div>
    <div class="card-actions"><button class="sectorDetailBtn" data-sector="${esc(sector.sector_code)}">Ouvrir</button><button class="sectorHeritageBtn" data-sector="${esc(sector.sector_code)}">Patrimoine UC</button><button class="sectorPrimaryBtn ${sector.benchmark_state === "benchmark_edge" || sector.benchmark_enabled ? "primary" : ""}" data-sector="${esc(sector.sector_code)}">${esc(sectorActionLabel(sector))}</button><button class="sectorFlowBtn" data-sector="${esc(sector.sector_code)}">Parcours complet</button></div>
  </article>`).join("");
  document.querySelectorAll(".sectorDetailBtn").forEach(btn => btn.addEventListener("click", () => openSectorDetail(btn.dataset.sector)));
  document.querySelectorAll(".sectorHeritageBtn").forEach(btn => btn.addEventListener("click", () => openSectorHeritage(btn.dataset.sector)));
  document.querySelectorAll(".sectorPrimaryBtn").forEach(btn => btn.addEventListener("click", () => runSectorPrimary(btn.dataset.sector)));
  document.querySelectorAll(".sectorFlowBtn").forEach(btn => btn.addEventListener("click", () => openWorkflow("demand", { sector_code: btn.dataset.sector })));
}

function runSectorPrimary(code) {
  const sector = (state.demand.sectors || []).find(s => s.sector_code === code);
  if (!sector) return;
  if (sector.primary_action === "launch_benchmark" || sector.primary_action === "refresh_benchmark") {
    openInvoke("sector-intelligence-consolidation", `Consolide le benchmark du secteur ICB ${sector.sector_code} — ${sector.sector_name}. Respecte le seuil de 3 études et préserve les use-case IDs par entreprise.`, sector.rollup_path ? [sector.rollup_path] : []);
  } else if (sector.primary_action === "add_third_company") {
    openInvoke("network-contact-intake", `Ajoute une nouvelle source de contact/entreprise afin de compléter le secteur ICB ${sector.sector_code}. Ne présume ni de la classification ni de la demande.`);
  } else {
    openInvoke("network-contact-intake", `Ajoute un contact ou une entreprise candidate pour développer la couverture du secteur ICB ${sector.sector_code}.`);
  }
}

function inventoryForStudy(studyId) {
  return state.inventories.find(i => i.study_id === studyId) || null;
}

function openSectorDetail(code) {
  state.selectedSector = code;
  const sector = (state.demand.sectors || []).find(s => s.sector_code === code);
  if (!sector) return;
  const companyRows = (sector.companies || []).map(company => {
    const inventory = company.study_id ? inventoryForStudy(company.study_id) : null;
    const useCases = inventory?.use_cases || [];
    return `<div class="company-row"><div class="company-main"><strong>${esc(company.company)}</strong><div class="meta"><span class="badge">ICB ${esc(company.mapping_status)}</span><span class="badge">${company.eligible ? "étude éligible" : "étude à compléter"}</span><span>${company.use_case_count} UC</span></div></div>
      <div class="row-actions">${company.study_path ? `<button class="useFlowBtn" data-study="${esc(company.study_id)}" data-path="${esc(company.study_path)}">Ajouter / MAJ use flow</button>` : ""}${company.study_id ? `<button class="companyOrgBtn" data-study="${esc(company.study_id)}" data-path="${esc(company.study_path || "")}">Organisation</button><button class="companyHeritageBtn" data-study="${esc(company.study_id)}">Patrimoine UC</button><button class="companyFlowBtn" data-study="${esc(company.study_id)}">Parcours entreprise</button><button class="companyQualBtn" data-study="${esc(company.study_id)}">Qualification</button>` : ""}</div>
      ${useCases.length ? `<div class="uc-stack">${useCases.map(uc => `<div class="uc-row"><div><strong>${esc(uc.use_case_id)} · ${esc(uc.name || uc.workflow || "use case")}</strong><div class="meta"><span>${esc(uc.line_of_business || "")}</span><span class="badge">${esc(uc.maturity || uc.evidence_status || "")}</span></div></div><div class="row-actions"><button class="valueChainBtn" data-study="${esc(company.study_id)}" data-uc="${esc(uc.use_case_id)}">Analyse chaîne de valeur</button><button class="ucGraphBtn" data-study="${esc(company.study_id)}">Relations UC</button></div></div>`).join("")}</div>` : ""}
    </div>`;
  }).join("") || `<div class="empty-state">Aucune entreprise mappée dans le runtime privé.</div>`;
  const detail = document.querySelector("#sectorDetail");
  detail.innerHTML = `<div class="section-head"><div><p class="eyebrow">Deep dive ICB ${esc(code)}</p><h3>${esc(sector.sector_name)}</h3><p>${sector.eligible_study_count}/3 études éligibles · ${sector.use_case_count} use cases recensés.</p></div><button id="closeSectorDetail" class="ghost">Fermer</button></div>
    <div class="action-row"><button id="detailPrimary" class="primary">${esc(sectorActionLabel(sector))}</button><button id="detailBenchmark" ${sector.benchmark_enabled ? "" : "disabled"}>Lancer benchmarking</button><button id="detailHeritage">Patrimoine UC secteur</button><button id="detailHarvest">Récolter / consolider use cases</button><button id="detailFlow">Parcours complet</button></div><div class="company-list">${companyRows}</div>`;
  detail.classList.remove("hidden");
  document.querySelector("#closeSectorDetail").addEventListener("click", () => detail.classList.add("hidden"));
  document.querySelector("#detailPrimary").addEventListener("click", () => runSectorPrimary(code));
  document.querySelector("#detailBenchmark").addEventListener("click", () => runSectorPrimary(code));
  document.querySelector("#detailHeritage").addEventListener("click", () => openSectorHeritage(code));
  document.querySelector("#detailFlow").addEventListener("click", () => openWorkflow("demand", { sector_code: code }));
  document.querySelector("#detailHarvest").addEventListener("click", () => {
    const firstStudy = (sector.companies || []).find(c => c.study_path);
    if (firstStudy) openInvoke("enterprise-use-case-intelligence", `Récolte ou consolide les use cases sous-jacents de ${firstStudy.company}. Préserve preuves, dépendances, maturité et feedback.`, [firstStudy.study_path]);
    else openInvoke("enterprise-use-case-intelligence", `Prépare la récolte des use cases après création d'une étude entreprise dans ${code}. Ne déduis aucun UC du secteur seul.`);
  });
  detail.querySelectorAll(".useFlowBtn").forEach(btn => btn.addEventListener("click", () => openInvoke("enterprise-use-case-intelligence", `Ajoute ou mets à jour les use flows/use cases du study ${btn.dataset.study}. Ne charge aucune offre.`, [btn.dataset.path])));
  detail.querySelectorAll(".companyOrgBtn").forEach(btn => btn.addEventListener("click", () => openInvoke("tech-leadership-org-intelligence", `Rafraîchis l'organigramme analytique et le système de décision du study ${btn.dataset.study}; distingue hiérarchie, influence, rôle et inconnues.`, btn.dataset.path ? [btn.dataset.path] : [])));
  detail.querySelectorAll(".companyHeritageBtn,.ucGraphBtn").forEach(btn => btn.addEventListener("click", () => openCompanyHeritage(btn.dataset.study)));
  detail.querySelectorAll(".companyFlowBtn").forEach(btn => btn.addEventListener("click", () => openWorkflow("company", { study_id: btn.dataset.study })));
  detail.querySelectorAll(".companyQualBtn").forEach(btn => btn.addEventListener("click", () => jumpToQualification(btn.dataset.study)));
  detail.querySelectorAll(".valueChainBtn").forEach(btn => btn.addEventListener("click", () => openValueChain(btn.dataset.study, btn.dataset.uc)));
}

async function openValueChain(studyId, useCaseId) {
  try {
    const study = await api("/api/value-chain/study", { method: "POST", body: JSON.stringify({ study_id: studyId }) });
    const uc = (study.use_cases || []).find(item => item.use_case_id === useCaseId);
    if (!uc) throw new Error(`Use case ${useCaseId} introuvable`);
    if (!uc.analysis) {
      const prepared = await api("/api/value-chain/prepare", { method: "POST", body: JSON.stringify({ study_id: studyId, use_case_id: useCaseId }) });
      openInvoke(prepared.skill, prepared.input, prepared.context_paths || []);
      return;
    }
    const a = uc.analysis;
    const list = values => (values || []).map(v => `<li>${esc(typeof v === "string" ? v : (v.label || v.statement || v.cause || JSON.stringify(v)))}</li>`).join("") || "<li>Non établi</li>";
    const html = `<div class="analysis-grid"><article class="analysis-card"><p class="eyebrow">Porter</p><h4>Chaîne opérationnelle</h4><strong>Amont</strong><ul>${list(a.porter?.upstream)}</ul><strong>Activité focale</strong><p>${esc(typeof a.porter?.focal_activity === "string" ? a.porter.focal_activity : (a.porter?.focal_activity?.label || "Non établi"))}</p><strong>Aval</strong><ul>${list(a.porter?.downstream)}</ul><strong>Support</strong><ul>${list(a.porter?.support_activities)}</ul><strong>Handoffs / contrôles</strong><ul>${list([...(a.porter?.handoffs || []), ...(a.porter?.control_points || [])])}</ul></article>
      <article class="analysis-card"><p class="eyebrow">Ishikawa</p><h4>Causes / contraintes</h4>${["people","process","technology","data","governance_control","environment_external"].map(k => `<strong>${esc(k.replace(/_/g," "))}</strong><ul>${list(a.ishikawa?.[k])}</ul>`).join("")}</article></div>
      <article class="analysis-card"><p class="eyebrow">Hypothèses adjacentes</p>${(a.adjacent_workflow_hypotheses || []).map(h => `<div class="data-row"><div><strong>${esc(h.label)}</strong><div class="hint">${esc(h.relation)} · ${esc(h.basis)}</div></div><span class="badge">hypothesis</span></div>`).join("") || "<div class='empty-state'>Aucune hypothèse adjacente.</div>"}<div class="action-row"><button id="refreshValueChain">Rafraîchir l'analyse</button><button id="validateAdjacent">Valider les workflows adjacents</button><button id="valueChainFlow">Parcours complet</button></div></article>`;
    openDataPanel(`${useCaseId} · ${uc.name}`, "Porter + Ishikawa", `Analyse evidence-bounded du study ${studyId}. Les workflows adjacents ne sont pas automatiquement des use cases.`, html);
    document.querySelector("#refreshValueChain").addEventListener("click", async () => {
      const prepared = await api("/api/value-chain/prepare", { method: "POST", body: JSON.stringify({ study_id: studyId, use_case_id: useCaseId }) });
      openInvoke(prepared.skill, prepared.input, prepared.context_paths || []);
    });
    document.querySelector("#validateAdjacent").addEventListener("click", () => openInvoke("enterprise-use-case-intelligence", `Valide ou rejette les workflows adjacents proposés autour de ${useCaseId} dans ${studyId}. Ne promeus que ceux supportés par des preuves entreprise.`, study.analysis_path ? [study.analysis_path, study.inventory_path] : [study.inventory_path]));
    document.querySelector("#valueChainFlow").addEventListener("click", () => openWorkflow("value_chain", { study_id: studyId, use_case_id: useCaseId }));
  } catch (error) {
    openDataPanel("Analyse chaîne de valeur", "Erreur", error.message, "");
  }
}

function renderGraph(heritage) {
  const graph = heritage.graph || heritage;
  const nodes = graph.nodes || [];
  const edges = graph.edges || [];
  return `<div class="graph-summary"><div class="metric-card"><strong>${nodes.length}</strong><span>nœuds</span></div><div class="metric-card"><strong>${edges.length}</strong><span>relations</span></div></div>
    <div class="graph-nodes">${nodes.map(node => `<div class="graph-node ${node.node_type === "workflow_hypothesis" ? "hypothesis-node" : ""}"><strong>${esc(node.label)}</strong><small>${esc(node.company || "")} ${node.use_case_id ? `· ${esc(node.use_case_id)}` : ""}</small></div>`).join("") || "<div class='empty-state'>Aucun nœud.</div>"}</div>
    <h4>Relations typées</h4><div class="edge-list">${edges.map(edge => `<div class="edge-row"><span class="badge">${esc(edge.relation)}</span><code>${esc(edge.source)}</code><span>→</span><code>${esc(edge.target)}</code><small>${esc(edge.basis)}</small><span class="badge">${esc(edge.confidence)}</span></div>`).join("") || "<div class='empty-state'>Aucune relation matérialisée.</div>"}</div>`;
}

function mermaidSafeId(nodeId) {
  return "N" + String(nodeId ?? "").replace(/[^A-Za-z0-9]/g, "_");
}

// Pure, direct structural mapping from the backend's derived-on-read use-case graph
// JSON (/api/uc-graph/company or /sector) into Mermaid flowchart syntax. This does not
// compute or reinterpret graph semantics (no new scoring/matching/derivation) — it only
// reshapes node_id/label/source/target/relation fields the backend already produced,
// per ADR-004 (the web layer stays a thin adapter).
function buildMermaidGraph(graph) {
  const nodes = graph.nodes || [];
  const edges = graph.edges || [];
  const lines = ["graph TD"];
  nodes.forEach(node => {
    const shape = node.node_type === "workflow_hypothesis" ? `(("${esc(node.label)}"))` : `["${esc(node.label)}"]`;
    lines.push(`  ${mermaidSafeId(node.node_id)}${shape}`);
  });
  edges.forEach(edge => {
    lines.push(`  ${mermaidSafeId(edge.source)} -->|${esc(edge.relation)}| ${mermaidSafeId(edge.target)}`);
  });
  return lines.join("\n");
}

async function openUseCaseGraph(kind, target) {
  try {
    const path = kind === "sector" ? "/api/uc-graph/sector" : "/api/uc-graph/company";
    const graph = await api(path, { method: "POST", body: JSON.stringify(target) });
    const label = graph.scope?.company || graph.scope?.sector_code || target.study_id || target.sector_code || "";
    const mermaidSource = buildMermaidGraph(graph);
    openDataPanel(
      `Graphe des use cases · ${esc(label)}`,
      "Mermaid · dérivé du graphe backend",
      `${graph.nodes.length} nœuds · ${graph.edges.length} relations. Rendu 100% client à partir du JSON /api/uc-graph, aucun recalcul métier côté frontend.`,
      `<div class="mermaid-graph"><pre class="mermaid">${mermaidSource}</pre></div>`
    );
    if (window.mermaid) {
      window.mermaid.initialize({ startOnLoad: false, theme: "neutral" });
      window.mermaid.run({ querySelector: "#dataContent .mermaid" });
    }
  } catch (error) {
    openDataPanel("Graphe des use cases", "Erreur", error.message, "");
  }
}

async function openCompanyHeritage(studyId) {
  try {
    const heritage = await api("/api/heritage/company", { method: "POST", body: JSON.stringify({ study_id: studyId }) });
    openDataPanel(`Patrimoine UC · ${heritage.scope.company || studyId}`, "Graphe dérivé", `${heritage.use_case_count} use cases · ${heritage.edge_count} relations · ${heritage.hypothesis_count} hypothèses de workflow. Aucun second store canonique.`, renderGraph(heritage));
  } catch (error) { openDataPanel("Patrimoine UC", "Erreur", error.message, ""); }
}

async function openSectorHeritage(sectorCode) {
  try {
    const heritage = await api("/api/heritage/sector", { method: "POST", body: JSON.stringify({ sector_code: sectorCode }) });
    openDataPanel(`Patrimoine UC · ICB ${sectorCode}`, "Comparaison sectorielle", `${heritage.company_count} entreprises · ${heritage.use_case_count} use cases · ${heritage.similarity_hypotheses} similitudes hypothétiques.`, `<div class="warning-box">${esc(heritage.warning)}</div>${renderGraph(heritage)}`);
  } catch (error) { openDataPanel("Patrimoine UC secteur", "Erreur", error.message, ""); }
}

function jumpToQualification(studyId) {
  showPanel("qualification");
  setTimeout(() => {
    const card = Array.from(document.querySelectorAll("[data-qualification-study]")).find(item => item.dataset.qualificationStudy === studyId);
    if (card) card.scrollIntoView({ behavior: "smooth", block: "center" });
  }, 0);
}

function renderQualification() {
  const grid = document.querySelector("#qualificationGrid");
  if (!state.qualification.length) {
    grid.innerHTML = `<div class="empty-state">Aucune étude locale disponible. Commence par le menu Demande.</div>`;
    return;
  }
  grid.innerHTML = state.qualification.map(row => {
    const blocker = row.current_blocker;
    return `<article class="card qualification-card" data-qualification-study="${esc(row.study_id)}">
      <div class="sector-top"><div><p class="eyebrow">${esc(row.study_id)}</p><h3>${esc(row.company)}</h3></div><span class="badge ${statusClass(row.stage)}">${esc(row.stage)}</span></div>
      <div class="stepper">${(row.steps || []).map(step => `<div class="mini-step ${statusClass(step.status)}"><span></span><small>${esc(step.id)}</small></div>`).join("")}</div>
      ${blocker ? `<div class="blocker-card"><p class="eyebrow">Blocker actuel</p><strong>${esc(blocker.message)}</strong><p>Besoin : ${esc(blocker.required_state)}</p><p>Après : ${esc(blocker.postcondition)}</p>${resolverButton(blocker)}</div>` : `<p class="hint">${esc(row.next_action || "Parcours complété")}</p>`}
      <div class="card-actions"><button class="companyContextBtn" data-study="${esc(row.study_id)}">Entreprise</button><button class="orgBtn" data-study="${esc(row.study_id)}" data-path="${esc(row.study_path)}">Organisation</button>${row.decision === "pursue" || row.decision === "validate" ? `<button class="reachBtn" data-study="${esc(row.study_id)}">Reach</button>` : ""}<button class="crossSellBtn" data-study="${esc(row.study_id)}">Préparer cross-sell</button><button class="qualFlowBtn" data-study="${esc(row.study_id)}">Parcours complet</button></div>
    </article>`;
  }).join("");
  bindResolverButtons(grid);
  grid.querySelectorAll(".companyContextBtn").forEach(btn => btn.addEventListener("click", () => openWorkflow("company", { study_id: btn.dataset.study })));
  grid.querySelectorAll(".orgBtn").forEach(btn => btn.addEventListener("click", () => openInvoke("tech-leadership-org-intelligence", `Rafraîchis l'organisation, le système de décision et les zones d'influence du study ${btn.dataset.study}.`, [btn.dataset.path])));
  grid.querySelectorAll(".reachBtn").forEach(btn => btn.addEventListener("click", () => openReach(btn.dataset.study)));
  grid.querySelectorAll(".crossSellBtn").forEach(btn => btn.addEventListener("click", () => launchCrossSell(btn.dataset.study)));
  grid.querySelectorAll(".qualFlowBtn").forEach(btn => btn.addEventListener("click", () => openWorkflow("qualification", { study_id: btn.dataset.study })));
}

async function openReach(studyId) {
  try {
    const reach = await api("/api/reach/preview", { method: "POST", body: JSON.stringify({ study_id: studyId }) });
    const byWave = wave => (reach.stakeholders || []).filter(item => item.wave === wave);
    const lane = (title, wave) => `<article class="analysis-card"><p class="eyebrow">${esc(title)}</p>${byWave(wave).map(item => `<div class="stakeholder-row"><div><strong>${esc(item.person_id)}</strong><div class="meta">${(item.stakeholder_roles || []).map(role => `<span class="badge">${esc(role)}</span>`).join("")}<span class="badge ${statusClass(item.status)}">${esc(item.status)}</span></div><small>${esc(item.why_person || "")}</small>${item.why_now ? `<small>Why now: ${esc(item.why_now)}</small>` : ""}</div></div>`).join("") || "<div class='empty-state'>Aucun candidat.</div>"}</article>`;
    const blockers = (reach.blockers || []).map(b => `<div class="blocker-card"><strong>${esc(b.message)}</strong><p>${esc(b.required_state)}</p>${resolverButton(b)}</div>`).join("");
    const html = `<div class="analysis-grid three-cols">${lane("First wave", "first")}${lane("Second wave", "second")}${lane("Validation only", "validation_only")}</div>${blockers ? `<h4>Blockers / actions</h4>${blockers}` : ""}<div class="action-row"><button id="prepareReach" class="primary">Préparer l'artefact reach</button><button id="reachFlow">Parcours reach</button></div>`;
    openDataPanel(`Reach · ${reach.company || studyId}`, "Entreprise × produit × ICP × personnes", `${reach.offer_id} · ${reach.fit_decision}. Newsflow = timing/angle uniquement ; aucun envoi outbound.`, html);
    bindResolverButtons(document.querySelector("#dataContent"));
    document.querySelector("#prepareReach").addEventListener("click", async () => {
      const prepared = await api("/api/reach/prepare", { method: "POST", body: JSON.stringify({ study_id: studyId }) });
      openInvoke(prepared.skill, prepared.input, prepared.context_paths || []);
      if (prepared.written) {
        document.querySelector("#invokeConfirmation").textContent = `Brouillon écrit : ${prepared.artifact_path}`;
      }
    });
    document.querySelector("#reachFlow").addEventListener("click", () => openWorkflow("reach", { study_id: studyId }));
  } catch (error) {
    openDataPanel("Reach", "Blocage", error.message, `<button id="openQualificationFromReach" class="primary">Revenir à la qualification</button>`);
    document.querySelector("#openQualificationFromReach").addEventListener("click", () => jumpToQualification(studyId));
  }
}

function renderNudgeInventory() {
  const select = document.querySelector("#nudgeInventory");
  select.innerHTML = state.nudgeInventories.length ? state.nudgeInventories.map(item => `<option value="${esc(item.study_id)}">${esc(item.company)} · ${item.use_case_count} UC</option>`).join("") : `<option value="">Aucun inventaire</option>`;
}

function nudgeDecisionButtons(studyId, nudge) {
  if (nudge.status === "accepted") return `<span class="badge badge-accepted">Acceptée · ${esc(nudge.decided_by || "")}</span>`;
  if (nudge.status === "rejected") return `<span class="badge badge-rejected">Rejetée · ${esc(nudge.decided_by || "")}</span>`;
  return `<div class="nudge-actions">
    <button class="nudgeDecisionBtn" data-study-id="${esc(studyId)}" data-nudge-id="${esc(nudge.nudge_id)}" data-decision="accept">Accepter</button>
    <button class="nudgeDecisionBtn" data-study-id="${esc(studyId)}" data-nudge-id="${esc(nudge.nudge_id)}" data-decision="reject">Rejeter</button>
  </div>`;
}

// C2 (red-team-spec): a lightweight human acknowledgment on the falsifier text
// -- ticking this only records that a human read and considered it (via
// POST /api/nudges/{id}/ack-falsifier); it never changes the nudge's
// accept/reject status. Once acknowledged it stays a plain confirmation, not
// an interactive control, mirroring accept/reject's own first-decision-wins
// display pattern above.
function falsifierBlock(studyId, nudge) {
  const label = esc(nudge.falsifier || "");
  if (nudge.falsifier_acknowledged) {
    return `<div class="falsifier-callout falsifier-acknowledged"><strong>Falsifier :</strong> ${label}<br><small>Vérifié par ${esc(nudge.falsifier_acknowledged_by || "")}</small></div>`;
  }
  return `<div class="falsifier-callout"><strong>Falsifier :</strong> ${label}<br>
    <label><input type="checkbox" class="falsifierAckCheckbox" data-study-id="${esc(studyId)}" data-nudge-id="${esc(nudge.nudge_id)}"> J'ai vérifié ce falsifier</label>
  </div>`;
}

async function generateNudges(mode) {
  const studyId = document.querySelector("#nudgeInventory").value;
  if (!studyId) return;
  const results = document.querySelector("#nudgeResults");
  results.innerHTML = `<div class="empty-state">Calcul…</div>`;
  try {
    const payload = await api("/api/nudging/generate", { method: "POST", body: JSON.stringify({ study_id: studyId, mode }) });
    results.innerHTML = (payload.nudges || []).map(n => `<article class="card"><p class="eyebrow">${esc(n.mode)}</p><h3>${esc((n.target_use_case_ids || []).join(" + "))}</h3><p>${esc(n.rationale)}</p><div class="meta"><span class="badge">${esc(n.status)}</span><span class="badge">${esc(n.confidence)}</span></div>${falsifierBlock(studyId, n)}${nudgeDecisionButtons(studyId, n)}</article>`).join("") || `<div class="empty-state">Aucune piste admissible avec les preuves actuelles.</div>`;
    results.querySelectorAll(".nudgeDecisionBtn").forEach(btn => {
      btn.addEventListener("click", () => decideNudge(btn.dataset.studyId, btn.dataset.nudgeId, btn.dataset.decision, mode));
    });
    results.querySelectorAll(".falsifierAckCheckbox").forEach(box => {
      box.addEventListener("change", () => ackFalsifier(box.dataset.studyId, box.dataset.nudgeId, mode));
    });
  } catch (error) { results.innerHTML = `<div class="error">${esc(error.message)}</div>`; }
}

async function decideNudge(studyId, nudgeId, decision, mode) {
  try {
    const body = { study_id: studyId };
    if (decision === "reject") {
      const reason = window.prompt("Motif du rejet (optionnel)") || undefined;
      if (reason) body.reason = reason;
    }
    await api(`/api/nudges/${encodeURIComponent(nudgeId)}/${decision}`, { method: "POST", body: JSON.stringify(body) });
    generateNudges(mode);
  } catch (error) { window.alert(error.message); }
}

async function ackFalsifier(studyId, nudgeId, mode) {
  try {
    await api(`/api/nudges/${encodeURIComponent(nudgeId)}/ack-falsifier`, { method: "POST", body: JSON.stringify({ study_id: studyId }) });
    generateNudges(mode);
  } catch (error) { window.alert(error.message); }
}

function renderFollowUp() {
  const grid = document.querySelector("#followUpGrid");
  const business = state.followUp.filter(item => item.kind !== "technical_todo");
  grid.innerHTML = business.length ? business.map(item => `<article class="card follow-card"><div class="sector-top"><div><p class="eyebrow">${esc(item.kind)} · ${esc(item.priority)}</p><h3>${esc(item.label)}</h3></div><span class="badge ${statusClass(item.state)}">${esc(item.state)}</span></div><p>${esc(item.message)}</p><div class="meta">${ageBadge(item)}</div>${item.resolver ? resolverButton(item.resolver) : ""}<button class="followNavBtn" data-menu="${esc(item.navigation?.menu || "backlog")}" data-study="${esc(item.navigation?.study_id || "")}" data-sector="${esc(item.navigation?.sector_code || "")}">Ouvrir le contexte</button></article>`).join("") : `<div class="empty-state">Aucune action métier pending dans les données locales.</div>`;
  bindResolverButtons(grid);
  grid.querySelectorAll(".followNavBtn").forEach(btn => btn.addEventListener("click", () => {
    if (btn.dataset.menu === "qualification" && btn.dataset.study) return jumpToQualification(btn.dataset.study);
    showPanel(btn.dataset.menu === "followup" ? "backlog" : btn.dataset.menu);
    if (btn.dataset.sector) openSectorDetail(btn.dataset.sector);
  }));
}

function renderBacklog() {
  document.querySelector("#backlogRows").innerHTML = state.backlog.filter(item => item.status !== "completed").sort((a,b) => String(a.priority).localeCompare(String(b.priority))).map(item => `<tr><td>${esc(item.id)}</td><td>${esc(item.priority)}</td><td>${esc(item.status)}</td><td>${esc(item.area)}</td><td>${esc(item.task)}</td></tr>`).join("");
}

// ------------------------------------------------------------------
// Kanban board (GET /api/kanban/board) — real columns/cards, no drag-drop.
// Mounted identically into Demande/Qualification/Suivi so it's reachable
// from wherever the user already is, per the sprint's item 6.
// ------------------------------------------------------------------
function renderKanbanInto(containerId, board) {
  const el = document.querySelector(`#${containerId}`);
  if (!el) return;
  const columns = (board && board.columns) || [];
  el.innerHTML = columns.map(col => `<div class="kanban-column">
    <h4><span>${esc(col.stage)}</span><span class="badge">${(col.cards || []).length}</span></h4>
    ${(col.cards || []).map(card => `<div class="kanban-card"><strong>${esc(card.company || card.study_id || card.label || "—")}</strong><span class="hint">${esc(card.study_id || "")}</span></div>`).join("") || "<div class='hint'>Vide</div>"}
  </div>`).join("") || "<div class='empty-state'>Aucune donnée de pipeline.</div>";
}

async function loadKanban() {
  try {
    const board = await api("/api/kanban/board");
    state.kanban = board;
    renderKanbanInto("kanbanDemandBoard", board);
    renderKanbanInto("kanbanQualificationBoard", board);
    renderKanbanInto("kanbanFullBoard", board);
  } catch (error) {
    ["kanbanDemandBoard", "kanbanQualificationBoard", "kanbanFullBoard"].forEach(id => {
      const el = document.querySelector(`#${id}`);
      if (el) el.innerHTML = `<div class="error">${esc(error.message)}</div>`;
    });
  }
}

// ------------------------------------------------------------------
// Catalog search CTA (GET /api/catalog/search) — Offres tab.
// ------------------------------------------------------------------
async function runCatalogSearch() {
  const query = document.querySelector("#catalogSearchQuery").value.trim();
  const container = document.querySelector("#catalogSearchResults");
  container.innerHTML = "<div class='empty-state'>Recherche…</div>";
  try {
    const results = await api(`/api/catalog/search?q=${encodeURIComponent(query)}`);
    container.innerHTML = results.map(r => `<article class="card"><p class="eyebrow">${esc(r.category || "")}</p><h3>${esc(r.name || r.offer_id)}</h3><p>${esc(r.one_liner || r.status || "")}</p><div class="meta"><span class="badge">${esc(r.offer_id)}</span><span class="badge">${esc(r.status || "")}</span></div><button class="viewCatalogResult" data-offer="${esc(r.offer_id)}">Voir / promouvoir</button></article>`).join("") || "<div class='empty-state'>Aucun résultat.</div>";
    container.querySelectorAll(".viewCatalogResult").forEach(btn => btn.addEventListener("click", () => openOfferOpportunities(btn.dataset.offer)));
  } catch (error) { container.innerHTML = `<div class="error">${esc(error.message)}</div>`; }
}

// ------------------------------------------------------------------
// Staged candidate promotion (GET /api/catalog/candidates, POST .../promote)
// and PO offer-sheet edit (PATCH /api/catalog/offers/{id}) — Offres tab.
// ------------------------------------------------------------------
async function loadCandidates() {
  const grid = document.querySelector("#candidatesGrid");
  const params = new URLSearchParams({
    text: document.querySelector("#candidatesFilterText")?.value.trim() || "",
    promotion_status: document.querySelector("#candidatesFilterStatus")?.value.trim() || "",
    shelf_id: document.querySelector("#candidatesFilterShelf")?.value.trim() || "",
    company: document.querySelector("#candidatesFilterCompany")?.value.trim() || "",
  });
  for (const key of [...params.keys()]) { if (!params.get(key)) params.delete(key); }
  try {
    const candidates = await api(`/api/catalog/candidates${params.toString() ? `?${params}` : ""}`);
    state.candidates = candidates;
    grid.innerHTML = candidates.map(c => `<article class="card candidateCard" data-id="${esc(c.id)}"><p class="eyebrow">${esc(c.company)} · ${esc(c.shelf_id)}</p><h3>${esc(c.name || c.candidate_id)}</h3><p>${(c.raw_claims || []).join(" ") || "Aucun claim capturé."}</p><div class="meta"><span class="badge">${esc(c.promotion_status || "unreviewed")}</span></div><button class="viewCandidateBtn" data-id="${esc(c.id)}">Voir le détail</button> <button class="promoteCandidateBtn primary" data-id="${esc(c.id)}">Promouvoir</button></article>`).join("") || "<div class='empty-state'>Aucun candidat stagé.</div>";
    grid.querySelectorAll(".promoteCandidateBtn").forEach(btn => btn.addEventListener("click", event => { event.stopPropagation(); promoteCandidate(btn.dataset.id); }));
    grid.querySelectorAll(".viewCandidateBtn").forEach(btn => btn.addEventListener("click", event => { event.stopPropagation(); openCandidateDetail(btn.dataset.id); }));
  } catch (error) { grid.innerHTML = `<div class="error">${esc(error.message)}</div>`; }
}

async function openCandidateDetail(candidateId) {
  try {
    const c = await api(`/api/catalog/candidates/${encodeURIComponent(candidateId)}`);
    const claims = (c.raw_claims || []).map(claim => `<li>${esc(claim)}</li>`).join("") || "<li>Aucun claim capturé.</li>";
    const html = `
      <p><strong>Entreprise :</strong> ${esc(c.company)} · <strong>Rayon :</strong> ${esc(c.shelf_id)}</p>
      <p><strong>Statut :</strong> ${esc(c.promotion_status || "unreviewed")}</p>
      <p><strong>Source :</strong> ${c.source_url ? `<a href="${esc(c.source_url)}" target="_blank" rel="noopener">${esc(c.source_url)}</a>` : "Aucune"}</p>
      <p><strong>Raw claims :</strong></p>
      <ul>${claims}</ul>
      <p><strong>Source metadata :</strong></p>
      <pre>${esc(JSON.stringify(c.source_metadata || {}, null, 2))}</pre>
      <button class="promoteCandidateBtn primary" data-id="${esc(c.id)}">Promouvoir</button>
    `;
    openDataPanel(`Candidat · ${c.name || c.candidate_id}`, "Revue avant promotion", "Contenu complet du candidat stagé, avant tout engagement de promotion.", html);
    document.querySelector("#dataContent .promoteCandidateBtn").addEventListener("click", () => promoteCandidate(c.id));
  } catch (error) { openDataPanel("Candidat", "Erreur", error.message, ""); }
}

async function promoteCandidate(candidateId) {
  const offerId = window.prompt("Identifiant de la nouvelle offre canonique (offer_id) :", "");
  if (!offerId) return;
  try {
    const offer = await api(`/api/catalog/candidates/${encodeURIComponent(candidateId)}/promote`, { method: "POST", body: JSON.stringify({ offer_id: offerId }) });
    openDataPanel(`Offre promue · ${offer.offer_id}`, "Publiée au catalogue", "Statut draft, unknowns honnêtes conservés.", `<pre>${esc(JSON.stringify(offer, null, 2))}</pre>`);
    loadCandidates();
    boot();
  } catch (error) { openDataPanel("Promotion", "Erreur", error.message, ""); }
}

function openOfferEditForm(offerId) {
  const html = `<form id="offerEditForm" class="form">
    <label>Positioning (one-liner)<input id="editPositioning"></label>
    <label>Problem (canonical)<input id="editProblem"></label>
    <label>Outcomes primaires (séparés par ;)<input id="editOutcomes"></label>
    <label>ICP must-have (séparés par ;)<input id="editIcp"></label>
    <button class="primary" type="submit">Enregistrer les modifications</button>
  </form><div id="offerEditResult" class="hint"></div>`;
  openDataPanel(`Modifier ma fiche produit · ${offerId}`, "Éditer l'offre", "Seuls positioning/problem/outcomes/icp/name/category sont éditables ici ; hard_gates et proof restent protégés.", html);
  document.querySelector("#offerEditForm").addEventListener("submit", async event => {
    event.preventDefault();
    const updates = {
      positioning: { one_liner: document.querySelector("#editPositioning").value },
      problem: { canonical: document.querySelector("#editProblem").value },
      outcomes: { primary: document.querySelector("#editOutcomes").value.split(";").map(s => s.trim()).filter(Boolean) },
      icp: { maturity: { must_have: document.querySelector("#editIcp").value.split(";").map(s => s.trim()).filter(Boolean) } },
    };
    const out = document.querySelector("#offerEditResult");
    out.textContent = "Enregistrement…";
    try {
      const offer = await api(`/api/catalog/offers/${encodeURIComponent(offerId)}`, { method: "PATCH", body: JSON.stringify({ updates }) });
      out.innerHTML = `<div class="confirmation-banner">Fiche mise à jour.</div>`;
      Object.assign(state, {});
      boot();
    } catch (error) { out.textContent = error.message; }
  });
}

// ------------------------------------------------------------------
// Network people/companies search (GET /api/network/people|companies) —
// Réseau tab.
// ------------------------------------------------------------------
async function runPeopleSearch() {
  const params = new URLSearchParams({
    text: document.querySelector("#peopleText").value.trim(),
    status: document.querySelector("#peopleStatus").value.trim(),
    role: document.querySelector("#peopleRole").value.trim(),
    workspace_id: document.querySelector("#peopleWorkspace").value.trim(),
    stale: document.querySelector("#peopleStale").checked ? "true" : "",
  });
  const container = document.querySelector("#peopleResults");
  container.innerHTML = "<div class='empty-state'>Recherche…</div>";
  try {
    const people = await api(`/api/network/people?${params.toString()}`);
    container.innerHTML = people.map(p => `<article class="card"><p class="eyebrow">${esc(p.seed_company_id || "")}</p><h3>${esc(p.display_name)}</h3><div class="meta"><span class="badge">${esc(p.status || "")}</span>${(p.role_hypotheses || []).map(r => `<span class="badge">${esc(typeof r === "string" ? r : r.role || "")}</span>`).join("")}</div></article>`).join("") || "<div class='empty-state'>Aucune personne trouvée.</div>";
  } catch (error) { container.innerHTML = `<div class="error">${esc(error.message)}</div>`; }
}

async function runCompaniesSearch() {
  const params = new URLSearchParams({
    text: document.querySelector("#companiesText").value.trim(),
    sector: document.querySelector("#companiesSector").value.trim(),
    workspace_id: document.querySelector("#companiesWorkspace").value.trim(),
  });
  const container = document.querySelector("#companiesResults");
  container.innerHTML = "<div class='empty-state'>Recherche…</div>";
  try {
    const companies = await api(`/api/network/companies?${params.toString()}`);
    container.innerHTML = companies.map(c => `<article class="card"><p class="eyebrow">${esc(c.workspace_id || "")}</p><h3>${esc(c.canonical_name)}</h3><div class="meta"><span class="badge">${esc(c.status || "")}</span></div><button class="open360Btn" data-company="${esc(c.company_id)}">Vue 360</button></article>`).join("") || "<div class='empty-state'>Aucune entreprise trouvée.</div>";
    container.querySelectorAll(".open360Btn").forEach(btn => btn.addEventListener("click", () => openAccount360(btn.dataset.company)));
  } catch (error) { container.innerHTML = `<div class="error">${esc(error.message)}</div>`; }
}

// ------------------------------------------------------------------
// Account 360 view (GET /api/accounts/{company_id}/360) + admin reassign.
// ------------------------------------------------------------------
async function openAccount360(companyId) {
  try {
    const account = await api(`/api/accounts/${encodeURIComponent(companyId)}/360`);
    const company = account.company || {};
    const people = account.people || [];
    const reassignHtml = state.user && state.user.is_admin ? `<div class="action-row"><input id="reassignWorkspace" placeholder="nouveau workspace_id"><button id="reassignBtn">Réassigner</button></div>` : "";
    const html = `<div class="analysis-card"><p class="eyebrow">Entreprise</p><strong>${esc(company.canonical_name || companyId)}</strong><p>${esc(company.workspace_id || "")}</p>${reassignHtml}</div>
      <div class="analysis-card"><p class="eyebrow">Personnes (${people.length})</p>${people.map(p => `<div class="data-row"><strong>${esc(p.display_name)}</strong><span class="badge">${esc(p.status || "")}</span></div>`).join("") || "<div class='empty-state'>Aucune personne.</div>"}</div>
      <div class="analysis-card"><p class="eyebrow">Qualification</p>${account.qualification ? `<span class="badge">${esc(account.qualification.stage)}</span>` : "<div class='empty-state'>Aucune étude.</div>"}</div>
      <div class="analysis-card"><p class="eyebrow">Reach</p>${account.reach ? `<span class="badge">${esc(account.reach.status)}</span>` : "<div class='empty-state'>Pas de statut reach.</div>"}</div>
      <div class="analysis-card"><p class="eyebrow">Actions récentes</p>${(account.recent_actions || []).map(a => `<div class="data-row"><span>${esc(a.action)}</span><small>${esc(a.timestamp || "")}</small></div>`).join("") || "<div class='empty-state'>Aucune action récente.</div>"}</div>`;
    openDataPanel(`Vue 360 · ${company.canonical_name || companyId}`, "Compte", "Agrégation lecture seule : entreprise, personnes, qualification, reach, actions récentes.", html);
    const reassignBtn = document.querySelector("#reassignBtn");
    if (reassignBtn) reassignBtn.addEventListener("click", async () => {
      const workspace_id = document.querySelector("#reassignWorkspace").value.trim();
      if (!workspace_id) return;
      try {
        await api(`/admin/network/companies/${encodeURIComponent(companyId)}/reassign`, { method: "POST", body: JSON.stringify({ workspace_id }) });
        openAccount360(companyId);
      } catch (error) { window.alert(error.message); }
    });
  } catch (error) {
    openDataPanel("Vue 360", "Erreur", error.message, "");
  }
}

// ------------------------------------------------------------------
// Duplicate detection (GET /api/network/duplicates) — Réseau tab.
// ------------------------------------------------------------------
async function loadDuplicates() {
  const container = document.querySelector("#duplicatesResults");
  container.innerHTML = "<div class='empty-state'>Détection…</div>";
  try {
    const groups = await api("/api/network/duplicates");
    container.innerHTML = groups.map(g => `<article class="card" data-group-key="${esc(g.group_key || "")}"><p class="eyebrow">${esc(g.normalized_name || "")}</p>${(g.records || g.people || []).map(r => `<div class="data-row"><span>${esc(r.display_name || r.person_id)}</span><span class="badge">${esc(r.seed_company_id || "")}</span></div>`).join("")}${g.group_key ? `<button class="dismissDuplicateBtn" data-group-key="${esc(g.group_key)}" data-person-ids="${esc((g.records || []).map(r => r.person_id).join(","))}">Pas un doublon</button>` : ""}</article>`).join("") || "<div class='empty-state'>Aucun doublon potentiel détecté.</div>";
    container.querySelectorAll(".dismissDuplicateBtn").forEach(btn => {
      btn.addEventListener("click", () => dismissDuplicate(btn.dataset.personIds.split(",").filter(Boolean)));
    });
  } catch (error) { container.innerHTML = `<div class="error">${esc(error.message)}</div>`; }
}

// C3 (red-team-side-story): persists a human's "not a duplicate" decision
// (POST /api/network/duplicates/dismiss) so the group stops reappearing on
// future detection runs; it never merges or otherwise touches the person
// records themselves.
async function dismissDuplicate(personIds) {
  try {
    await api("/api/network/duplicates/dismiss", { method: "POST", body: JSON.stringify({ person_ids: personIds }) });
    loadDuplicates();
  } catch (error) { window.alert(error.message); }
}

// ------------------------------------------------------------------
// Prospecting campaigns (POST /api/campaigns/prospecting, GET /api/campaigns)
// and cross-sell prep (POST /api/campaigns/cross-sell).
// ------------------------------------------------------------------
async function loadCampaigns() {
  const container = document.querySelector("#campaignsList");
  try {
    const campaigns = await api("/api/campaigns");
    state.campaigns = campaigns;
    container.innerHTML = campaigns.map(c => {
      const markSentBtn = c.kind === "prospecting" && c.status === "draft"
        ? `<button class="markCampaignSentBtn" data-campaign-id="${esc(c.campaign_id)}">Marquer envoyée</button>`
        : "";
      return `<article class="card"><p class="eyebrow">${esc(c.kind || "")}</p><h3>${esc(c.name || c.campaign_id)}</h3><span class="badge">${esc(c.status || "")}</span>${markSentBtn}</article>`;
    }).join("") || "<div class='empty-state'>Aucune campagne.</div>";
    container.querySelectorAll(".markCampaignSentBtn").forEach(btn => {
      btn.addEventListener("click", () => markCampaignSent(btn.dataset.campaignId));
    });
  } catch (error) { container.innerHTML = `<div class="error">${esc(error.message)}</div>`; }
}

async function markCampaignSent(campaignId) {
  try {
    await api(`/api/campaigns/${encodeURIComponent(campaignId)}/mark-sent`, { method: "POST", body: JSON.stringify({}) });
    loadCampaigns();
  } catch (error) { window.alert(error.message); }
}

async function launchProspectingCampaign() {
  const name = document.querySelector("#campaignName").value.trim();
  const entity = document.querySelector("#campaignEntity").value;
  const text = document.querySelector("#campaignText").value.trim();
  const workspace_id = document.querySelector("#campaignWorkspace").value.trim();
  const criteria = { entity };
  if (text) criteria.text = text;
  if (workspace_id) criteria.workspace_id = workspace_id;
  try {
    await api("/api/campaigns/prospecting", { method: "POST", body: JSON.stringify({ name, criteria }) });
    loadCampaigns();
  } catch (error) { window.alert(error.message); }
}

async function launchCrossSell(studyId) {
  try {
    const result = await api("/api/campaigns/cross-sell", { method: "POST", body: JSON.stringify({ study_id: studyId }) });
    openDataPanel(`Cross-sell prep · ${studyId}`, "Nudging → campagne", "Préparation cross-sell à partir des use cases déjà catalogués.", `<pre>${esc(JSON.stringify(result, null, 2))}</pre>`);
    loadCampaigns();
  } catch (error) { openDataPanel("Cross-sell", "Erreur", error.message, ""); }
}

async function checkAuth() {
  try {
    const response = await fetch("/api/auth/me", { headers: { "Content-Type": "application/json" } });
    if (response.status === 401) {
      window.location.href = "/login.html";
      return null;
    }
    if (!response.ok) return null;
    return await response.json();
  } catch (error) {
    return null;
  }
}

function renderUserBar(user) {
  const bar = document.querySelector("#userBar");
  if (!bar) return;
  if (!user) { bar.textContent = ""; return; }
  const role = user.is_admin ? "admin" : (user.role || "sans rôle");
  const adminLink = user.is_admin ? ` <a class="admin-link" href="/admin/workspaces">Admin</a>` : "";
  bar.innerHTML = `<span class="user-email">${esc(user.email)}</span> <span class="badge">${esc(role)}</span>${user.workspace_id ? ` <span class="user-workspace">${esc(user.workspace_id)}</span>` : ""}${adminLink} <a id="logoutLink" href="/auth/logout">Se déconnecter</a>`;
  const logoutLink = document.querySelector("#logoutLink");
  if (logoutLink) {
    logoutLink.addEventListener("click", event => {
      event.preventDefault();
      fetch("/auth/logout", { method: "POST" }).finally(() => { window.location.href = "/login.html"; });
    });
  }
}

async function boot() {
  const user = await checkAuth();
  if (!user) return; // checkAuth already redirected to /login.html on 401
  state.user = user;
  renderUserBar(user);
  try {
    const [health, skills, offers, shelves, demand, inventories, qualification, nudgeInventories, backlog, followUp, valueChain] = await Promise.all([
      api("/api/health"), api("/api/skills"), api("/api/offers"), api("/api/shelves"), api("/api/demand"), api("/api/demand/inventories"), api("/api/qualification"), api("/api/nudging/inventories"), api("/api/backlog"), api("/api/follow-up"), api("/api/value-chain")
    ]);
    document.querySelector("#health").textContent = health.executor_configured ? `v${health.version} · Executor connecté` : `v${health.version} · Executor à configurer`;
    state.executorConfigured = !!health.executor_configured;
    Object.assign(state, { skills, offers, shelves, demand, inventories, qualification, nudgeInventories, backlog, followUp, valueChain });
    renderSkills(); renderShelves(); renderDemand(); renderQualification(); renderNudgeInventory(); renderFollowUp(); renderBacklog();
    loadKanban(); loadCandidates(); loadCampaigns(); loadBlockerActions();
  } catch (error) {
    document.querySelector("#health").textContent = "Erreur de chargement";
    console.error(error);
  }
}

document.querySelectorAll("nav button").forEach(button => button.addEventListener("click", () => showPanel(button.dataset.target)));
document.querySelector("#sectorFilter").addEventListener("input", event => renderDemand(event.target.value));
document.querySelector("#skillFilter").addEventListener("input", event => renderSkills(event.target.value));
document.querySelector("#globalAddContact").addEventListener("click", () => openInvoke("network-contact-intake", "Ajoute et normalise une nouvelle source de contacts/entreprises. Ne déduis ni ICB, ni demande, ni fit depuis les titres."));
document.querySelector("#closeInvoke").addEventListener("click", () => document.querySelector("#invokePanel").classList.add("hidden"));
document.querySelector("#closeWorkflow").addEventListener("click", () => document.querySelector("#workflowPanel").classList.add("hidden"));
document.querySelector("#closeData").addEventListener("click", () => document.querySelector("#dataPanel").classList.add("hidden"));
document.querySelector("#runSkill").addEventListener("click", async () => {
  const result = document.querySelector("#invokeResult"); result.textContent = "Exécution…";
  const confirmation = document.querySelector("#invokeConfirmation"); confirmation.textContent = "";
  try {
    const context_paths = document.querySelector("#contextPaths").value.split("\n").map(x => x.trim()).filter(Boolean);
    const payload = await api(`/api/skills/${encodeURIComponent(state.selectedSkill)}/invoke`, { method: "POST", body: JSON.stringify({ input: document.querySelector("#invokeInput").value, context_paths }) });
    result.textContent = JSON.stringify(payload, null, 2);
    document.querySelector("#executorBanner").classList.toggle("hidden", !!payload.executor_configured);
    if (payload.executor_configured && payload.status === "completed") {
      confirmation.textContent = state.selectedSkill === "network-contact-intake" ? "Contact créé (exécuteur exécuté)." : "Invocation exécutée.";
    }
  } catch (error) { result.textContent = error.message; }
});

document.querySelector("#createContactDirect").addEventListener("click", async () => {
  const out = document.querySelector("#contactStructResult");
  const name = document.querySelector("#contactStructName").value.trim();
  const company = document.querySelector("#contactStructCompany").value.trim();
  if (!name || !company) { out.textContent = "Nom et entreprise sont requis."; return; }
  out.textContent = "Création…";
  try {
    const person = await api("/api/network/people", { method: "POST", body: JSON.stringify({ display_name: name, seed_company_id: company, source: "manual_entry" }) });
    out.innerHTML = `<div class="confirmation-banner">Contact créé — ${esc(person.display_name || name)} (${esc(person.person_id || "")})</div>`;
  } catch (error) { out.textContent = error.message; }
});

document.querySelector("#discoverForm").addEventListener("submit", async event => {
  event.preventDefault(); const result = document.querySelector("#discoverResult"); result.textContent = "Découverte…";
  try {
    const payload = await api("/api/catalog/discover", { method: "POST", body: JSON.stringify({ company: document.querySelector("#discoverCompany").value, shelf_id: document.querySelector("#discoverShelf").value, domain: document.querySelector("#discoverDomain").value, source: "web", persist: true }) });
    result.textContent = JSON.stringify(payload, null, 2);
  } catch (error) { result.textContent = error.message; }
});

document.querySelector("#harvestForm").addEventListener("submit", async event => {
  event.preventDefault(); const result = document.querySelector("#harvestResult");
  try {
    const items = JSON.parse(document.querySelector("#catalogItems").value);
    const payload = await api("/api/catalog/harvest", { method: "POST", body: JSON.stringify({ company: document.querySelector("#company").value, shelf_id: document.querySelector("#shelf").value, items, persist: true }) });
    result.textContent = JSON.stringify(payload, null, 2);
  } catch (error) { result.textContent = error.message; }
});

document.querySelector("#candidatesFilterForm").addEventListener("submit", event => { event.preventDefault(); loadCandidates(); });

document.querySelectorAll(".nudgeBtn").forEach(btn => btn.addEventListener("click", () => generateNudges(btn.dataset.mode)));
document.querySelector("#fullNudgeFlow").addEventListener("click", () => { const study_id = document.querySelector("#nudgeInventory").value; if (study_id) openWorkflow("nudging", { study_id }); });
document.querySelector("#nudgeGraph").addEventListener("click", () => { const studyId = document.querySelector("#nudgeInventory").value; if (studyId) openCompanyHeritage(studyId); });
document.querySelector("#ucGraphBtn").addEventListener("click", () => { const studyId = document.querySelector("#nudgeInventory").value; if (studyId) openUseCaseGraph("company", { study_id: studyId }); });
document.querySelector("#nudgeSkillCall").addEventListener("click", () => { const studyId = document.querySelector("#nudgeInventory").value; if (studyId) openInvoke("use-case-nudging", `Génère et challenge les nudges du study ${studyId} depuis l'inventaire UC uniquement; ne charge ni ICB ni product fit.`); });

document.querySelector("#catalogSearchBtn").addEventListener("click", runCatalogSearch);
document.querySelector("#catalogSearchQuery").addEventListener("keydown", event => { if (event.key === "Enter") { event.preventDefault(); runCatalogSearch(); } });

document.querySelector("#peopleSearchForm").addEventListener("submit", event => { event.preventDefault(); runPeopleSearch(); });
document.querySelector("#companiesSearchForm").addEventListener("submit", event => { event.preventDefault(); runCompaniesSearch(); });
document.querySelector("#companiesSearchTab").addEventListener("click", () => document.querySelector("#companiesText").focus());

document.querySelector("#createPersonForm").addEventListener("submit", async event => {
  event.preventDefault();
  const out = document.querySelector("#createPersonResult");
  out.textContent = "Création…";
  try {
    const person = await api("/api/network/people", { method: "POST", body: JSON.stringify({
      display_name: document.querySelector("#newPersonName").value.trim(),
      seed_company_id: document.querySelector("#newPersonCompany").value.trim(),
      source: "manual_entry",
    }) });
    out.innerHTML = `<div class="confirmation-banner">Contact créé — ${esc(person.display_name)} (${esc(person.person_id || "")})</div>`;
    document.querySelector("#createPersonForm").reset();
  } catch (error) { out.textContent = error.message; }
});

document.querySelector("#createCompanyForm").addEventListener("submit", async event => {
  event.preventDefault();
  const out = document.querySelector("#createCompanyResult");
  out.textContent = "Création…";
  try {
    const company = await api("/api/network/companies", { method: "POST", body: JSON.stringify({
      canonical_name: document.querySelector("#newCompanyName").value.trim(),
      sector_code: document.querySelector("#newCompanySector").value.trim() || undefined,
    }) });
    out.innerHTML = `<div class="confirmation-banner">Entreprise créée — ${esc(company.canonical_name)} (${esc(company.company_id || "")})</div>`;
    document.querySelector("#createCompanyForm").reset();
  } catch (error) { out.textContent = error.message; }
});

document.querySelector("#demandIntakeForm").addEventListener("submit", async event => {
  event.preventDefault();
  const out = document.querySelector("#demandIntakeResult");
  out.textContent = "Création…";
  try {
    const result = await api("/api/demand/intake", { method: "POST", body: JSON.stringify({
      company: document.querySelector("#demandIntakeCompany").value.trim(),
      problem_statement: document.querySelector("#demandIntakeProblem").value.trim(),
      sector_code: document.querySelector("#demandIntakeSector").value.trim() || undefined,
      company_id: document.querySelector("#demandIntakeCompanyId").value.trim() || undefined,
      study_id: document.querySelector("#demandIntakeStudyId").value.trim() || undefined,
      confidence: document.querySelector("#demandIntakeConfidence").value,
    }) });
    out.innerHTML = `<div class="confirmation-banner">Profil de demande créé — ${esc(result.study_id)} (${esc(result.profile_path)})</div>`;
    document.querySelector("#demandIntakeForm").reset();
    renderDemand();
  } catch (error) { out.textContent = error.message; }
});

document.querySelector("#loadDuplicatesBtn").addEventListener("click", loadDuplicates);

async function loadBlockerActions() {
  const params = new URLSearchParams();
  const studyId = document.querySelector("#blockerActionsStudyId").value.trim();
  const companyId = document.querySelector("#blockerActionsCompanyId").value.trim();
  const stepId = document.querySelector("#blockerActionsStepId").value;
  const action = document.querySelector("#blockerActionsAction").value;
  const since = document.querySelector("#blockerActionsSince").value;
  const until = document.querySelector("#blockerActionsUntil").value;
  if (studyId) params.set("study_id", studyId);
  if (companyId) params.set("company_id", companyId);
  if (stepId) params.set("step_id", stepId);
  if (action) params.set("action", action);
  if (since) params.set("since", since);
  if (until) params.set("until", until);
  const tbody = document.querySelector("#blockerActionsRows");
  tbody.innerHTML = `<tr><td colspan="6">Chargement…</td></tr>`;
  try {
    const rows = await api(`/api/blocker-actions?${params.toString()}`);
    tbody.innerHTML = rows.map(r => `<tr><td>${esc(r.timestamp || "")}</td><td>${esc(r.study_id || "")}</td><td>${esc(r.step_id || "")}</td><td><span class="badge">${esc(r.action || "")}</span></td><td>${esc(r.actor || "")}</td><td>${esc(r.reason || "")}</td></tr>`).join("") || `<tr><td colspan="6">Aucune action trouvée.</td></tr>`;
  } catch (error) {
    tbody.innerHTML = `<tr><td colspan="6" class="error">${esc(error.message)}</td></tr>`;
  }
}

document.querySelector("#blockerActionsFilterForm").addEventListener("submit", event => { event.preventDefault(); loadBlockerActions(); });

document.querySelector("#prospectingForm").addEventListener("submit", event => { event.preventDefault(); launchProspectingCampaign(); });

boot();
