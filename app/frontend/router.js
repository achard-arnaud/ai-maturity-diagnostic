(function () {
  "use strict";
  const spaces = new Set(["home", "discover", "research", "fit", "targets", "reach", "engagement", "pipeline", "insights"]);
  let workspaceId = null;
  let onNavigate = null;
  function parse(pathname = window.location.pathname) {
    const match = pathname.match(/^\/w\/([^/]+)\/([^/]+)(?:\/([^/]+))?\/?$/);
    if (!match || !spaces.has(match[2])) return null;
    return { workspace: decodeURIComponent(match[1]), space: match[2], objectId: match[3] ? decodeURIComponent(match[3]) : null };
  }
  function path(space, objectId = null) {
    if (!workspaceId || !spaces.has(space)) throw new Error("workspace and valid GTM space are required");
    return `/w/${encodeURIComponent(workspaceId)}/${space}${objectId ? `/${encodeURIComponent(objectId)}` : ""}`;
  }
  function navigate(space, objectId = null, replace = false) {
    window.history[replace ? "replaceState" : "pushState"]({}, "", path(space, objectId));
    if (onNavigate) onNavigate({ workspace: workspaceId, space, objectId });
  }
  function start(authoritativeWorkspaceId, callback) {
    workspaceId = authoritativeWorkspaceId;
    onNavigate = callback;
    const current = parse();
    if (!current || current.workspace !== workspaceId) navigate("home", null, true); else callback(current);
    window.addEventListener("popstate", () => {
      const route = parse();
      if (!route || route.workspace !== workspaceId) navigate("home", null, true); else callback(route);
    });
  }
  window.GtmRouter = { navigate, parse, start, spaces };
})();
