#!/usr/bin/env python3
"""Public-first advanced research acquisition for enterprise qualification.

This module is intentionally self-contained: it does not import or call the
francois-search-skills package or mvanhorn/last30days-skill. It implements a
small normalized evidence layer for the sources useful to this repository.

Policy:
- keyless/public acquisition where possible;
- optional first-party credentials only when already present in the environment;
- no billing flow or credential persistence;
- no authenticated LinkedIn scraping or browser automation;
- public-index LinkedIn results are discovery evidence, never proof of a live role.
"""
from __future__ import annotations

import argparse
import datetime as dt
from dataclasses import asdict, dataclass, field
from html.parser import HTMLParser
import html
import json
import os
import re
import shutil
import subprocess
import tempfile
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from typing import Any, Iterable

UA = "ai-maturity-diagnostic-advanced-research/0.1"


@dataclass
class EvidenceHit:
    source: str
    title: str
    url: str
    snippet: str = ""
    published_at: str | None = None
    author: str | None = None
    relevance: float = 0.5
    metadata: dict[str, Any] = field(default_factory=dict)

    def canonical_url(self) -> str:
        return re.sub(r"[#?].*$", "", self.url.rstrip("/")).lower()


def _window(days: int) -> tuple[str, str, int]:
    end = dt.datetime.now(dt.timezone.utc).date()
    start = end - dt.timedelta(days=max(1, days))
    epoch = int(dt.datetime.combine(start, dt.time.min, tzinfo=dt.timezone.utc).timestamp())
    return start.isoformat(), end.isoformat(), epoch


def _request(url: str, *, method: str = "GET", payload: dict[str, Any] | None = None,
             headers: dict[str, str] | None = None, timeout: int = 25) -> bytes:
    hdrs = {"User-Agent": UA, "Accept": "*/*"}
    if headers:
        hdrs.update(headers)
    body = None
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        hdrs.setdefault("Content-Type", "application/json")
    req = urllib.request.Request(url, data=body, headers=hdrs, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def _json(url: str, **kwargs: Any) -> dict[str, Any]:
    return json.loads(_request(url, **kwargs).decode("utf-8", errors="replace"))


def _dedupe(items: Iterable[EvidenceHit], limit: int) -> list[EvidenceHit]:
    out: list[EvidenceHit] = []
    seen: set[str] = set()
    for item in sorted(items, key=lambda x: x.relevance, reverse=True):
        key = item.canonical_url()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(item)
        if len(out) >= limit:
            break
    return out


class _DDG(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.rows: list[dict[str, str]] = []
        self._title = False
        self._snippet = False
        self._buf: list[str] = []
        self._current: dict[str, str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        data = dict(attrs)
        cls = data.get("class") or ""
        if tag == "a" and "result__a" in cls:
            self._title = True
            self._buf = []
            self._current = {"url": data.get("href") or "", "title": "", "snippet": ""}
        elif tag in {"a", "div"} and "result__snippet" in cls and self.rows:
            self._snippet = True
            self._buf = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._title:
            self._title = False
            if self._current is not None:
                self._current["title"] = " ".join(self._buf).strip()
                self.rows.append(self._current)
        elif tag in {"a", "div"} and self._snippet:
            self._snippet = False
            self.rows[-1]["snippet"] = " ".join(self._buf).strip()

    def handle_data(self, data: str) -> None:
        if self._title or self._snippet:
            self._buf.append(data)


def _unwrap_ddg(url: str) -> str:
    if url.startswith("//"):
        url = "https:" + url
    parsed = urllib.parse.urlparse(url)
    target = urllib.parse.parse_qs(parsed.query).get("uddg")
    return urllib.parse.unquote(target[0]) if target else url


def _web_index(query: str, limit: int, source: str = "web") -> list[EvidenceHit]:
    url = "https://html.duckduckgo.com/html/?" + urllib.parse.urlencode({"q": query})
    parser = _DDG()
    parser.feed(_request(url, headers={"Accept": "text/html"}).decode("utf-8", errors="replace"))
    out: list[EvidenceHit] = []
    for index, row in enumerate(parser.rows[: max(10, limit * 2)]):
        target = _unwrap_ddg(row.get("url", ""))
        if not target.startswith("http"):
            continue
        out.append(EvidenceHit(
            source=source,
            title=html.unescape(re.sub(r"\s+", " ", row.get("title", ""))).strip(),
            url=target,
            snippet=html.unescape(re.sub(r"\s+", " ", row.get("snippet", ""))).strip(),
            relevance=max(0.35, 0.82 - index * 0.03),
            metadata={"acquisition_method": "public_web_index"},
        ))
    return _dedupe(out, limit)


def search_web(query: str, days: int, limit: int, enrich: bool = False) -> list[EvidenceHit]:
    start, end, _ = _window(days)
    items = _web_index(f"{query} after:{start} before:{end}", limit, "web")
    for item in items:
        item.metadata.update({"window_start": start, "window_end": end})
    return items


def search_linkedin(query: str, days: int, limit: int, enrich: bool = False) -> list[EvidenceHit]:
    """Discover publicly indexed LinkedIn material without accessing LinkedIn pages.

    This is deliberately not the deferred LinkedIn connector described by the
    repository PRD. Results can seed manual validation but cannot set a role to
    current or resolve a canonical identity by themselves.
    """
    lanes = [
        (f"site:linkedin.com/pulse {query}", 0.95, "article"),
        (f"site:linkedin.com/posts {query}", 0.84, "post"),
        (f"site:linkedin.com/in {query}", 0.62, "profile_index_entry"),
    ]
    out: list[EvidenceHit] = []
    for lane, boost, kind in lanes:
        try:
            for hit in _web_index(lane, max(4, limit // 2), "linkedin"):
                hit.relevance = min(0.99, (hit.relevance + boost) / 2)
                hit.metadata.update({
                    "content_type": kind,
                    "acquisition_method": "public_web_index",
                    "connector_runtime": False,
                    "authenticated_linkedin_access": False,
                    "live_role_validation": False,
                    "canonical_identity_resolution": False,
                })
                out.append(hit)
        except Exception:
            continue
    return _dedupe(out, limit)


def search_reddit(query: str, days: int, limit: int, enrich: bool = False) -> list[EvidenceHit]:
    start, _, _ = _window(days)
    params = urllib.parse.urlencode({"q": query, "sort": "new", "t": "month"})
    out: list[EvidenceHit] = []
    try:
        root = ET.fromstring(_request("https://www.reddit.com/search.rss?" + params,
                                      headers={"Accept": "application/atom+xml"}))
        ns = {"a": "http://www.w3.org/2005/Atom"}
        for index, entry in enumerate(root.findall("a:entry", ns)):
            date = (entry.findtext("a:updated", default="", namespaces=ns) or "")[:10]
            if date and date < start:
                continue
            link = entry.find("a:link", ns)
            href = link.attrib.get("href", "") if link is not None else ""
            title = re.sub(r"\s+", " ", entry.findtext("a:title", default="", namespaces=ns)).strip()
            body = re.sub(r"<[^>]+>", " ", entry.findtext("a:content", default="", namespaces=ns) or "")
            body = html.unescape(re.sub(r"\s+", " ", body)).strip()
            out.append(EvidenceHit("reddit", title, href, body[:1200], date, None,
                                   max(0.45, 0.78 - index * 0.02),
                                   {"acquisition_method": "reddit_public_rss"}))
    except Exception:
        pass
    if not out:
        try:
            out = _web_index(f"site:reddit.com {query}", limit, "reddit")
            for hit in out:
                hit.metadata["acquisition_method"] = "public_web_index_fallback"
        except Exception:
            return []
    return _dedupe(out, limit)


def search_hackernews(query: str, days: int, limit: int, enrich: bool = False) -> list[EvidenceHit]:
    _, _, epoch = _window(days)
    params = urllib.parse.urlencode({
        "query": query,
        "tags": "story",
        "numericFilters": f"created_at_i>{epoch}",
        "hitsPerPage": min(50, max(10, limit * 2)),
    })
    data = _json("https://hn.algolia.com/api/v1/search_by_date?" + params)
    out: list[EvidenceHit] = []
    for row in data.get("hits", []):
        oid = row.get("objectID")
        url = row.get("url") or (f"https://news.ycombinator.com/item?id={oid}" if oid else "")
        if not url:
            continue
        points = int(row.get("points") or 0)
        comments = int(row.get("num_comments") or 0)
        out.append(EvidenceHit(
            "hackernews", row.get("title") or "Hacker News", url, "",
            (row.get("created_at") or "")[:10], row.get("author"),
            min(0.99, 0.50 + min(0.30, points / 1000) + min(0.15, comments / 1000)),
            {"points": points, "comments": comments,
             "discussion_url": f"https://news.ycombinator.com/item?id={oid}" if oid else None,
             "acquisition_method": "hn_algolia_public_api"},
        ))
    return _dedupe(out, limit)


def search_arxiv(query: str, days: int, limit: int, enrich: bool = False) -> list[EvidenceHit]:
    start, _, _ = _window(days)
    q = urllib.parse.quote(f"all:{query}")
    url = ("https://export.arxiv.org/api/query?search_query=" + q +
           f"&start=0&max_results={max(10, limit * 2)}&sortBy=submittedDate&sortOrder=descending")
    root = ET.fromstring(_request(url, headers={"Accept": "application/atom+xml"}))
    ns = {"a": "http://www.w3.org/2005/Atom"}
    out: list[EvidenceHit] = []
    for entry in root.findall("a:entry", ns):
        date = (entry.findtext("a:published", default="", namespaces=ns) or "")[:10]
        if date and date < start:
            continue
        authors = [a.findtext("a:name", default="", namespaces=ns) for a in entry.findall("a:author", ns)]
        out.append(EvidenceHit(
            "arxiv",
            re.sub(r"\s+", " ", entry.findtext("a:title", default="", namespaces=ns)).strip(),
            entry.findtext("a:id", default="", namespaces=ns),
            re.sub(r"\s+", " ", entry.findtext("a:summary", default="", namespaces=ns)).strip()[:1600],
            date,
            ", ".join(a for a in authors if a)[:500],
            0.82,
            {"acquisition_method": "arxiv_public_atom"},
        ))
    return _dedupe(out, limit)


def _github_headers() -> dict[str, str]:
    headers = {"Accept": "application/vnd.github+json"}
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def search_github(query: str, days: int, limit: int, enrich: bool = False) -> list[EvidenceHit]:
    start, _, _ = _window(days)
    out: list[EvidenceHit] = []
    for kind, endpoint, base in (("repository", "repositories", 0.80), ("issue", "issues", 0.72)):
        params = urllib.parse.urlencode({
            "q": f"{query} updated:>={start}", "sort": "updated", "order": "desc",
            "per_page": min(50, limit),
        })
        try:
            data = _json(f"https://api.github.com/search/{endpoint}?{params}", headers=_github_headers())
        except Exception:
            continue
        for index, row in enumerate(data.get("items", [])):
            if kind == "repository":
                owner = (row.get("owner") or {}).get("login")
                out.append(EvidenceHit(
                    "github", row.get("full_name") or row.get("name") or "GitHub repository",
                    row.get("html_url") or "", (row.get("description") or "")[:1000],
                    (row.get("updated_at") or "")[:10], owner,
                    min(0.98, base + min(0.15, int(row.get("stargazers_count") or 0) / 100000)),
                    {"kind": kind, "stars": row.get("stargazers_count"), "forks": row.get("forks_count"),
                     "language": row.get("language"), "acquisition_method": "github_public_rest"},
                ))
            else:
                out.append(EvidenceHit(
                    "github", row.get("title") or "GitHub issue/PR", row.get("html_url") or "",
                    (row.get("body") or "")[:1000], (row.get("updated_at") or "")[:10],
                    (row.get("user") or {}).get("login"), max(0.45, base - index * 0.01),
                    {"kind": "pull_request" if row.get("pull_request") else "issue", "state": row.get("state"),
                     "comments": row.get("comments"), "acquisition_method": "github_public_rest"},
                ))
    return _dedupe((hit for hit in out if hit.url), limit)


def _clean_vtt(text: str, max_words: int = 1800) -> str:
    rows: list[str] = []
    seen: set[str] = set()
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("WEBVTT") or "-->" in line or re.fullmatch(r"\d+", line):
            continue
        line = html.unescape(re.sub(r"<[^>]+>", "", line))
        line = re.sub(r"\s+", " ", line).strip()
        if line and line not in seen:
            seen.add(line)
            rows.append(line)
    return " ".join(" ".join(rows).split()[:max_words])


def _youtube_transcript(url: str) -> str:
    exe = shutil.which("yt-dlp")
    if not exe:
        return ""
    with tempfile.TemporaryDirectory(prefix="amd-yt-") as tmp:
        cmd = [exe, url, "--skip-download", "--write-subs", "--write-auto-subs",
               "--sub-langs", "fr.*,en.*", "--sub-format", "vtt",
               "-o", os.path.join(tmp, "%(id)s.%(ext)s"), "--quiet", "--no-warnings"]
        try:
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=40, check=False)
        except Exception:
            return ""
        for name in os.listdir(tmp):
            if name.endswith(".vtt"):
                try:
                    with open(os.path.join(tmp, name), encoding="utf-8", errors="replace") as handle:
                        return _clean_vtt(handle.read())
                except OSError:
                    pass
    return ""


def search_youtube(query: str, days: int, limit: int, enrich: bool = False) -> list[EvidenceHit]:
    start, _, _ = _window(days)
    exe = shutil.which("yt-dlp")
    out: list[EvidenceHit] = []
    if exe:
        cmd = [exe, f"ytsearch{limit}:{query}", "--dump-json", "--skip-download",
               "--dateafter", start.replace("-", ""), "--no-warnings"]
        try:
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                  text=True, timeout=120, check=False)
            for line in proc.stdout.splitlines():
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                video_id = row.get("id")
                url = row.get("webpage_url") or (f"https://www.youtube.com/watch?v={video_id}" if video_id else "")
                if not url:
                    continue
                date = row.get("upload_date")
                if isinstance(date, str) and len(date) == 8:
                    date = f"{date[:4]}-{date[4:6]}-{date[6:]}"
                views = int(row.get("view_count") or 0)
                likes = int(row.get("like_count") or 0)
                out.append(EvidenceHit(
                    "youtube", row.get("title") or "YouTube video", url,
                    (row.get("description") or "")[:1200], date,
                    row.get("channel") or row.get("uploader"),
                    min(0.98, 0.58 + 0.04 * max(0, len(str(views)) - 3) + 0.02 * max(0, len(str(likes)) - 2)),
                    {"views": views, "likes": likes, "duration": row.get("duration"),
                     "acquisition_method": "yt-dlp"},
                ))
        except Exception:
            out = []
    if not out:
        try:
            out = _web_index(f"site:youtube.com/watch {query}", limit, "youtube")
        except Exception:
            return []
    if enrich:
        for hit in out[: min(2, len(out))]:
            transcript = _youtube_transcript(hit.url)
            if transcript:
                hit.metadata["transcript"] = transcript
                hit.metadata["transcript_words"] = len(transcript.split())
                hit.relevance = min(0.99, hit.relevance + 0.08)
    return _dedupe(out, limit)


def search_twitter(query: str, days: int, limit: int, enrich: bool = False) -> list[EvidenceHit]:
    out: list[EvidenceHit] = []
    for lane in (f"site:x.com {query}", f"site:twitter.com {query}"):
        try:
            out.extend(_web_index(lane, max(4, limit // 2), "twitter"))
        except Exception:
            continue
    for hit in out:
        hit.metadata.update({"acquisition_method": "public_web_index", "authenticated_x_access": False})
    return _dedupe(out, limit)


def search_perplexity(query: str, days: int, limit: int, enrich: bool = False) -> list[EvidenceHit]:
    key = os.environ.get("PERPLEXITY_API_KEY", "").strip()
    if not key:
        out = search_web(query, days, limit)
        for hit in out:
            hit.source = "perplexity"
            hit.metadata.update({"perplexity_api_used": False, "fallback": "public_web_index"})
        return out
    start, end, _ = _window(days)
    payload = {
        "query": query,
        "max_results": min(20, limit),
        "search_after_date_filter": dt.datetime.strptime(start, "%Y-%m-%d").strftime("%m/%d/%Y"),
        "search_before_date_filter": dt.datetime.strptime(end, "%Y-%m-%d").strftime("%m/%d/%Y"),
    }
    data = _json(
        "https://api.perplexity.ai/search", method="POST", payload=payload,
        headers={"Authorization": f"Bearer {key}", "Accept": "application/json"},
    )
    out: list[EvidenceHit] = []
    for index, row in enumerate(data.get("results", [])):
        if not isinstance(row, dict) or not row.get("url"):
            continue
        out.append(EvidenceHit(
            "perplexity", row.get("title") or row["url"], row["url"],
            row.get("snippet") or "", row.get("date"), None,
            max(0.55, 0.88 - index * 0.03),
            {"acquisition_method": "perplexity_first_party_search_api", "perplexity_api_used": True},
        ))
    return _dedupe(out, limit)


SEARCHERS = {
    "web": search_web,
    "linkedin": search_linkedin,
    "reddit": search_reddit,
    "youtube": search_youtube,
    "twitter": search_twitter,
    "hackernews": search_hackernews,
    "github": search_github,
    "arxiv": search_arxiv,
    "perplexity": search_perplexity,
}


def source_limitations(source: str) -> list[str]:
    limits = ["Public/indexed evidence may be incomplete or stale; preserve publication and retrieval dates."]
    if source == "linkedin":
        limits += [
            "Public web index only; this is not the deferred LinkedIn connector.",
            "Indexed profile text cannot prove a current role or canonical identity.",
            "No authenticated LinkedIn page scraping or browser automation is performed.",
        ]
    elif source == "twitter":
        limits += ["Only public web-indexed X/Twitter results are used."]
    elif source == "youtube":
        limits += ["yt-dlp is optional; transcript coverage depends on publicly available subtitles/auto-captions."]
    elif source == "perplexity":
        limits += ["PERPLEXITY_API_KEY is optional and never persisted; without it this lane is a web-index fallback."]
    return limits


def main() -> int:
    parser = argparse.ArgumentParser(description="Acquire normalized public research evidence")
    parser.add_argument("query")
    parser.add_argument("--source", choices=sorted(SEARCHERS), required=True)
    parser.add_argument("--days", type=int, default=30)
    parser.add_argument("--limit", type=int, default=12)
    parser.add_argument("--enrich", action="store_true", help="Enable bounded source-specific enrichment")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    hits = SEARCHERS[args.source](args.query, max(1, args.days), max(1, min(args.limit, 50)), args.enrich)
    print(json.dumps({
        "query": args.query,
        "source": args.source,
        "days": args.days,
        "count": len(hits),
        "results": [asdict(hit) for hit in hits],
        "limitations": source_limitations(args.source),
    }, ensure_ascii=False, indent=2 if args.pretty else None))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
