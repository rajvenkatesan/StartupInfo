"""
Structured data extractor — parses raw HTML / plain text into typed company fields.
All functions are pure (no I/O) and operate on text already fetched by the caller.
"""
from __future__ import annotations

import re
from bs4 import BeautifulSoup, Tag

# ── Compiled patterns ─────────────────────────────────────────────────────────

_FOUNDED_RE = re.compile(
    r"(?:founded|established|incorporated|launched|started|since)\s*(?:in\s+)?(\d{4})",
    re.IGNORECASE,
)
_YEAR_BARE_RE = re.compile(r"\b(20[0-2]\d|199\d)\b")   # 1990-2029 as fallback

_FUNDING_AMOUNT_RE = re.compile(
    r"\$\s*(\d+(?:\.\d+)?)\s*([BMK])\b",
    re.IGNORECASE,
)
_TOTAL_RAISED_RE = re.compile(
    r"(?:raised?|secured?|closed?|total\s+funding|total\s+raised?)\s+\$\s*(\d+(?:\.\d+)?)\s*([BMK])\b",
    re.IGNORECASE,
)

_SERIES_RE = re.compile(
    r"\b(Pre[-\s]?Seed|Seed|Series\s+[A-G]|Series\s+[A-G]\+|Growth|Late\s+Stage|IPO|Pre[-\s]?IPO)\b",
    re.IGNORECASE,
)

_EMPLOYEE_RE = re.compile(
    r"(\d[\d,]*(?:\+)?)\s*(?:[-–]\s*(\d[\d,]*))?\s*\+?\s*(?:employees?|people|team\s+members?|staff)",
    re.IGNORECASE,
)
_EMPLOYEE_RANGE_RE = re.compile(
    r"\b(\d{1,4}[,\d]*)\s*[-–]\s*(\d{1,4}[,\d]*)\s+(?:employees?|people|staff)\b",
    re.IGNORECASE,
)

_HQ_RE = re.compile(
    r"(?:headquartered|based|located|offices?)\s+in\s+([A-Z][a-zA-Z\s,]+?)(?:\.|,\s+[A-Z][a-z]|$)",
    re.IGNORECASE,
)

# Name patterns deliberately NOT case-insensitive so [A-Z] only matches
# true title-case proper nouns and won't capture words like "and", "the".
_FOUNDER_NAME_RE = re.compile(
    r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})"
    r"[\s,]+(?:is\s+)?(?:the\s+)?(?:[Cc]o-?)?[Ff]ounder"
    r"|(?:[Cc]o-?)?[Ff]ounder[^,\n]{0,20},?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})",
)
_EXEC_TITLE_RE = re.compile(
    r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})"
    r"[\s,]+(?:CEO|CTO|COO|CPO|CFO|Chief\s+[A-Z]\w+\s+Officer)",
)

# Broad investor name extraction — "backed by X", "investors include X and Y", "X led the round"
_INVESTOR_BACKED_RE = re.compile(
    r"(?:backed\s+by|investors?\s+include[sd]?|funded\s+by|led\s+by|support(?:ed)?\s+by)"
    r"\s+([A-Z][A-Za-z\s&,]+?)(?:\s+and\s+([A-Z][A-Za-z\s&]+?))?(?:\.|,\s+(?:and\s+)?[a-z]|$)",
    re.IGNORECASE,
)
_KNOWN_INVESTORS: list[tuple[str, str]] = [
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
    ("Accel", "vc_firm"),
    ("Kleiner Perkins", "vc_firm"),
    ("Lightspeed", "vc_firm"),
    ("General Catalyst", "vc_firm"),
    ("Bessemer", "vc_firm"),
    ("Index Ventures", "vc_firm"),
    ("Greylock", "vc_firm"),
    ("NEA", "vc_firm"),
    ("Insight Partners", "vc_firm"),
    ("SoftBank", "vc_firm"),
    ("Intel Capital", "corporate"),
    ("Microsoft Ventures", "corporate"),
    ("Google", "corporate"),
    ("Amazon", "corporate"),
    ("Salesforce Ventures", "corporate"),
    ("Qualcomm Ventures", "corporate"),
    ("Lux Capital", "vc_firm"),
    ("Eclipse", "vc_firm"),
    ("Mayfield", "vc_firm"),
]


# ── Public API ─────────────────────────────────────────────────────────────────

def extract_from_html(html: str, url: str) -> dict:
    """Parse an HTML page and return all extractable company fields."""
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True)
    data: dict = {}

    # description
    meta = (
        soup.find("meta", attrs={"name": "description"})
        or soup.find("meta", attrs={"property": "og:description"})
    )
    if meta and meta.get("content"):
        data["description"] = meta["content"].strip()

    # about / mission / vision from labelled sections
    _extract_labelled_sections(soup, data)

    # founders from page text
    founders = _extract_founders(text)
    if founders:
        data["founders"] = founders

    # founded year
    year = _extract_founded_year(text)
    if year:
        data["founded_year"] = year

    # headquarters
    hq = _extract_headquarters(text)
    if hq:
        data["headquarters"] = hq

    # employee count
    emp = _extract_employee_count(text)
    if emp:
        data["employee_count"] = emp

    # industry — og:site_name or <title> keywords as heuristic
    industry = _extract_industry(soup, text)
    if industry:
        data["industry"] = industry

    # funding
    funding = _extract_total_funding(text)
    if funding:
        data["total_funding_usd"] = funding

    # latest series
    series = _extract_latest_series(text)
    if series:
        data["latest_series"] = series

    # products — h2/h3 inside "product" or "platform" sections
    products = _extract_products(soup)
    if products:
        data["products"] = products

    # investors mentioned inline
    investors = _extract_investors_from_text(text)
    if investors:
        data["_investors"] = investors     # underscore → handled separately

    data["website"] = url
    return data


def extract_from_text(text: str) -> dict:
    """Extract fields from plain text (e.g. DuckDuckGo snippets)."""
    data: dict = {}

    year = _extract_founded_year(text)
    if year:
        data["founded_year"] = year

    hq = _extract_headquarters(text)
    if hq:
        data["headquarters"] = hq

    emp = _extract_employee_count(text)
    if emp:
        data["employee_count"] = emp

    funding = _extract_total_funding(text)
    if funding:
        data["total_funding_usd"] = funding

    series = _extract_latest_series(text)
    if series:
        data["latest_series"] = series

    founders = _extract_founders(text)
    if founders:
        data["founders"] = founders

    investors = _extract_investors_from_text(text)
    if investors:
        data["_investors"] = investors

    return data


# ── Private helpers ────────────────────────────────────────────────────────────

def _extract_labelled_sections(soup: BeautifulSoup, data: dict) -> None:
    for tag in soup.find_all(["section", "div", "article", "p"], limit=300):
        text = tag.get_text(" ", strip=True)
        if not text or len(text) < 30:
            continue
        tag_id = (tag.get("id") or "").lower()
        tag_class = " ".join(tag.get("class") or []).lower()
        label = tag_id + " " + tag_class

        if not data.get("about") and any(k in label for k in ("about", "who-we-are", "our-story", "company")):
            data["about"] = text[:600]
        if not data.get("mission") and "mission" in label:
            data["mission"] = text[:400]
        if not data.get("vision") and "vision" in label:
            data["vision"] = text[:400]


def _extract_founders(text: str) -> list[str]:
    found: list[str] = []
    for m in _FOUNDER_NAME_RE.finditer(text):
        name = (m.group(1) or m.group(2) or "").strip()
        if name and name not in found and len(name.split()) >= 2:
            found.append(name)
    # also grab CEO/CTO names as they are often founders
    for m in _EXEC_TITLE_RE.finditer(text):
        name = m.group(1).strip()
        if name and name not in found and len(name.split()) >= 2:
            found.append(name)
    return found[:10]  # cap to avoid noise


def _extract_founded_year(text: str) -> int | None:
    m = _FOUNDED_RE.search(text)
    if m:
        return int(m.group(1))
    # fallback: first plausible year near a relevant keyword
    for kw in ("founded", "launched", "started", "incorporated"):
        idx = text.lower().find(kw)
        if idx != -1:
            snippet = text[max(0, idx - 10): idx + 60]
            ym = _YEAR_BARE_RE.search(snippet)
            if ym:
                return int(ym.group(1))
    return None


def _extract_headquarters(text: str) -> str | None:
    m = _HQ_RE.search(text)
    if m:
        return m.group(1).strip().rstrip(",")
    return None


def _extract_employee_count(text: str) -> str | None:
    m = _EMPLOYEE_RANGE_RE.search(text)
    if m:
        return f"{m.group(1)}-{m.group(2)}"
    m = _EMPLOYEE_RE.search(text)
    if m:
        low = m.group(1).replace(",", "")
        high = m.group(2).replace(",", "") if m.group(2) else None
        return f"{low}-{high}" if high else f"{low}+"
    return None


def _extract_industry(soup: BeautifulSoup, text: str) -> str | None:
    # og:site_name or keywords meta
    kw_meta = soup.find("meta", attrs={"name": "keywords"})
    if kw_meta and kw_meta.get("content"):
        return kw_meta["content"].strip()[:100]
    return None


def _parse_usd(amount: str, suffix: str) -> int:
    val = float(amount)
    suffix = suffix.upper()
    if suffix == "B":
        return int(val * 1_000_000_000)
    if suffix == "M":
        return int(val * 1_000_000)
    if suffix == "K":
        return int(val * 1_000)
    return int(val)


def _extract_total_funding(text: str) -> int | None:
    # prefer explicit "raised $X" pattern
    m = _TOTAL_RAISED_RE.search(text)
    if m:
        return _parse_usd(m.group(1), m.group(2))
    # fall back to largest funding amount mentioned
    amounts = [_parse_usd(m.group(1), m.group(2)) for m in _FUNDING_AMOUNT_RE.finditer(text)]
    return max(amounts) if amounts else None


def _extract_latest_series(text: str) -> str | None:
    # Return the last (most recent) series found
    matches = _SERIES_RE.findall(text)
    if not matches:
        return None
    # Normalise spacing
    return re.sub(r"\s+", " ", matches[-1]).strip().title()


def _extract_products(soup: BeautifulSoup) -> list[str]:
    products: list[str] = []
    for tag in soup.find_all(["section", "div"], limit=200):
        tag_id = (tag.get("id") or "").lower()
        tag_class = " ".join(tag.get("class") or []).lower()
        label = tag_id + " " + tag_class
        if any(k in label for k in ("product", "platform", "solution", "offering")):
            for h in tag.find_all(["h2", "h3", "h4"]):
                name = h.get_text(strip=True)
                if name and 2 < len(name) < 80 and name not in products:
                    products.append(name)
    return products[:10]


def _extract_investors_from_text(text: str) -> list[dict]:
    found: list[dict] = []
    seen: set[str] = set()

    # 1. Match known investors by name
    for name, inv_type in _KNOWN_INVESTORS:
        if name.lower() in text.lower() and name not in seen:
            found.append({"name": name, "type": inv_type})
            seen.add(name)

    # 2. Try to parse investor names from "backed by / led by" patterns
    for m in _INVESTOR_BACKED_RE.finditer(text):
        for grp in (m.group(1), m.group(2)):
            if not grp:
                continue
            name = grp.strip().rstrip(".")
            if len(name) > 3 and name not in seen:
                found.append({"name": name, "type": "vc_firm"})
                seen.add(name)

    return found
