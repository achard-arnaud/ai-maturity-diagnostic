const state = { skills: [], offers: [], shelves: [], selectedSkill: null };

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

function openInvoke(skillId) {
  state.selectedSkill = skillId;
  document.querySelector("#invokeTitle").textContent = skillId;
  document.querySelector("#invokePanel").classList.remove("hidden");
  document.querySelector("#invokeResult").textContent = "";
  document.querySelector("#invokeInput").focus();
}

function renderShelves() {
  const offersById = Object.fromEntries(state.offers.map(o => [o.offer_id, o]));
  document.querySelector("#shelfGrid").innerHTML = state.shelves.map(shelf => {
    const cards = (shelf.offer_ids || []).map(id => offersById[id]).filter(Boolean);
    return `<article class="card">
      <p class="eyebrow">${esc(shelf.shelf_id)}</p>
      <h3>${esc(shelf.name)}</h3>
      <p>${esc(shelf.purpose || "")}</p>
      <div>${cards.map(o => `<div class="meta"><span class="badge">${esc(o.offer_id)}</span><span>${esc(o.name)}</span><span class="badge">${esc(o.status)}</span></div>`).join("") || "<small>Aucune offre canonique.</small>"}</div>
    </article>`;
  }).join("");
  document.querySelector("#shelf").innerHTML = state.shelves.map(s => `<option value="${esc(s.shelf_id)}">${esc(s.name)}</option>`).join("");
}

function renderBacklog(items) {
  document.querySelector("#backlogRows").innerHTML = items
    .filter(item => item.status !== "completed")
    .sort((a,b) => String(a.priority).localeCompare(String(b.priority)))
    .map(item => `<tr><td>${esc(item.id)}</td><td>${esc(item.priority)}</td><td>${esc(item.status)}</td><td>${esc(item.area)}</td><td>${esc(item.task)}</td></tr>`).join("");
}

async function boot() {
  try {
    const [health, skills, offers, shelves, backlog] = await Promise.all([
      api("/api/health"), api("/api/skills"), api("/api/offers"), api("/api/shelves"), api("/api/backlog")
    ]);
    document.querySelector("#health").textContent = health.executor_configured ? "Executor connecté" : "Executor à configurer";
    state.skills = skills; state.offers = offers; state.shelves = shelves;
    renderSkills(); renderShelves(); renderBacklog(backlog);
  } catch (error) {
    document.querySelector("#health").textContent = "Erreur de chargement";
    console.error(error);
  }
}

document.querySelectorAll("nav button").forEach(button => button.addEventListener("click", () => showPanel(button.dataset.target)));
document.querySelector("#skillFilter").addEventListener("input", event => renderSkills(event.target.value));
document.querySelector("#closeInvoke").addEventListener("click", () => document.querySelector("#invokePanel").classList.add("hidden"));
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
document.querySelector("#harvestForm").addEventListener("submit", async event => {
  event.preventDefault();
  const result = document.querySelector("#harvestResult");
  try {
    const items = JSON.parse(document.querySelector("#catalogItems").value);
    const payload = await api("/api/catalog/harvest", {
      method: "POST",
      body: JSON.stringify({
        company: document.querySelector("#company").value,
        shelf_id: document.querySelector("#shelf").value,
        items,
        persist: true
      })
    });
    result.textContent = JSON.stringify(payload, null, 2);
  } catch (error) { result.textContent = error.message; }
});

boot();
