from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "advanced_research.py"
SPEC = spec_from_file_location("advanced_research", MODULE_PATH)
assert SPEC and SPEC.loader
research = module_from_spec(SPEC)
SPEC.loader.exec_module(research)


def test_required_sources_are_available():
    assert {
        "reddit",
        "youtube",
        "twitter",
        "hackernews",
        "github",
        "arxiv",
        "linkedin",
        "perplexity",
        "web",
    }.issubset(research.SEARCHERS)


def test_linkedin_is_public_index_only():
    limitations = " ".join(research.source_limitations("linkedin")).lower()
    assert "not the deferred linkedin connector" in limitations
    assert "cannot prove a current role" in limitations
    assert "no authenticated linkedin page scraping" in limitations


def test_dedupe_prefers_highest_relevance():
    a = research.EvidenceHit("web", "a", "https://example.com/x?ref=1", relevance=0.4)
    b = research.EvidenceHit("web", "b", "https://example.com/x#section", relevance=0.9)
    items = research._dedupe([a, b], 10)
    assert len(items) == 1
    assert items[0].title == "b"


def test_perplexity_policy_does_not_require_key():
    limitations = " ".join(research.source_limitations("perplexity")).lower()
    assert "optional" in limitations
    assert "never persisted" in limitations
