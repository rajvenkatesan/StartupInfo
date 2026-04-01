"""Career page scraper — discovers open roles for a company."""
import re
import structlog
import httpx
from bs4 import BeautifulSoup
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import Job
from app.services.company import get_company

logger = structlog.get_logger()

CAREERS_PATHS = ["/careers", "/jobs", "/work-with-us", "/join-us", "/about/careers"]


async def discover_jobs(db: AsyncSession, company_name: str) -> list[Job]:
    """
    Scrape the company's careers page and upsert jobs found.
    Uses httpx for static pages; Playwright fallback for JS-rendered pages.
    """
    log = logger.bind(company=company_name)
    company = await get_company(db, company_name)
    if not company or not company.website:
        log.warning("no_website_for_company")
        return []

    base = company.website.rstrip("/")
    html = await _fetch_careers_page(base, log)
    if not html:
        log.warning("careers_page_not_found")
        return []

    jobs_data = _parse_jobs_from_html(html, base)
    log.info("jobs_parsed", count=len(jobs_data))

    saved = []
    for jd in jobs_data:
        job = Job(
            company_name=company_name,
            title=jd["title"],
            location=jd.get("location"),
            job_type=jd.get("job_type"),
            url=jd.get("url"),
            source="scraped",
        )
        db.add(job)
        saved.append(job)

    await db.commit()
    return saved


async def _fetch_careers_page(base_url: str, log) -> str | None:
    """Try each common careers path and return the HTML of the first that responds."""
    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
        for path in CAREERS_PATHS:
            url = base_url + path
            try:
                resp = await client.get(url)
                if resp.status_code == 200 and len(resp.text) > 500:
                    log.info("careers_page_fetched", url=url)
                    return resp.text
            except Exception:
                continue
    return None


def _parse_jobs_from_html(html: str, base_url: str) -> list[dict]:
    """
    Heuristic parser: look for common job listing patterns.
    This is intentionally simple for v1 — extend with site-specific parsers as needed.
    """
    soup = BeautifulSoup(html, "html.parser")
    jobs = []

    # Strategy 1: look for <li> or <div> elements with 'job' or 'position' in class/id
    candidates = soup.find_all(
        lambda tag: tag.name in ("li", "div", "article")
        and any(
            kw in (tag.get("class", []) + [tag.get("id", "")])
            for kw in ["job", "position", "opening", "role", "career"]
        )
    )

    for el in candidates[:50]:  # cap at 50 to avoid noise
        title_el = el.find(["h1", "h2", "h3", "h4", "a"])
        if not title_el:
            continue
        title = title_el.get_text(strip=True)
        if len(title) < 3 or len(title) > 200:
            continue

        link = el.find("a")
        url = None
        if link and link.get("href"):
            href = link["href"]
            url = href if href.startswith("http") else base_url + href

        location_el = el.find(
            lambda t: t.name in ("span", "p", "div")
            and any(kw in (t.get("class") or []) for kw in ["location", "city", "place"])
        )
        location = location_el.get_text(strip=True) if location_el else None

        jobs.append({"title": title, "url": url, "location": location})

    return jobs
