"""
Search client — uses DuckDuckGo (free, no API key required).
Runs the synchronous DDGS client in a thread executor to avoid blocking the event loop.
A hard timeout of DDG_TIMEOUT_S seconds is applied so a slow/rate-limited response
never hangs the discovery pipeline indefinitely.
"""
import asyncio
import structlog
from duckduckgo_search import DDGS

logger = structlog.get_logger()

DDG_TIMEOUT_S = 12   # seconds before we give up on a single DDG query


def _ddg_text_sync(query: str, num: int) -> list[dict]:
    """Blocking DuckDuckGo search — runs in a thread executor."""
    with DDGS() as ddgs:
        return list(ddgs.text(query, max_results=num))


async def serp_search(query: str, num: int = 10) -> list[dict]:
    """
    Search the web via DuckDuckGo and return normalised results.
    Returns an empty list (never raises) on timeout or any error.
    Return shape: [{"title": ..., "snippet": ..., "link": ...}, ...]
    """
    try:
        loop = asyncio.get_event_loop()
        results = await asyncio.wait_for(
            loop.run_in_executor(None, _ddg_text_sync, query, num),
            timeout=DDG_TIMEOUT_S,
        )
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
    except asyncio.TimeoutError:
        logger.warning("ddg_search_timeout", query=query, timeout=DDG_TIMEOUT_S)
        return []
    except Exception as exc:
        logger.error("ddg_search_failed", query=query, error=str(exc))
        return []
