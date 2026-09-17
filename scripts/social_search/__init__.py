from .core import VERSION,Result,SourceRun,dedupe,search_web
from .linkedin import search_linkedin
from .youtube import search_youtube
from .community import search_hackernews,search_github,search_reddit,github_token,_reddit_ref
from .research import search_arxiv,search_x,search_perplexity
SELECTED_SOURCES=("reddit","youtube","x","hackernews","github","arxiv","linkedin","perplexity","web")
SEARCHERS={"web":search_web,"linkedin":search_linkedin,"youtube":search_youtube,"hackernews":search_hackernews,"arxiv":search_arxiv,"github":search_github,"reddit":search_reddit,"x":search_x,"perplexity":search_perplexity}
