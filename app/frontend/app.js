const state = {
  skills: [], offers: [], shelves: [], demand: { sectors: [] }, inventories: [],
  qualification: [], nudgeInventories: [], selectedSkill: null, selectedSector: null
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

async function openWorkflow(kind, target) {
  const payload = { kind, ...target };
  const panel = document.querySelector("#workflowPanel");
  document.querySelector("#workflowSteps").innerHTML = "Chargement…";
  panel.classList.remove("hidden");
  try {
    const plan = await api("/api/workflows/plan", { method: "POST", body: JSON.stringify(payload) });
    document.querySelector("#workflowTitle").textContent = `${plan.label || plan.target} · ${kind}`;
    const current = plan.current ? `État : ${plan.current.eligible_studies ?? "—"} études éligibles · ${plan.current.use_cases ?? "—"} use cases · ${plan.current.benchmark_state ?? ""}` : (plan.stage ? `Étape actuelle : ${plan.stage}` : "Parcours guidé avec gates explicites.");
    document.querySelector("#workflowSummary").textContent = current;
    document.querySelector("#workflowSteps").innerHTML = (plan.steps || []).map((step, index) => `
      <div class="workflow-step ${statusClass(step.status)}">
        <div class="step-index">${String(index + 1).padStart(2, "0")}</div>
        <div class="step-body">
          <div class="step-title"><strong>${esc(step.id)}</strong><span class="badge">${esc(step.status)}</span></div>
          <div class="hint">${esc(step.gate || step.skill || "Revue humaine")}</div>
        </div>
        ${step.skill ? `<button class="workflowSkillBtn" data-skill="${esc(step.skill)}" data-target="${esc(plan.target)}" ${step.status === "blocked" ? "disabled" : ""}>Préparer</button>` : ""}
      </div>`).join("");
    document.querySelectorAll(".workflowSkillBtn").forEach(btn => btn.addEventListener("click", () => {
      openInvoke(btn.dataset.skill, `Poursuis le parcours ${kind} pour ${btn.dataset.target}. Respecte les gates du workflow et produis uniquement l'artefact de cette skill.`);
    }));
  } catch (error) {
    document.querySelector("#workflowSteps").innerHTML = `<div class="error">${esc(error.message)}</div>`;
  }
}

function renderSkills(filter = "") {
  const needle = filter.trim().toLowerCase();
  const grid = document.querySelector("#skillGrid");
  grid.innerHTML = state.skills
    .filter(s => !needle || `${s.id} ${s.description}`.toLowerCase().includes(needle))
    .map(s => `<article class="card">
      <h3>${esc(s.id)}</h3>
      <p>${esc(s.description || "Skill sans description.")}</p>
      <div class="meta"><span class="badge">sha ${esc(s.sha256.slice(0, 10))}</span></div>
      <button data-skill="${esc(s.id)}" class="invokeBtn">Appel unitaire</button>
    </article>`).join("");
  document.querySelectorAll(".invokeBtn").forEach(button => button.addEventListener("click", () => openInvoke(button.dataset.skill)));
}

function renderShelves() {
  const offersById = Object.fromEntries(state.offers.map(o => [o.offer_id, o]));
  document.querySelector("#shelfGrid").innerHTML = state.shelves.map(shelf => {
    const cards = (shelf.offer_ids || []).map(id => offersById[id]).filter(Boolean);
    return `<article class="card shelf-card">
      <p class="eyebrow">${esc(shelf.shelf_id)}</p>
      <h3>${esc(shelf.name)}</h3>
      <p>${esc(shelf.purpose || "")}</p>
      <div>${cards.map(o => `<div class="offer-row">
        <div><strong>${esc(o.name)}</strong><div class="meta"><span class="badge">${esc(o.offer_id)}</span><span class="badge">${esc(o.status)}</span><span>${esc(o.profile_version || "")}</span></div></div>
        <button class="offerAuditBtn" data-offer="${esc(o.offer_id)}" data-file="${esc(o.file || "")}">Auditer / MAJ</button>
      </div>`).join("") || "<small>Aucune offre canonique.</small>"}</div>
    </article>`;
  }).join("");
  document.querySelectorAll(".offerAuditBtn").forEach(btn => btn.addEventListener("click", () => openInvoke(
    "product-icp-intelligence",
    `Audite ou mets à jour la vérité canonique de ${btn.dataset.offer} sans charger de compte nommé.`,
    btn.dataset.file ? [`product_catalog/${btn.dataset.file}`] : []
  )));
  const options = state.shelves.map(s => `<option value="${esc(s.shelf_id)}">${esc(s.name)}</option>`).join("");
  document.querySelector("#shelf").innerHTML = options;
  document.querySelector("#discoverShelf").innerHTML = options;
}

function sectorActionLabel(sector) {
  return ({
    add_contact: "Ajouter un contact",
    add_company: "Ajouter une entreprise",
    add_third_company: "Ajouter une 3e entreprise",
    launch_benchmark: "Lancer le benchmark",
    refresh_benchmark: "Rafraîchir le benchmark"
  })[sector.primary_action] || "Continuer";
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
  document.querySelector("#sectorGrid").innerHTML = sectors.map(sector => `
    <article class="card sector-card ${statusClass(sector.benchmark_state)}">
      <div class="sector-top">
        <div><p class="eyebrow">${esc(sector.industry_name)} · ${esc(sector.sector_code)}</p><h3>${esc(sector.sector_name)}</h3></div>
        <span class="badge ${statusClass(sector.benchmark_state)}">${esc(sectorStateLabel(sector))}</span>
      </div>
      <div class="metrics">
        <div><strong>${sector.eligible_study_count}</strong><span>/ 3 études</span></div>
        <div><strong>${sector.mapped_company_count}</strong><span>entreprises</span></div>
        <div><strong>${sector.use_case_count}</strong><span>use cases</span></div>
      </div>
      <div class="card-actions">
        <button class="sectorDetailBtn" data-sector="${esc(sector.sector_code)}">Ouvrir</button>
        <button class="sectorPrimaryBtn ${sector.benchmark_state === "benchmark_edge" || sector.benchmark_enabled ? "primary" : ""}" data-sector="${esc(sector.sector_code)}">${esc(sectorActionLabel(sector))}</button>
        <button class="sectorFlowBtn" data-sector="${esc(sector.sector_code)}">Parcours complet</button>
      </div>
    </article>`).join("");
  document.querySelectorAll(".sectorDetailBtn").forEach(btn => btn.addEventListener("click", () => openSectorDetail(btn.dataset.sector)));
  document.querySelectorAll(".sectorPrimaryBtn").forEach(btn => btn.addEventListener("click", () => runSectorPrimary(btn.dataset.sector)));
  document.querySelectorAll(".sectorFlowBtn").forEach(btn => btn.addEventListener("click", () => openWorkflow("demand", { sector_code: btn.dataset.sector })));
}

function runSectorPrimary(code) {
  const sector = (state.demand.sectors || []).find(s => s.sector_code === code);
  if (!sector) return;
  if (sector.primary_action === "launch_benchmark" || sector.primary_action === "refresh_benchmark") {
    openInvoke(
      "sector-intelligence-consolidation",
      `Consolide le benchmark du secteur ICB ${sector.sector_code} — ${sector.sector_name}. Respecte le seuil de 3 études, le statut ICB et préserve les use-case IDs par entreprise.`,
      sector.rollup_path ? [sector.rollup_path] : []
    );
  } else if (sector.primary_action === "add_third_company") {
    openInvoke("network-contact-intake", `Ajoute une nouvelle source de contact/entreprise afin de compléter le secteur ICB ${sector.sector_code}. Ne présume pas de la classification : elle devra être validée par enterprise-icb-mapping.`);
  } else {
    openInvoke("network-contact-intake", `Ajoute un contact ou une entreprise candidate pour développer la couverture du secteur ICB ${sector.sector_code}. La classification et la demande restent à établir.`);
  }
}

function openSectorDetail(code) {
  state.selectedSector = code;
  const sector = (state.demand.sectors || []).find(s => s.sector_code === code);
  if (!sector) return;
  const inventoryByStudy = Object.fromEntries(state.inventories.map(i => [i.study_id, i]));
  const companyRows = (sector.companies || []).map(company => {
    const inventory = company.study_id ? inventoryByStudy[company.study_id] : null;
    return `<div class="company-row">
      <div>
        <strong>${esc(company.company)}</strong>
        <div class="meta"><span class="badge">ICB ${esc(company.mapping_status)}</span><span class="badge">${company.eligible ? "étude éligible" : "étude à compléter"}</span><span>${company.use_case_count} use cases</span></div>
      </div>
      <div class="row-actions">
        ${company.study_path ? `<button class="useFlowBtn" data-study="${esc(company.study_id)}" data-path="${esc(company.study_path)}">Ajouter / MAJ use flow</button>` : ""}
        ${company.study_id ? `<button class="companyQualBtn" data-study="${esc(company.study_id)}">Qualification</button>` : ""}
      </div>
      ${inventory && inventory.use_cases.length ? `<div class="use-case-list">${inventory.use_cases.map(uc => `<span class="badge">${esc(uc.use_case_id)} · ${esc(uc.name || uc.workflow || "use case")}</span>`).join("")}</div>` : ""}
    </div>`;
  }).join("") || `<div class="empty-state">Aucune entreprise mappée dans le runtime privé.</div>`;
  const detail = document.querySelector("#sectorDetail");
  detail.innerHTML = `
    <div class="section-head"><div><p class="eyebrow">Deep dive ICB ${esc(code)}</p><h3>${esc(sector.sector_name)}</h3><p>${sector.eligible_study_count}/3 études éligibles · ${sector.use_case_count} use cases recensés.</p></div><button id="closeSectorDetail" class="ghost">Fermer</button></div>
    <div class="action-row">
      <button id="detailPrimary" class="primary">${esc(sectorActionLabel(sector))}</button>
      <button id="detailBenchmark" ${sector.benchmark_enabled ? "" : "disabled"}>Lancer benchmarking</button>
      <button id="detailHarvest">Récolter / consolider use cases</button>
      <button id="detailFlow">Parcours complet</button>
    </div>
    <div class="company-list">${companyRows}</div>`;
  detail.classList.remove("hidden");
  document.querySelector("#closeSectorDetail").addEventListener("click", () => detail.classList.add("hidden"));
  document.querySelector("#detailPrimary").addEventListener("click", () => runSectorPrimary(code));
  document.querySelector("#detailBenchmark").addEventListener("click", () => runSectorPrimary(code));
  document.querySelector("#detailFlow").addEventListener("click", () => openWorkflow("demand", { sector_code: code }));
  document.querySelector("#detailHarvest").addEventListener("click", () => {
    const firstStudy = (sector.companies || []).find(c => c.study_path);
    if (firstStudy) openInvoke("enterprise-use-case-intelligence", `Récolte ou consolide les use cases sous-jacents de ${firstStudy.company}. Préserve les preuves, dépendances, maturité et feedback.`, [firstStudy.study_path]);
    else openInvoke("enterprise-use-case-intelligence", `Prépare la récolte des use cases pour le secteur ${code} après création d'une étude entreprise. Ne déduis aucun use case du secteur seul.`);
  });
  document.querySelectorAll(".useFlowBtn").forEach(btn => btn.addEventListener("click", () => openInvoke(
    "enterprise-use-case-intelligence",
    `Ajoute ou mets à jour les use flows/use cases du study ${btn.dataset.study}. Ne charge aucune offre.`,
    [btn.dataset.path]
  )));
  document.querySelectorAll(".companyQualBtn").forEach(btn => btn.addEventListener("click", () => {
    showPanel("qualification");
    const card = document.querySelector(`[data-qualification-study="${CSS.escape(btn.dataset.study)}"]`);
    if (card) card.scrollIntoView({ behavior: "smooth", block: "center" });
  }));
}

function renderQualification() {
  const grid = document.querySelector("#qualificationGrid");
  if (!state.qualification.length) {
    grid.innerHTML = `<div class="empty-state">Aucune étude locale disponible. Commence par le menu Demande.</div>`;
    return;
  }
  grid.innerHTML = state.qualification.map(row => `
    <article class="card qualification-card" data-qualification-study="${esc(row.study_id)}">
      <div class="sector-top"><div><p class="eyebrow">${esc(row.study_id)}</p><h3>${esc(row.company)}</h3></div><span class="badge ${statusClass(row.stage)}">${esc(row.stage)}</span></div>
      <div class="stepper">${(row.steps || []).map(step => `<div class="mini-step ${statusClass(step.status)}"><span></span><small>${esc(step.id)}</small></div>`).join("")}</div>
      <p class="hint">${esc(row.blocked_reason || `Prochaine action : ${row.next_action}`)}</p>
      <div class="card-actions">
        ${row.next_skill ? `<button class="primary qualNextBtn" data-skill="${esc(row.next_skill)}" data-study="${esc(row.study_id)}" data-path="${esc(row.study_path)}">${esc(row.next_action)}</button>` : `<button disabled>${esc(row.next_action)}</button>`}
        <button class="qualFlowBtn" data-study="${esc(row.study_id)}">Parcours complet</button>
      </div>
    </article>`).join("");
  document.querySelectorAll(".qualNextBtn").forEach(btn => btn.addEventListener("click", () => openInvoke(
    btn.dataset.skill,
    `Exécute uniquement l'étape suivante du parcours de qualification pour ${btn.dataset.study}. Respecte tous les artefacts et hard gates existants.`,
    [btn.dataset.path]
  )));
  document.querySelectorAll(".qualFlowBtn").forEach(btn => btn.addEventListener("click", () => openWorkflow("qualification", { study_id: btn.dataset.study })));
}

function renderNudgeInventories() {
  const select = document.querySelector("#nudgeInventory");
  if (!state.nudgeInventories.length) {
    select.innerHTML = `<option value="">Aucun inventaire de use cases</option>`;
    select.disabled = true;
    document.querySelectorAll(".nudgeBtn").forEach(btn => btn.disabled = true);
    document.querySelector("#nudgeSkillCall").disabled = true;
    document.querySelector("#fullNudgeFlow").disabled = true;
    return;
  }
  select.disabled = false;
  select.innerHTML = state.nudgeInventories.map(i => `<option value="${esc(i.study_id)}" data-path="${esc(i.path)}">${esc(i.company)} · ${i.use_case_count} use cases</option>`).join("");
  document.querySelectorAll(".nudgeBtn").forEach(btn => btn.disabled = false);
  document.querySelector("#nudgeSkillCall").disabled = false;
  document.querySelector("#fullNudgeFlow").disabled = false;
}

async function generateNudges(mode) {
  const studyId = document.querySelector("#nudgeInventory").value;
  if (!studyId) return;
  const grid = document.querySelector("#nudgeResults");
  grid.innerHTML = `<div class="empty-state">Génération…</div>`;
  try {
    const result = await api("/api/nudging/generate", { method: "POST", body: JSON.stringify({ study_id: studyId, mode }) });
    const nudges = result.nudges || [];
    grid.innerHTML = nudges.length ? nudges.map(nudge => `<article class="card nudge-result">
      <div class="sector-top"><p class="eyebrow">${esc(nudge.mode)}</p><span class="badge">${esc(nudge.confidence)}</span></div>
      <h3>${esc((nudge.source_use_case_ids || []).join(" + "))}${nudge.target_use_case_ids?.length ? ` → ${esc(nudge.target_use_case_ids.join(" + "))}` : ""}</h3>
      <p>${esc(nudge.rationale)}</p>
      <div class="callout"><strong>Préconditions</strong><br>${esc((nudge.prerequisites || []).join(" · ") || "—")}</div>
      <div class="callout"><strong>Falsifier</strong><br>${esc(nudge.falsifier)}</div>
      ${nudge.evidence_feedback?.length ? `<div class="hint">Feedback : ${esc(nudge.evidence_feedback.map(f => f.statement).join(" · "))}</div>` : ""}
      ${nudge.unknowns?.length ? `<div class="hint">Inconnues : ${esc(nudge.unknowns.join(" · "))}</div>` : ""}
    </article>`).join("") : `<div class="empty-state">Aucune piste conforme aux règles de ce mode. C’est un résultat valide : le moteur n’invente pas d’adjacence.</div>`;
  } catch (error) {
    grid.innerHTML = `<div class="error">${esc(error.message)}</div>`;
  }
}

function renderBacklog(items) {
  document.querySelector("#backlogRows").innerHTML = items
    .filter(item => item.status !== "completed")
    .sort((a,b) => String(a.priority).localeCompare(String(b.priority)))
    .map(item => `<tr><td>${esc(item.id)}</td><td>${esc(item.priority)}</td><td><span class="badge ${statusClass(item.status)}">${esc(item.status)}</span></td><td>${esc(item.area)}</td><td>${esc(item.task)}</td></tr>`).join("");
}

async function boot() {
  try {
    const [health, skills, offers, shelves, backlog, demand, inventories, qualification, nudgeInventories] = await Promise.all([
      api("/api/health"), api("/api/skills"), api("/api/offers"), api("/api/shelves"), api("/api/backlog"),
      api("/api/demand"), api("/api/demand/inventories"), api("/api/qualification"), api("/api/nudging/inventories")
    ]);
    document.querySelector("#health").textContent = health.executor_configured ? "Executor connecté" : "Mode local · executor à configurer";
    state.skills = skills; state.offers = offers; state.shelves = shelves; state.demand = demand;
    state.inventories = inventories; state.qualification = qualification; state.nudgeInventories = nudgeInventories;
    renderDemand(); renderShelves(); renderQualification(); renderNudgeInventories(); renderSkills(); renderBacklog(backlog);
  } catch (error) {
    document.querySelector("#health").textContent = "Erreur de chargement";
    console.error(error);
  }
}

document.querySelectorAll("nav button").forEach(button => button.addEventListener("click", () => showPanel(button.dataset.target)));
document.querySelector("#sectorFilter").addEventListener("input", event => renderDemand(event.target.value));
document.querySelector("#skillFilter").addEventListener("input", event => renderSkills(event.target.value));
document.querySelector("#globalAddContact").addEventListener("click", () => openInvoke("network-contact-intake", "Ajoute un contact ou un lot de contacts, préserve la provenance et ne déduis ni ICB, ni demande, ni autorité."));
document.querySelector("#closeInvoke").addEventListener("click", () => document.querySelector("#invokePanel").classList.add("hidden"));
document.querySelector("#closeWorkflow").addEventListener("click", () => document.querySelector("#workflowPanel").classList.add("hidden"));
document.querySelector("#runSkill").addEventListener("click", async () => {
  const result = document.querySelector("#invokeResult");
  result.textContent = "Exécution…";
  try {
    const context_paths = document.querySelector("#contextPaths").value.split("\n").map(x => x.trim()).filter(Boolean);
    const payload = await api(`/api/skills/${encodeURIComponent(state.selectedSkill)}/invoke`, {
      method: "POST",
      body: JSON.stringify({ input: document.querySelector("#invokeInput").value, context_paths })
    });
    result.textContent = JSON.stringify(payload, null, 2);
  } catch (error) { result.textContent = error.message; }
});

document.querySelectorAll(".nudgeBtn").forEach(btn => btn.addEventListener("click", () => generateNudges(btn.dataset.mode)));
document.querySelector("#fullNudgeFlow").addEventListener("click", () => {
  const studyId = document.querySelector("#nudgeInventory").value;
  if (studyId) openWorkflow("nudging", { study_id: studyId });
});
document.querySelector("#nudgeSkillCall").addEventListener("click", () => {
  const select = document.querySelector("#nudgeInventory");
  const studyId = select.value;
  const path = select.options[select.selectedIndex]?.dataset.path;
  if (studyId) openInvoke("use-case-nudging", `Génère les trois familles de nudges pour ${studyId} en utilisant uniquement l'inventaire de use cases et le feedback embarqué.`, path ? [path] : []);
});

document.querySelector("#discoverForm").addEventListener("submit", async event => {
  event.preventDefault();
  const result = document.querySelector("#discoverResult");
  result.textContent = "Découverte…";
  try {
    const payload = await api("/api/catalog/discover", { method: "POST", body: JSON.stringify({ company: document.querySelector("#discoverCompany").value, shelf_id: document.querySelector("#discoverShelf").value, domain: document.querySelector("#discoverDomain").value, source: "web", persist: true }) });
    result.textContent = JSON.stringify(payload, null, 2);
  } catch (error) { result.textContent = error.message; }
});

document.querySelector("#harvestForm").addEventListener("submit", async event => {
  event.preventDefault();
  const result = document.querySelector("#harvestResult");
  try {
    const items = JSON.parse(document.querySelector("#catalogItems").value);
    const payload = await api("/api/catalog/harvest", { method: "POST", body: JSON.stringify({ company: document.querySelector("#company").value, shelf_id: document.querySelector("#shelf").value, items, persist: true }) });
    result.textContent = JSON.stringify(payload, null, 2);
  } catch (error) { result.textContent = error.message; }
});

boot();
