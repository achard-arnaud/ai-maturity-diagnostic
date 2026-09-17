/* GTM V1 prototype — shared shell injector. No build step, no framework,
   consistent with the isolation rule (this is UX exploration, not
   production code, and must not depend on app/**). See SHELL_CONTRACT.md §1.
*/
(function () {
  "use strict";

  var NAV_ITEMS = [
    { id: "home", label: "Home", href: "../home/index.html" },
    { id: "discover", label: "Discover", href: "../discover/index.html" },
    { id: "research", label: "Research", href: "../research/index.html" },
    { id: "fit", label: "Fit", href: "../fit/index.html" },
    { id: "targets", label: "Targets", href: "../targets/index.html" },
    { id: "reach", label: "Reach", href: "../reach/index.html" },
    { id: "engagement", label: "Engagement", href: "../engagement/index.html" },
    { id: "pipeline", label: "Pipeline", href: "../pipeline/index.html" },
    { id: "insights", label: "Insights", href: "../insights/index.html" },
  ];
  var SECONDARY_NAV_ITEMS = [{ id: "admin", label: "Admin & Automation", href: "../admin/index.html" }];

  function escapeHtml(value) {
    return String(value == null ? "" : value).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function navItemHtml(item, activeNav) {
    var current = item.id === activeNav ? ' aria-current="page"' : "";
    return (
      '<li><a href="' +
      escapeHtml(item.href) +
      '"' +
      current +
      "><span aria-hidden=\"true\">" +
      navIcon(item.id) +
      '</span> <span class="gtm-nav-label">' +
      escapeHtml(item.label) +
      "</span></a></li>"
    );
  }

  function navIcon(id) {
    // Text glyphs, not an icon font dependency — keeps this isolated and
    // dependency-free. Purely decorative (aria-hidden); the label carries
    // the meaning, per "do not rely on a single non-text signal" spirit.
    var glyphs = {
      home: "⌂",
      discover: "◉",
      research: "⌕",
      fit: "✓",
      targets: "◎",
      reach: "✉",
      engagement: "⛁",
      pipeline: "☷",
      insights: "☷",
      admin: "⚙",
    };
    return glyphs[id] || "•";
  }

  function render(activeNav, options) {
    options = options || {};
    var workspace = options.workspace || "Acme Workspace";
    var user = options.user || "Alex Reviewer";
    var hasRail = !!options.rail;
    var mount = document.getElementById("gtmShell");
    if (!mount) {
      throw new Error("GtmProtoShell.render: no #gtmShell element found on this page");
    }
    mount.classList.add("gtm-shell");
    if (hasRail) mount.classList.add("has-rail");

    // If the page authored its main content as literal, inspectable HTML
    // inside <template id="gtmMainContent"> (recommended for any page a
    // checker or reviewer needs to grep, e.g. states.html's data-state
    // panels), move it into the #gtmMain slot below instead of leaving it
    // JS-generated. See SHELL_CONTRACT.md §1.
    var staticContent = document.getElementById("gtmMainContent");
    var staticHtml = staticContent ? staticContent.innerHTML : "";
    if (staticContent) staticContent.remove();

    mount.innerHTML =
      '<header class="gtm-header">' +
      '<span class="gtm-header__workspace">' +
      escapeHtml(workspace) +
      "</span>" +
      '<input class="gtm-header__search" type="search" placeholder="Rechercher comptes, personnes, signaux…" aria-label="Recherche globale" disabled>' +
      '<span class="gtm-header__spacer"></span>' +
      '<button class="gtm-header__create" type="button">+ Créer</button>' +
      '<button class="gtm-header__icon-btn" type="button" aria-label="Notifications">\u{1F514}</button>' +
      '<span class="gtm-header__user"><span aria-hidden="true">\u{1F464}</span>' +
      escapeHtml(user) +
      "</span>" +
      "</header>" +
      '<nav class="gtm-sidebar" aria-label="Navigation principale">' +
      '<ul class="gtm-sidebar__nav">' +
      NAV_ITEMS.map(function (item) {
        return navItemHtml(item, activeNav);
      }).join("") +
      "</ul>" +
      '<hr class="gtm-sidebar__separator">' +
      '<ul class="gtm-sidebar__nav gtm-sidebar__secondary">' +
      SECONDARY_NAV_ITEMS.map(function (item) {
        return navItemHtml(item, activeNav);
      }).join("") +
      "</ul>" +
      "</nav>" +
      '<main class="gtm-main" id="gtmMain">' + staticHtml + "</main>" +
      (hasRail ? '<aside class="gtm-rail" id="gtmRail" aria-label="Contexte"></aside>' : "");
  }

  /** Renders a state banner into a target element. See SHELL_CONTRACT.md §3. */
  var STATE_COPY = {
    loading: { icon: "⏳", text: "Chargement…" },
    empty: { icon: "•", text: "Aucun élément pour ce filtre." },
    error: { icon: "⚠", text: "Une erreur est survenue. Réessayer." },
    blocked: { icon: "⛔", text: "Bloqué — une action est requise avant de continuer." },
    stale: { icon: "↻", text: "Ces données sont périmées et doivent être revérifiées." },
    "partial-data": { icon: "◐", text: "Données partielles — certaines sources n'ont pas répondu." },
  };

  function stateBanner(state, detail) {
    if (state === "default" || state === "success") return "";
    var copy = STATE_COPY[state] || { icon: "•", text: state };
    return (
      '<div class="state-banner state-banner--' +
      escapeHtml(state) +
      '" role="status">' +
      '<span aria-hidden="true">' +
      copy.icon +
      "</span> " +
      escapeHtml(detail || copy.text) +
      (state === "blocked" ? ' <button type="button" class="state-banner__resolve">Résoudre</button>' : "") +
      "</div>"
    );
  }

  window.GtmProtoShell = { render: render, stateBanner: stateBanner, NAV_ITEMS: NAV_ITEMS };
})();
