#!/usr/bin/env python3
"""
Phase 1 - Discovery Scraper v2 (Search-first)
==============================================
Strategy: use DuckDuckGo search to find the exact MCH page on each
county's health department website, then fetch that page and extract
program links.

No HEAD probing. No nav-chain heuristics. No scoring pyramids.
Search → fetch → extract. That's it.

INSTALL:  pip install aiohttp beautifulsoup4 lxml duckduckgo-search
USAGE:
  python scraper_discovery_v2.py                        # all 58 counties
  python scraper_discovery_v2.py --county Alameda Fresno
  python scraper_discovery_v2.py --concurrency 4
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import time
from collections import Counter
from datetime import datetime
from typing import Callable, Dict, List, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse

import aiohttp
from bs4 import BeautifulSoup
from ddgs import DDGS

from src.config import CALIFORNIA_COUNTIES, HEALTH_DEPT_URLS, MATERNAL_HEALTH_URLS
from src.maternal_taxonomy import classify_program, is_maternal_health_program, is_non_maternal_program, score_maternal_relevance
from src.federal_program_registry import get_aliases_flat

# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

FETCH_TIMEOUT   = 15
CONCURRENCY     = 4    # keep low — DDG rate-limits aggressive callers
DDG_DELAY       = 1.5  # seconds between DDG calls (avoid 202 rate-limit)
MAX_PROG_LINKS  = 30
# Minimum score for a link to be considered a program candidate during the
# "strict" discovery pass. We also run a relaxed pass if strict finds nothing.
MIN_PROG_SCORE  = 1.0

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

_CA_ALIASES: Set[str] = set(get_aliases_flat("CA").keys())

# Lightweight maternal keywords used only for the relaxed discovery fallback.
# This avoids dropping entire counties when the taxonomy-based scoring misses
# due to naming/markup differences on county sites.
_BASIC_MATERNAL_KEYWORDS: Set[str] = {
    "wic",
    "prenatal",
    "postpartum",
    "pregnancy",
    "maternal",
    "mch",
    "mcah",
    "perinatal",
    "home visiting",
    "doula",
    "midwife",
    "midwifery",
    "breastfeeding",
    "lactation",
    "black infant health",
    "bih",
    "healthy start",
    "first 5",
    "teen pregnancy",
    "title v",
    "family planning",
    "reproductive health",
}


def _basic_maternal_hit(href: str, text: str) -> bool:
    combined = (text + " " + href).lower()
    return any(kw in combined for kw in _BASIC_MATERNAL_KEYWORDS)

# Search query templates — tried in order until one returns a result
# on the county's own domain
SEARCH_TEMPLATES = [
    '"{county}" county health department WIC maternal prenatal California',
    '"{county}" county "maternal child health" OR "MCAH" OR "WIC" California',
    '"{county}" county health "home visiting" OR "prenatal" OR "Black Infant Health"',
    '"{county}" county "maternal child adolescent health" WIC',
    '"{county}" county health department "women infants children" prenatal postpartum',
    '"{county}" county WIC program "apply" California',
]

# UI chrome link text — skip these before scoring
_SKIP_TEXT: Set[str] = {
    "skip to main content", "skip to content", "click here to learn more",
    "click here", "learn more", "read more", "more information",
    "staff login", "login", "sign in", "back to top", "home",
    "contact us", "sitemap", "accessibility", "translate", "search",
    "menu", "close", "español", "",
}

_SKIP_URL_SEGS: Set[str] = {
    "login", "sign-in", "logout", "admin", "news", "press-release",
    "blog", "event", "calendar", "permit", "job", "career",
    "agendas", "minutes", "board", "facebook.com", "twitter.com",
    "instagram.com", "youtube.com",
}

# ─────────────────────────────────────────────────────────────────────────────
# DuckDuckGo search (sync, called in executor to avoid blocking event loop)
# ─────────────────────────────────────────────────────────────────────────────

def _ddg_search(query: str, max_results: int = 8, retries: int = 3) -> List[Dict]:
    """
    Run a DDG text search and return result dicts with 'href' and 'title'.
    Retries with exponential backoff on rate-limit (202) or empty results.
    Returns [] on persistent failure.
    """
    for attempt in range(retries):
        try:
            ddgs = DDGS()
            results = list(ddgs.text(query, max_results=max_results))
            if results:
                return results
            # Empty result — might be transient rate-limit, wait and retry
            if attempt < retries - 1:
                time.sleep(DDG_DELAY * (2 ** attempt))
        except Exception:
            if attempt < retries - 1:
                time.sleep(DDG_DELAY * (2 ** attempt))
    return []


def _county_domain(county_name: str) -> Optional[str]:
    """
    Derive the expected county domain from HEALTH_DEPT_URLS or CALIFORNIA_COUNTIES.
    Returns e.g. 'acgov.org' or 'co.alameda.ca.us'.
    """
    base = HEALTH_DEPT_URLS.get(county_name) or CALIFORNIA_COUNTIES.get(county_name, "")
    if not base:
        return None
    netloc = urlparse(base).netloc.lstrip("www.")
    return netloc or None


def _find_mch_url_via_search(county_name: str) -> Optional[str]:
    """
    Try each search template until we get a result URL on the county's domain.
    Returns the best matching URL or None.
    Adds a small delay between calls to avoid DDG rate-limiting.
    """
    domain = _county_domain(county_name)

    for template in SEARCH_TEMPLATES:
        query = template.format(county=county_name)
        results = _ddg_search(query, max_results=8)
        time.sleep(DDG_DELAY)

        if not results:
            continue

        # Prefer results on the county's own domain
        if domain:
            for r in results:
                href = r.get("href", "")
                if not href:
                    continue
                href_l = href.lower()
                if href_l.endswith(".pdf") or "/.pdf" in href_l or "pdf" in href_l:
                    continue
                if domain in href:
                    return href

        # Fallback: return first non-PDF result that looks like a .gov/.us page
        for r in results:
            href = r.get("href", "")
            href_l = (href or "").lower()
            if not re.search(r"\.(gov|us|ca\.us)(/|$)", href_l):
                continue
            if href_l.endswith(".pdf") or "/.pdf" in href_l or "pdf" in href_l:
                continue
            return href

    return None


def _find_mch_url_candidates_via_search(
    county_name: str,
    *,
    max_candidates: int = 6,
) -> List[str]:
    """
    Return multiple candidate MCH seed URLs for a county.

    Used when the first seed yields 0 program links; we want recall over precision.
    """
    domain = _county_domain(county_name)
    candidates: List[str] = []
    seen: Set[str] = set()

    for template in SEARCH_TEMPLATES:
        query = template.format(county=county_name)
        results = _ddg_search(query, max_results=8)
        time.sleep(DDG_DELAY)
        for r in results:
            href = r.get("href", "")
            if not href or not href.startswith("http"):
                continue
            href_l = href.lower()
            if href_l.endswith(".pdf") or "/.pdf" in href_l or "pdf" in href_l:
                continue
            if href in seen:
                continue

            # Prefer same-domain candidates when possible.
            if domain and domain in href:
                candidates.append(href)
                seen.add(href)
            elif not domain and re.search(r"\.(gov|us|ca\.us)(/|$)", href_l):
                candidates.append(href)
                seen.add(href)

            if len(candidates) >= max_candidates:
                return candidates

    return candidates[:max_candidates]

# ─────────────────────────────────────────────────────────────────────────────
# HTTP fetch
# ─────────────────────────────────────────────────────────────────────────────

async def _get(session: aiohttp.ClientSession, url: str) -> Optional[str]:
    try:
        async with session.get(
            url, headers=HEADERS,
            timeout=aiohttp.ClientTimeout(total=FETCH_TIMEOUT),
            allow_redirects=True,
        ) as r:
            if r.status >= 400:
                return None
            return await r.text(errors="replace")
    except Exception:
        return None


def _parse_links(html: str, base_url: str) -> List[Tuple[str, str]]:
    try:
        soup = BeautifulSoup(html, "lxml")
    except Exception:
        soup = BeautifulSoup(html, "html.parser")
    for el in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
        el.decompose()
    out: List[Tuple[str, str]] = []
    for a in soup.find_all("a", href=True):
        href = urljoin(base_url, a["href"])
        text = a.get_text(separator=" ", strip=True)
        if href.startswith("http"):
            out.append((href, text))
    return out


def same_domain(base: str, candidate: str) -> bool:
    try:
        b = urlparse(base).netloc
        c = urlparse(candidate).netloc
        return c == b or c.endswith("." + b)
    except Exception:
        return False

# ─────────────────────────────────────────────────────────────────────────────
# Program link scoring and extraction
# ─────────────────────────────────────────────────────────────────────────────

def _score_program_link(href: str, text: str) -> float:
    combined = (text + " " + href).lower()
    path_segs = set(re.split(r"[/\-_.]", urlparse(href).path.lower()))

    if path_segs & _SKIP_URL_SEGS:
        return 0.0
    if text.lower().strip() in _SKIP_TEXT:
        return 0.0

    score = 0.0

    # Registry alias hit — strongest signal
    if any(alias in combined for alias in _CA_ALIASES):
        score += 3.0

    # Maternal taxonomy signals
    # Note: this is intentionally conservative (strict pass). We rely on the
    # relaxed fallback when strict fails to find any candidates.
    if is_maternal_health_program(text, href):
        score += 2.0
        score += score_maternal_relevance(text, href)

    # Penalties
    if any(d in href for d in ["facebook.com", "twitter.com", "instagram.com", "youtube.com"]):
        score -= 5.0
    if is_non_maternal_program(text, href):
        score -= 3.0

    return score


def _extract_program_links(
    html: str,
    base_url: str,
    *,
    min_score: float = MIN_PROG_SCORE,
    max_links: int = MAX_PROG_LINKS,
    allow_external: bool = False,
) -> List[Dict]:
    links = _parse_links(html, base_url)
    scored: List[Tuple[float, str, str]] = []
    seen: Set[str] = set()

    for href, text in links:
        if href in seen:
            continue
        if not allow_external and not same_domain(base_url, href):
            continue
        sc = _score_program_link(href, text)
        if sc < min_score:
            # Relaxed fallback: include links that match basic maternal keywords
            # even if the taxonomy score didn't fire.
            if min_score <= 0.1 and _basic_maternal_hit(href, text):
                sc = 0.2
            else:
                continue
        seen.add(href)
        scored.append((sc, href, text))

    scored.sort(reverse=True)
    results: List[Dict] = []
    for sc, href, text in scored[:max_links]:
        classification = classify_program(text, href)
        results.append({
            "name": text or "",
            "url": href,
            "link_text": text or "",
            "nav_path": f"search → {base_url}",
            "category": classification.category if classification else "Unknown",
            "relevance_score": round(sc, 2),
        })
    return results


def _maybe_add_seed_program(html: str, seed_url: str) -> Optional[Dict]:
    """
    If the "maternal section URL" is actually a program landing page (common for
    WIC/perinatal entry points), add the seed page itself as a discovered program.
    """
    seed_l = (seed_url or "").lower()
    if seed_l.endswith(".pdf") or "/.pdf" in seed_l or "pdf" in seed_l:
        return None
    try:
        soup = BeautifulSoup(html, "lxml")
    except Exception:
        soup = BeautifulSoup(html, "html.parser")

    # Extract a small text snippet for taxonomy matching.
    for el in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
        el.decompose()

    title = ""
    if soup.title and soup.title.get_text(strip=True):
        title = soup.title.get_text(strip=True)

    h1 = ""
    for tag in soup.find_all("h1"):
        t = tag.get_text(separator=" ", strip=True)
        if t:
            h1 = t
            break

    name = h1 or title or "Maternal Program"

    text = soup.get_text(separator=" ", strip=True)
    text = text[:8000]

    # If taxonomy classification fails, we still want to keep the seed as a
    # candidate program when we can tell it's maternal-content-like.
    classification = classify_program(text, seed_url)
    maternal_like = _basic_maternal_hit(seed_url, name) or _basic_maternal_hit(seed_url, text[:1500])
    if not classification and not maternal_like:
        return None

    rel = score_maternal_relevance(text, seed_url)
    return {
        "name": name,
        "url": seed_url,
        "link_text": name,
        "nav_path": f"seed → {seed_url}",
        "category": classification.category if classification else "Unknown",
        "relevance_score": round(2.0 + rel * 2.0, 2),
    }

# ─────────────────────────────────────────────────────────────────────────────
# Per-county discovery
# ─────────────────────────────────────────────────────────────────────────────

async def _discover_one(
    session: aiohttp.ClientSession,
    county_name: str,
    county_root_url: str,
    semaphore: asyncio.Semaphore,
    progress_cb: Callable[[str], None],
) -> Dict:
    result: Dict = {
        "county_name": county_name,
        "county_url": county_root_url,
        "health_dept_url": "",
        "maternal_section_url": "",
        "discovery_tier": "",
        "programs": [],
    }

    async with semaphore:

        mch_url: Optional[str] = None
        html: Optional[str] = None

        # ── Tier 1: validated URL — only commit if fetch succeeds ─────────────
        validated = MATERNAL_HEALTH_URLS.get(county_name)
        if validated:
            html = await _get(session, validated)
            if html:
                mch_url = validated
                result["maternal_section_url"] = mch_url
                result["discovery_tier"] = "tier1_validated"
            # If fetch failed (404/timeout), fall through to tier2 below

        # ── Tier 2: DuckDuckGo search for county MCH page ─────────────────────
        if not mch_url:
            loop = asyncio.get_event_loop()
            search_url = await loop.run_in_executor(
                None, _find_mch_url_via_search, county_name
            )
            if search_url:
                mch_url = search_url
                html = await _get(session, mch_url)
                result["maternal_section_url"] = mch_url
                result["discovery_tier"] = "tier2_search"

        # ── Tier 3: known health dept URL or county root ───────────────────────
        if not mch_url:
            mch_url = HEALTH_DEPT_URLS.get(county_name) or county_root_url
            html = await _get(session, mch_url)
            result["health_dept_url"] = mch_url
            result["discovery_tier"] = "tier3_fallback"

        # ── Extract program links ──────────────────────────────────────────────
        programs: List[Dict] = []
        if html:
            programs = _extract_program_links(html, mch_url)
            if not programs:
                # Relaxed pass: lower score threshold + allow basic maternal keywords.
                programs = _extract_program_links(
                    html,
                    mch_url,
                    min_score=0.1,
                    max_links=min(80, MAX_PROG_LINKS * 3),
                    allow_external=True,
                )
                result["discovery_tier"] = f"{result['discovery_tier']}_relaxed_extract"

            # If seed page itself looks like a program landing page, include it.
            if not programs:
                seed_prog = _maybe_add_seed_program(html, mch_url)
                if seed_prog:
                    programs = [seed_prog]
                    result["discovery_tier"] = f"{result['discovery_tier']}_seed_program"

        # ── Multi-seed fallback: runs regardless of whether primary fetch worked ─
        if not programs:
            loop = asyncio.get_event_loop()
            seed_candidates = await loop.run_in_executor(
                None, _find_mch_url_candidates_via_search, county_name
            )
            # Always append known health dept + county root as last resorts.
            seed_candidates.extend([
                HEALTH_DEPT_URLS.get(county_name) or county_root_url,
                county_root_url,
            ])
            # De-dupe while preserving order.
            uniq: List[str] = []
            seen_u: Set[str] = set()
            for s in seed_candidates:
                if not s or s in seen_u:
                    continue
                seen_u.add(s)
                uniq.append(s)
            # Try up to 4 additional seeds.
            for candidate_seed in uniq[:4]:
                if candidate_seed == mch_url:
                    continue
                cand_html = await _get(session, candidate_seed)
                if not cand_html:
                    continue
                programs = _extract_program_links(
                    cand_html,
                    candidate_seed,
                    min_score=0.1,
                    max_links=min(80, MAX_PROG_LINKS * 3),
                    allow_external=True,
                )
                if programs:
                    mch_url = candidate_seed
                    result["maternal_section_url"] = candidate_seed
                    result["discovery_tier"] = f"{result['discovery_tier']}_alt_seed"
                    break

        result["programs"] = programs

    n = len(result["programs"])
    tier = result["discovery_tier"]
    icon = "✓" if n > 0 else "○"
    progress_cb(f"→ Discovery: {county_name:<22} [{tier:<18}]  {n} program links")
    return result

# ─────────────────────────────────────────────────────────────────────────────
# Batch runner
# ─────────────────────────────────────────────────────────────────────────────

async def _run_all(county_names: List[str], concurrency: int) -> List[Dict]:
    semaphore = asyncio.Semaphore(concurrency)
    connector = aiohttp.TCPConnector(limit=concurrency * 2, ssl=False)
    printed: List[str] = []

    def progress_cb(msg: str):
        print(msg, flush=True)
        printed.append(msg)

    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [
            _discover_one(session, name, CALIFORNIA_COUNTIES[name], semaphore, progress_cb)
            for name in county_names
            if name in CALIFORNIA_COUNTIES
        ]
        raw = await asyncio.gather(*tasks, return_exceptions=True)

    results: List[Dict] = []
    for name, r in zip(county_names, raw):
        if isinstance(r, Exception):
            print(f"  ✗ {name}: {r}")
            results.append({
                "county_name": name, "county_url": "", "health_dept_url": "",
                "maternal_section_url": "", "discovery_tier": "error", "programs": [],
            })
        else:
            results.append(r)
    return results


def _print_summary(results: List[Dict]) -> None:
    tiers = Counter(r.get("discovery_tier", "?") for r in results)
    total = sum(len(r["programs"]) for r in results)
    zero = [r["county_name"] for r in results if not r["programs"]]

    print(f"\n{'─'*60}")
    print("Discovery summary:")
    for tier, count in sorted(tiers.items()):
        print(f"  {tier:<25}: {count} counties")
    print(f"\n  Total program links: {total}")
    print(f"  Counties with hits:  {len(results) - len(zero)}/{len(results)}")
    if zero:
        print(f"\n  Zero-result counties ({len(zero)}) — add manually to MATERNAL_HEALTH_URLS:")
        for name in zero:
            print(f"    {name}")

# ─────────────────────────────────────────────────────────────────────────────
# Public API — drop-in for run_pipeline.py
# ─────────────────────────────────────────────────────────────────────────────

def run_discovery_for_county(county_name: str, county_root_url: str) -> Dict:
    """Sync drop-in replacement for run_pipeline.py."""
    printed: List[str] = []

    async def _inner() -> Dict:
        connector = aiohttp.TCPConnector(ssl=False)
        sem = asyncio.Semaphore(1)
        async with aiohttp.ClientSession(connector=connector) as session:
            return await _discover_one(
                session, county_name, county_root_url, sem,
                progress_cb=lambda msg: printed.append(msg),
            )

    result = asyncio.run(_inner())
    for msg in printed:
        print(msg, flush=True)
    return result

# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Phase 1 Discovery — search-first")
    parser.add_argument("--county", nargs="*", help="Specific county names")
    parser.add_argument("--concurrency", type=int, default=CONCURRENCY,
                        help=f"Max concurrent tasks (default: {CONCURRENCY})")
    args = parser.parse_args()

    target = args.county if args.county else list(CALIFORNIA_COUNTIES.keys())

    print(f"\n{'='*60}")
    print(f"🔎 Phase 1 Discovery — search-first — {len(target)} counties")
    print(f"   Concurrency: {args.concurrency}")
    print(f"{'='*60}\n")

    results = asyncio.run(_run_all(target, args.concurrency))
    _print_summary(results)

    os.makedirs("data", exist_ok=True)
    out = os.path.join("data", "discovery_results.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(
            {"generated_at": datetime.now().isoformat(), "results": results},
            f, ensure_ascii=False, indent=2,
        )
    print(f"\n✓ Saved → {out}")


if __name__ == "__main__":
    main()