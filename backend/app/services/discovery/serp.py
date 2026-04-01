"""
Search client — uses DuckDuckGo (free, no API key required).
Replaced SerpAPI on 2026-03-31. No credentials needed.
Install: duckduckgo-search (already in pyproject.toml dependencies).
"""
import structlog
from duckduckgo_search import DDGS

logger = structlog.get_logger()


async def serp_search(query: str, num: int = 10) -> list[dict]:
    """
    Search the web via DuckDuckGo and return results.
    Return shape is normalised to match the rest of the discovery service:
      [{"title": ..., "snippet": ..., "link": ...}, ...]
    """
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=num))
        # DDG returns "body" for the snippet text; normalise to "snippet"
        normalised = [
            {
                "title":   r.get("title", ""),
                "snippet": r.get("body", ""),
                "link":    r.get("href", ""),
            }
            for r in results
        ]
        logger.info("ddg_search_ok", query=query, hits=len(normalised))
        return normalised
    except Exception as exc:
        logger.error("ddg_search_failed", query=query, error=str(exc))
        return []
