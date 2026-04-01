"""
Background task: deep-discover a company by scraping its pages and running
targeted web searches, then persist everything to the database.
"""
from __future__ import annotations

import asyncio
import structlog
import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.services import company as company_svc
from app.services import investor as investor_svc
from app.services.discovery.extractor import extract_from_html, extract_from_text
from app.services.discovery.serp import serp_search
from app.schemas.investment import InvestmentCreate

logger = structlog.get_logger()

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}

# Fields written from scraped / searched data — ordered so that
# scraping (higher quality) is preferred over search snippets.
_COMPANY_FIELDS = (
    "description", "about", "mission", "vision", "founders",
    "website", "headquarters", "founded_year", "employee_count",
    "industry", "total_funding_usd", "latest_series", "products",
)


async def discover_company(db: AsyncSession, company_name: str) -> None:
    """
    Full discovery pipeline:
      1. Set status → 'discovering'
      2. Scrape company_url  (primary source)
      3. Scrape every related_url  (merge missing fields)
      4. Run targeted DuckDuckGo searches in parallel for:
           - general overview / description
           - founders / leadership
           - funding / investors / series
      5. Persist company fields + investors + investments
      6. Set status → 'ready' (or 'error')
    """
    log = logger.bind(company=company_name)
    log.info("discovery_started")
    await company_svc.set_company_status(db, company_name, "discovering")

    try:
        company = await company_svc.get_company(db, company_name)
        company_url  = (company.company_url  or "").strip() if company else ""
        related_urls = (company.related_urls or [])         if company else []

        merged: dict = {}

        # ── Step 1: scrape company_url ────────────────────────────────────────
        if company_url:
            page = await _fetch_page(company_url, log)
            if page:
                data = extract_from_html(page, company_url)
                _merge(merged, data)
                log.info("company_url_scraped", fields=_visible(data))
        else:
            log.warning("no_company_url_set")

        # ── Step 2: scrape related_urls ───────────────────────────────────────
        for url in related_urls:
            page = await _fetch_page(url, log)
            if page:
                data = extract_from_html(page, url)
                _merge(merged, data)
                log.info("related_url_scraped", url=url, fields=_visible(data))

        # ── Step 3: sequential DuckDuckGo searches (2 s gap to avoid rate-limits) ──
        # Parallel requests reliably trigger DDG rate-limiting, causing threads to
        # hang. Each query already has a DDG_TIMEOUT_S hard timeout in serp_search.
        queries = {
            "overview":  f"{company_name} startup company overview about",
            "founders":  f"{company_name} founders CEO CTO leadership team",
            "funding":   f"{company_name} funding raised investors series round",
        }
        search_results_list = []
        for q in queries.values():
            search_results_list.append(await serp_search(q, num=5))
            await asyncio.sleep(2)
        search_results = search_results_list

        for label, results in zip(queries.keys(), search_results):
            if isinstance(results, Exception) or not results:
                continue
            keyword = company_name.split(".")[0].lower()
            all_text = " ".join(
                r.get("title", "") + " " + r.get("snippet", "") for r in results
            )
            # Only use snippets that actually mention the company name
            if keyword not in all_text.lower():
                log.info("ddg_irrelevant", query=label)
                continue
            extracted = extract_from_text(all_text)
            _merge(merged, extracted)
            log.info("ddg_extracted", query=label, fields=_visible(extracted))

            # For description: grab the first on-topic snippet
            if not merged.get("description") and label == "overview":
                for r in results:
                    snippet = r.get("snippet", "")
                    if keyword in snippet.lower():
                        merged["description"] = snippet
                        break

        # ── Step 4: persist company fields ───────────────────────────────────
        update_payload: dict = {"company_name": company_name.strip().lower()}
        for field in _COMPANY_FIELDS:
            val = merged.get(field)
            if val is not None and val != [] and val != "":
                update_payload[field] = val

        if len(update_payload) > 1:
            await company_svc.upsert_company(db, update_payload)
            log.info("company_persisted", fields=list(update_payload.keys()))
        else:
            log.warning("no_data_extracted")

        # ── Step 5: persist investors & investments ───────────────────────────
        investors_found: list[dict] = merged.get("_investors", [])
        series = merged.get("latest_series", "Unknown")

        for inv in investors_found:
            await investor_svc.upsert_investor(db, {
                "investor_name": inv["name"],
                "investor_type": inv.get("type", "vc_firm"),
            })
            await investor_svc.upsert_investment(
                db,
                InvestmentCreate(
                    company_name=company_name.strip().lower(),
                    investor_name=inv["name"],
                    series_name=inv.get("series") or series or "Unknown",
                    investor_role=inv.get("role"),
                ),
            )
        if investors_found:
            log.info("investors_persisted", count=len(investors_found))

        await company_svc.set_company_status(db, company_name, "ready")
        log.info("discovery_complete")

    except Exception as exc:
        log.error("discovery_failed", error=str(exc))
        await company_svc.set_company_status(db, company_name, "error")


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _fetch_page(url: str, log) -> str | None:
    """Fetch a URL and return the HTML body, or None on failure."""
    if not url.startswith("http"):
        url = "https://" + url
    try:
        async with httpx.AsyncClient(
            headers=_HEADERS, timeout=15, follow_redirects=True
        ) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return resp.text
    except Exception as exc:
        log.warning("fetch_failed", url=url, error=str(exc))
        return None


def _merge(base: dict, incoming: dict) -> None:
    """
    Merge `incoming` into `base`, keeping existing values unless the
    incoming value is richer (longer string, non-empty list).
    The special `_investors` key is always extended, never replaced.
    """
    for k, v in incoming.items():
        if not v and v != 0:
            continue
        if k == "_investors":
            existing = base.get("_investors", [])
            seen_names = {i["name"] for i in existing}
            base["_investors"] = existing + [i for i in v if i["name"] not in seen_names]
            continue
        if k not in base:
            base[k] = v
        elif isinstance(v, str) and isinstance(base[k], str) and len(v) > len(base[k]):
            base[k] = v        # keep the longer / richer string
        elif isinstance(v, list) and (not base[k] or len(v) > len(base[k])):
            base[k] = v


def _visible(data: dict) -> list[str]:
    """Return the non-private extracted field names for logging."""
    return [k for k, v in data.items() if v and not k.startswith("_")]
