const state = {
  skills: [], offers: [], shelves: [], demand: { sectors: [] }, inventories: [],
  qualification: [], nudgeInventories: [], backlog: [], followUp: [], valueChain: [],
  selectedSkill: null, selectedSector: null, resolvers: {}
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

function openInvoke(skillId, input = "", contextPaths = []) {
  if (!skillId) return;
  state.selectedSkill = skillId;
  document.querySelector("#invokeTitle").textContent = skillId;
  document.querySelector("#invokeInput").value = input;
  document.querySelector("#contextPaths").value = (contextPaths || []).filter(Boolean).join("\n");
  document.querySelector("#invokeResult").textContent = "";
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
        </div>
      </div>`;
    }).join("");
    document.querySelectorAll(".workflowSkillBtn").forEach(btn => btn.addEventListener("click", () => openInvoke(
      btn.dataset.skill,
      `Poursuis le parcours ${kind} pour ${btn.dataset.target}. Respecte les gates et produis uniquement l'artefact de cette skill.`
    )));
    bindResolverButtons(document.querySelector("#workflowSteps"));
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
        <div class="row-actions"><button class="offerAuditBtn" data-offer="${esc(o.offer_id)}" data-file="${esc(o.file || "")}">Auditer / MAJ</button><button class="offerOppBtn" data-offer="${esc(o.offer_id)}">Opportunités</button><button class="offerFlowBtn" data-offer="${esc(o.offer_id)}">Parcours complet</button></div></div>`).join("") || "<small>Aucune offre canonique.</small>"}</div></article>`;
  }).join("");
  document.querySelectorAll(".offerAuditBtn").forEach(btn => btn.addEventListener("click", () => openInvoke("product-icp-intelligence", `Audite ou mets à jour la vérité canonique de ${btn.dataset.offer} sans charger de compte nommé.`, btn.dataset.file ? [`product_catalog/${btn.dataset.file}`] : [])));
  document.querySelectorAll(".offerFlowBtn").forEach(btn => btn.addEventListener("click", () => openWorkflow("offer", { offer_id: btn.dataset.offer })));
  document.querySelectorAll(".offerOppBtn").forEach(btn => btn.addEventListener("click", () => openOfferOpportunities(btn.dataset.offer)));
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
      <div class="card-actions"><button class="companyContextBtn" data-study="${esc(row.study_id)}">Entreprise</button><button class="orgBtn" data-study="${esc(row.study_id)}" data-path="${esc(row.study_path)}">Organisation</button>${row.decision === "pursue" || row.decision === "validate" ? `<button class="reachBtn" data-study="${esc(row.study_id)}">Reach</button>` : ""}<button class="qualFlowBtn" data-study="${esc(row.study_id)}">Parcours complet</button></div>
    </article>`;
  }).join("");
  bindResolverButtons(grid);
  grid.querySelectorAll(".companyContextBtn").forEach(btn => btn.addEventListener("click", () => openWorkflow("company", { study_id: btn.dataset.study })));
  grid.querySelectorAll(".orgBtn").forEach(btn => btn.addEventListener("click", () => openInvoke("tech-leadership-org-intelligence", `Rafraîchis l'organisation, le système de décision et les zones d'influence du study ${btn.dataset.study}.`, [btn.dataset.path])));
  grid.querySelectorAll(".reachBtn").forEach(btn => btn.addEventListener("click", () => openReach(btn.dataset.study)));
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

async function generateNudges(mode) {
  const studyId = document.querySelector("#nudgeInventory").value;
  if (!studyId) return;
  const results = document.querySelector("#nudgeResults");
  results.innerHTML = `<div class="empty-state">Calcul…</div>`;
  try {
    const payload = await api("/api/nudging/generate", { method: "POST", body: JSON.stringify({ study_id: studyId, mode }) });
    results.innerHTML = (payload.nudges || []).map(n => `<article class="card"><p class="eyebrow">${esc(n.mode)}</p><h3>${esc((n.target_use_case_ids || []).join(" + "))}</h3><p>${esc(n.rationale)}</p><div class="meta"><span class="badge">${esc(n.status)}</span><span class="badge">${esc(n.confidence)}</span></div><small>Falsifier: ${esc(n.falsifier)}</small></article>`).join("") || `<div class="empty-state">Aucune piste admissible avec les preuves actuelles.</div>`;
  } catch (error) { results.innerHTML = `<div class="error">${esc(error.message)}</div>`; }
}

function renderFollowUp() {
  const grid = document.querySelector("#followUpGrid");
  const business = state.followUp.filter(item => item.kind !== "technical_todo");
  grid.innerHTML = business.length ? business.map(item => `<article class="card follow-card"><div class="sector-top"><div><p class="eyebrow">${esc(item.kind)} · ${esc(item.priority)}</p><h3>${esc(item.label)}</h3></div><span class="badge ${statusClass(item.state)}">${esc(item.state)}</span></div><p>${esc(item.message)}</p>${item.resolver ? resolverButton(item.resolver) : ""}<button class="followNavBtn" data-menu="${esc(item.navigation?.menu || "backlog")}" data-study="${esc(item.navigation?.study_id || "")}" data-sector="${esc(item.navigation?.sector_code || "")}">Ouvrir le contexte</button></article>`).join("") : `<div class="empty-state">Aucune action métier pending dans les données locales.</div>`;
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

async function boot() {
  try {
    const [health, skills, offers, shelves, demand, inventories, qualification, nudgeInventories, backlog, followUp, valueChain] = await Promise.all([
      api("/api/health"), api("/api/skills"), api("/api/offers"), api("/api/shelves"), api("/api/demand"), api("/api/demand/inventories"), api("/api/qualification"), api("/api/nudging/inventories"), api("/api/backlog"), api("/api/follow-up"), api("/api/value-chain")
    ]);
    document.querySelector("#health").textContent = health.executor_configured ? `v${health.version} · Executor connecté` : `v${health.version} · Executor à configurer`;
    Object.assign(state, { skills, offers, shelves, demand, inventories, qualification, nudgeInventories, backlog, followUp, valueChain });
    renderSkills(); renderShelves(); renderDemand(); renderQualification(); renderNudgeInventory(); renderFollowUp(); renderBacklog();
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
  try {
    const context_paths = document.querySelector("#contextPaths").value.split("\n").map(x => x.trim()).filter(Boolean);
    const payload = await api(`/api/skills/${encodeURIComponent(state.selectedSkill)}/invoke`, { method: "POST", body: JSON.stringify({ input: document.querySelector("#invokeInput").value, context_paths }) });
    result.textContent = JSON.stringify(payload, null, 2);
  } catch (error) { result.textContent = error.message; }
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

document.querySelectorAll(".nudgeBtn").forEach(btn => btn.addEventListener("click", () => generateNudges(btn.dataset.mode)));
document.querySelector("#fullNudgeFlow").addEventListener("click", () => { const study_id = document.querySelector("#nudgeInventory").value; if (study_id) openWorkflow("nudging", { study_id }); });
document.querySelector("#nudgeGraph").addEventListener("click", () => { const studyId = document.querySelector("#nudgeInventory").value; if (studyId) openCompanyHeritage(studyId); });
document.querySelector("#nudgeSkillCall").addEventListener("click", () => { const studyId = document.querySelector("#nudgeInventory").value; if (studyId) openInvoke("use-case-nudging", `Génère et challenge les nudges du study ${studyId} depuis l'inventaire UC uniquement; ne charge ni ICB ni product fit.`); });

boot();
