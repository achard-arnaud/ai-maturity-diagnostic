# Vendored from `search-social-networks`

The files in this directory (`__init__.py`, `core.py`, `linkedin.py`,
`youtube.py`, `community.py`, `research.py`) are vendored, with no
functional changes, from `achard-arnaud/search-social-networks`
(MIT license, see `UPSTREAM_LICENSE` in this directory), per
`docs/ADR-011-evidence-acquisition-search.md`'s decision to vendor rather
than depend on that repository as a live cross-repo import or git
submodule (Program invariant #11: no new gateway/integration coupling
without demonstrated need).

Per-source reuse decisions (REUSE_AS_IS / ADAPT / WRAP) and the full
audit are recorded in
`docs/research/next-wave/HARVEST_SEARCH_SOCIAL_NETWORKS.md`. The
budget/correlation/run discipline these functions are wrapped in lives in
`app/harvest_runner.py`, not in this directory -- these files remain a
pure, unmodified acquisition layer (`f(query, days, limit, enrich,
allow_commercial=False) -> list[social_search.core.Result]` per source),
exactly as upstream ships them.

Do not hand-edit these files to add ai-maturity-diagnostic-specific
behavior; that belongs in `app/harvest_runner.py`. Re-vendor (replace
these files wholesale) instead, if a future revision of the upstream
functions is needed, so the diff against upstream stays reviewable.
