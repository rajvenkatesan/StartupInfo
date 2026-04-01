"""Background task: discover company details and investors via DuckDuckGo web search."""
import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services import company as company_svc
from app.services import investor as investor_svc
from app.services.discovery.serp import serp_search
from app.schemas.investment import InvestmentCreate

logger = structlog.get_logger()


async def discover_company(db: AsyncSession, company_name: str) -> None:
    """
    Main discovery task.
    1. Sets company status to 'discovering'.
    2. Searches for company info and investors via DuckDuckGo.
    3. Upserts company, investors, and investments.
    4. Sets status to 'ready' (or 'error' on failure).
    """
    log = logger.bind(company=company_name)
    log.info("discovery_started")

    await company_svc.set_company_status(db, company_name, "discovering")

    try:
        # --- Company profile search ---
        results = await serp_search(f"{company_name} startup company overview founders mission")
        snippet = results[0].get("snippet", "") if results else ""

        await company_svc.upsert_company(db, {
            "company_name": company_name.strip().lower(),
            "status": "discovering",
            "description": snippet or None,
        })

        # --- Investor / funding search ---
        funding_results = await serp_search(
            f"{company_name} startup investors funding rounds series", num=5
        )
        log.info("funding_results_fetched", count=len(funding_results))

        # Parse investor mentions from snippets (simplified extractor)
        # In production this would use a more robust NLP/structured extraction
        investors_found = _extract_investors_from_snippets(funding_results)

        for inv_data in investors_found:
            await investor_svc.upsert_investor(db, {
                "investor_name": inv_data["name"],
                "investor_type": inv_data.get("type", "vc_firm"),
            })
            await investor_svc.upsert_investment(
                db,
                InvestmentCreate(
                    company_name=company_name.strip().lower(),
                    investor_name=inv_data["name"],
                    series_name=inv_data.get("series", "Unknown"),
                    investor_role=inv_data.get("role"),
                ),
            )

        await company_svc.set_company_status(db, company_name, "ready")
        log.info("discovery_complete")

    except Exception as exc:
        log.error("discovery_failed", error=str(exc))
        await company_svc.set_company_status(db, company_name, "error")


def _extract_investors_from_snippets(results: list[dict]) -> list[dict]:
    """
    Simplified: scan snippets for known VC firm keywords.
    Replace with structured extraction (Crunchbase / LLM) in v2.
    """
    known_patterns = [
        ("Sequoia Capital", "vc_firm"),
        ("Andreessen Horowitz", "vc_firm"),
        ("a16z", "vc_firm"),
        ("Y Combinator", "accelerator"),
        ("Benchmark", "vc_firm"),
        ("Founders Fund", "vc_firm"),
        ("Tiger Global", "vc_firm"),
        ("Google Ventures", "corporate"),
        ("GV", "corporate"),
        ("Spark Capital", "vc_firm"),
    ]
    found = []
    all_text = " ".join(r.get("snippet", "") + " " + r.get("title", "") for r in results)
    for name, inv_type in known_patterns:
        if name.lower() in all_text.lower():
            found.append({"name": name, "type": inv_type, "series": "Unknown"})
    return found
