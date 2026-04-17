#!/usr/bin/env python3
"""
Phase 2 Enhanced — seed-URL crawl with sub-page discovery, PDF extraction,
and Playwright fallback for bot-blocked counties.

vs. scraper_extract.py
  scraper_extract.py  : iterates Phase 1 discovered links, fetches each one
  phase2_enhanced.py  : starts from a human-verified MCAH seed URL, crawls
                        2 levels deep (keyword-filtered links), also pulls PDFs

Key additions
  • Seed-first crawl   — starts from MATERNAL_HEALTH_URLS[county] landing page
  • Sub-page discovery — follows links 2 levels deep (MCAH keyword filter)
  • PDF extraction     — LangChain PyPDFLoader for PDF program documents (≤5/county)
  • Playwright path    — headless Chromium for the 10 counties in PLAYWRIGHT_REQUIRED_COUNTIES
  • Identical output   — writes data/raw/{county}/*.json in the same schema as
                         scraper_extract.py so Phase 3 needs no changes

USAGE
  # Standalone (replaces scraper_extract.py):
  python -m src.phase2_enhanced

  # Selective counties:
  python -m src.phase2_enhanced --counties "San Francisco,Sacramento,Los Angeles"

  # From run_pipeline.py:
  from src.phase2_enhanced import run_phase2_enhanced
  run_phase2_enhanced(discovery_results)   # seed-URL path + Phase 1 fallback

INSTALL
  pip install -r requirements-langchain.txt
  playwright install chromium              # one-time browser binary download
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
from collections import deque
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urljoin, urldefrag, urlparse

import aiohttp
from bs4 import BeautifulSoup

from src.config import (
    MAX_TEXT_CHARS,
    MATERNAL_HEALTH_URLS,
    PLAYWRIGHT_REQUIRED_COUNTIES,
)
from src.federal_program_registry import get_aliases_flat

# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

RAW_DIR       = os.path.join("data", "raw")
CONCURRENCY   = 6       # simultaneous aiohttp fetches
FETCH_TIMEOUT = 15      # seconds per request
MAX_DEPTH     = 2       # how many link hops from seed to follow
MAX_PAGES_PER_COUNTY = 30   # hard cap to prevent crawl explosion
MAX_PDFS_PER_COUNTY  = 5    # LangChain PDF loader cap per county
MIN_TEXT_CHARS = 200
MIN_SIGNAL_SCORE = 1

PHONE_RE = re.compile(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}')
EMAIL_RE = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')

BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

# Link URL path keywords that indicate a maternal/child health sub-page worth crawling
MCAH_URL_KEYWORDS = {
    "wic", "maternal", "prenatal", "perinatal", "mcah", "mch", "mcf",
    "home-visit", "home_visit", "home-visiting", "homevisit",
    "infant", "postpartum", "breastfeed", "lactation",
    "family-health", "family_health", "women-health", "women_health",
    "black-infant", "black_infant", "nurse-family", "nurse_family",
    "healthy-families", "healthy_families", "healthy-start", "healthy_start",
    "family-planning", "family_planning", "reproductive",
    "newborn", "pregnancy", "pregnant", "birth", "doula", "midwife",
    "obstetric", "ob-gyn", "title-v", "title_v", "miechv",
    "adolescent-family", "adolescent_family", "aflp", "cpsp",
    "perinatal-equity", "perinatal_equity",
    "childbirth", "childhealth", "child-health",
}

# URL segments that are definitely not program pages — skip before fetching
BAD_URL_SEGMENTS = {
    "login", "sign-in", "logout", "admin",
    "news", "press-release", "press_release", "blog", "announcement",
    "event", "calendar", "permit", "license", "fee-schedule",
    "job", "career", "employment", "bid", "rfp", "procurement",
    "agendas", "minutes", "meeting",
    "facebook", "twitter", "instagram", "youtube", "linkedin",
    "donate", "volunteer", "search",
}

# ─────────────────────────────────────────────────────────────────────────────
# Registry aliases (CA) — used for content quality gate
# ─────────────────────────────────────────────────────────────────────────────

_CA_ALIASES: Set[str] = set(get_aliases_flat("CA").keys())


# ─────────────────────────────────────────────────────────────────────────────
# HTML fetchers
# ─────────────────────────────────────────────────────────────────────────────

async def _fetch_aiohttp(session: aiohttp.ClientSession, url: str) -> Optional[str]:
    try:
        async with session.get(
            url,
            headers=BROWSER_HEADERS,
            timeout=aiohttp.ClientTimeout(total=FETCH_TIMEOUT),
            allow_redirects=True,
        ) as resp:
            if resp.status >= 400:
                return None
            return await resp.text(errors="replace")
    except Exception:
        return None


def _fetch_curl_cffi_sync(url: str) -> Optional[str]:
    """
    Chrome TLS-fingerprint impersonation via curl-cffi.

    curl-cffi spoofs the TLS ClientHello and HTTP/2 settings of a real Chrome
    browser at the socket level.  This bypasses Cloudflare and most anti-bot
    middleware that inspect TLS fingerprints (JA3/JA4), which plain aiohttp
    and even headless Playwright (without patches) fail.

    Returns raw HTML string, or None on any error.
    """
    try:
        from curl_cffi import requests as cffi_requests  # type: ignore
        resp = cffi_requests.get(
            url,
            impersonate="chrome124",
            timeout=FETCH_TIMEOUT,
            allow_redirects=True,
        )
        if resp.status_code >= 400:
            return None
        # Cloudflare managed challenge returns 200 with a JS interstitial —
        # detect it and treat as a failure so Playwright can try next.
        if "just a moment" in resp.text[:500].lower():
            return None
        return resp.text
    except Exception:
        return None


async def _fetch_curl_cffi(url: str) -> Optional[str]:
    """Async wrapper — runs the sync curl-cffi call in a thread pool."""
    import asyncio
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _fetch_curl_cffi_sync, url)


async def _fetch_playwright(url: str) -> Optional[str]:
    """
    Stealth headless Chromium fetch via Playwright.

    Patches applied:
      • --disable-blink-features=AutomationControlled  (removes navigator.webdriver)
      • navigator.webdriver overridden to undefined via init script
      • Realistic Accept-Language / platform headers injected

    Used as the second tier for bot-blocked counties when curl-cffi fails
    (e.g. sites that require JavaScript execution to render the DOM).
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("  [warn] playwright not installed — run: pip install playwright && playwright install chromium")
        return None
    try:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                ],
            )
            ctx = await browser.new_context(
                user_agent=BROWSER_HEADERS["User-Agent"],
                locale="en-US",
                extra_http_headers={
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept": BROWSER_HEADERS["Accept"],
                },
            )
            # Patch navigator.webdriver to undefined so JS bot-checks pass
            await ctx.add_init_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )
            page = await ctx.new_page()
            # "networkidle" gives Cloudflare JS challenges time to resolve
            try:
                await page.goto(url, wait_until="networkidle", timeout=FETCH_TIMEOUT * 2 * 1000)
            except Exception:
                # Fallback to domcontentloaded if networkidle times out
                await page.goto(url, wait_until="domcontentloaded", timeout=FETCH_TIMEOUT * 1000)
            html = await page.content()
            await browser.close()
            # Surface Cloudflare blocks clearly so the operator can act
            if "just a moment" in html[:500].lower():
                print(f"  [cloudflare] Playwright hit Cloudflare managed challenge — {url}")
                return None
            return html
    except Exception as exc:
        print(f"  [warn] Playwright fetch failed for {url}: {exc}")
        return None


async def fetch_html(
    county: str,
    url: str,
    session: aiohttp.ClientSession,
) -> Optional[str]:
    """
    Three-tier fetch for bot-blocked counties; plain aiohttp for all others.

    Tier 1 — curl-cffi  : Chrome TLS fingerprint spoofing (fast, no browser)
    Tier 2 — Playwright : stealth headless Chromium (handles JS-rendered pages)
    Tier 3 — aiohttp    : plain HTTP (last resort; will likely fail for blocked sites)
    """
    if county in PLAYWRIGHT_REQUIRED_COUNTIES:
        # Tier 1: curl-cffi (Chrome TLS impersonation)
        html = await _fetch_curl_cffi(url)
        if html:
            return html
        print(f"  [bot-block] curl-cffi failed for {county} — trying Playwright …")
        # Tier 2: Playwright with stealth patches
        html = await _fetch_playwright(url)
        if html:
            return html
        print(f"  [bot-block] Playwright failed for {county} — falling back to aiohttp …")
    # Tier 3 (or normal path): plain aiohttp
    return await _fetch_aiohttp(session, url)


# ─────────────────────────────────────────────────────────────────────────────
# HTML parsing helpers
# ─────────────────────────────────────────────────────────────────────────────

def _parse_html(html: str, base_url: str) -> Tuple[str, List[str], List[str], Dict]:
    """
    Returns (text, sub_links, pdf_links, contacts).
    sub_links  — absolute URLs of same-domain links that pass the keyword filter
    pdf_links  — absolute URLs of PDF files linked from the page
    contacts   — {phones: [...], emails: [...]}
    """
    soup = BeautifulSoup(html, "lxml")
    for el in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
        el.decompose()

    # Text
    text = soup.get_text(separator="\n", strip=True)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    if len(text) > MAX_TEXT_CHARS:
        text = text[:MAX_TEXT_CHARS] + "\n\n[truncated]"

    base_domain = urlparse(base_url).netloc

    sub_links: List[str] = []
    pdf_links: List[str] = []
    seen: Set[str] = set()

    for a in soup.find_all("a", href=True):
        href, _ = urldefrag(urljoin(base_url, a["href"]))
        if href in seen or not href.startswith("http"):
            continue
        seen.add(href)

        href_lower = href.lower()
        # Collect PDFs regardless of domain
        if href_lower.endswith(".pdf") or "/pdf" in href_lower:
            pdf_links.append(href)
            continue

        # Only follow same-domain links
        if urlparse(href).netloc != base_domain:
            continue

        path = urlparse(href).path.lower()
        path_parts = set(re.split(r'[/\-_.]', path))

        # Skip obvious non-program segments
        if path_parts & BAD_URL_SEGMENTS:
            continue

        # Accept if path contains an MCAH keyword
        if path_parts & MCAH_URL_KEYWORDS:
            sub_links.append(href)
            continue

        # Accept if link text mentions a registry alias
        link_text = a.get_text(strip=True).lower()
        if any(alias in link_text for alias in _CA_ALIASES):
            sub_links.append(href)

    contacts = {
        "phones": sorted(set(PHONE_RE.findall(text))),
        "emails": sorted(set(EMAIL_RE.findall(text))),
    }

    return text, sub_links, pdf_links[:20], contacts


# ─────────────────────────────────────────────────────────────────────────────
# Content quality gate (same logic as scraper_extract.py)
# ─────────────────────────────────────────────────────────────────────────────

def _score_content(text: str) -> Tuple[int, List[str]]:
    text_lower = text.lower()
    matched = [a for a in _CA_ALIASES if a in text_lower]
    indicators = [
        "eligibility", "how to apply", "to apply", "application",
        "services include", "program provides", "program offers",
        "to enroll", "enrollment",
        "pregnant", "prenatal", "postpartum", "infant", "newborn",
        "phone:", "hours:", "location:", "address:",
    ]
    bonus = 1 if sum(1 for i in indicators if i in text_lower) >= 3 else 0
    return len(matched) + bonus, matched


def _is_program_page(text: str) -> Tuple[bool, str]:
    if len(text) < MIN_TEXT_CHARS:
        return False, f"too short ({len(text)} chars)"
    score, matched = _score_content(text)
    if score < MIN_SIGNAL_SCORE:
        return False, f"no registry signal (score={score})"
    return True, f"score={score}, aliases={matched[:3]}"


def _fingerprint(text: str) -> str:
    cleaned = re.sub(r'\s+', ' ', text[:2000]).strip().lower()
    return hashlib.sha1(cleaned.encode()).hexdigest()


# ─────────────────────────────────────────────────────────────────────────────
# PDF extraction (LangChain)
# ─────────────────────────────────────────────────────────────────────────────

def _extract_pdf_text(pdf_url: str) -> Optional[str]:
    """
    Download and extract text from a PDF.
    Uses LangChain PyPDFLoader if available, falls back to pdfplumber, then skips.
    """
    try:
        from langchain_community.document_loaders import PyPDFLoader
        loader = PyPDFLoader(pdf_url)
        docs = loader.load()
        return "\n\n".join(d.page_content for d in docs)[:MAX_TEXT_CHARS]
    except Exception:
        pass

    try:
        import pdfplumber, urllib.request, tempfile
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            urllib.request.urlretrieve(pdf_url, tmp.name)  # noqa: S310
            with pdfplumber.open(tmp.name) as pdf:
                pages = [p.extract_text() or "" for p in pdf.pages[:20]]
            os.unlink(tmp.name)
            return "\n\n".join(pages)[:MAX_TEXT_CHARS]
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────────────────────
# File I/O (same as scraper_extract.py)
# ─────────────────────────────────────────────────────────────────────────────

def _slugify(text: str) -> str:
    s = re.sub(r'[^a-zA-Z0-9]+', '-', (text or "").strip().lower())
    s = re.sub(r'-{2,}', '-', s).strip('-')
    return s[:60] or "item"


def _page_hash(url: str) -> str:
    return hashlib.sha1(url.encode()).hexdigest()[:10]


def _save_raw(county: str, record: Dict) -> str:
    county_dir = os.path.join(RAW_DIR, _slugify(county))
    os.makedirs(county_dir, exist_ok=True)
    base = _slugify(record.get("program_name_guess") or record.get("link_text") or "program")
    fname = f"{base}-{_page_hash(record['page_url'])}.json"
    out_path = os.path.join(county_dir, fname)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=2)
    return out_path


def _make_record(
    county: str,
    url: str,
    text: str,
    contacts: Dict,
    pdf_links: List[str],
    matched_aliases: List[str],
    link_text: str = "",
    source_depth: int = 0,
) -> Dict:
    """Build the output record — schema identical to scraper_extract.py."""
    return {
        "county": county,
        "page_url": url,
        "link_text": link_text,
        "program_name_guess": "",
        "nav_path": "",
        "scraped_at": datetime.now().isoformat(),
        "registry_signals": matched_aliases[:10],
        "text": text,
        "contacts": contacts,
        "pdf_links": pdf_links,
        # Enhanced fields (ignored by Phase 3 — backward compatible)
        "source_depth": source_depth,
        "scraper_version": "phase2_enhanced",
    }


# ─────────────────────────────────────────────────────────────────────────────
# County crawler — BFS from seed, depth ≤ MAX_DEPTH
# ─────────────────────────────────────────────────────────────────────────────

async def _crawl_county(
    county: str,
    seed_url: str,
    session: aiohttp.ClientSession,
    semaphore: asyncio.Semaphore,
    seen_fingerprints: Set[str],
) -> List[str]:
    """
    BFS crawl starting from seed_url.
    Returns list of saved file paths.
    """
    saved_paths: List[str] = []
    visited_urls: Set[str] = set()
    all_pdf_links: List[str] = []

    # Queue entries: (url, depth, link_text)
    queue: deque[Tuple[str, int, str]] = deque([(seed_url, 0, "MCAH landing page")])

    while queue and len(saved_paths) < MAX_PAGES_PER_COUNTY:
        url, depth, link_text = queue.popleft()

        if url in visited_urls:
            continue
        visited_urls.add(url)

        async with semaphore:
            html = await fetch_html(county, url, session)

        if not html:
            print(f"   ○ fetch failed  (depth={depth}): {url[:80]}")
            continue

        text, sub_links, pdf_links, contacts = _parse_html(html, url)
        all_pdf_links.extend(pl for pl in pdf_links if pl not in set(all_pdf_links))

        # Content gate
        ok, reason = _is_program_page(text)
        if not ok:
            # Still enqueue sub-links from the seed even if the seed itself is thin
            if depth == 0:
                for link in sub_links:
                    if link not in visited_urls:
                        queue.append((link, depth + 1, ""))
            print(f"   ○ content gate ({reason})  (depth={depth}): {url[:80]}")
            continue

        # Dedup
        fp = _fingerprint(text)
        if fp in seen_fingerprints:
            print(f"   ○ duplicate  (depth={depth}): {url[:80]}")
            continue
        seen_fingerprints.add(fp)

        _, matched = _score_content(text)
        record = _make_record(county, url, text, contacts, pdf_links, matched,
                              link_text=link_text, source_depth=depth)
        path = _save_raw(county, record)
        saved_paths.append(path)
        print(f"   ✓ saved  (depth={depth}, {len(matched)} signals): {os.path.basename(path)}")

        # Enqueue sub-links up to MAX_DEPTH
        if depth < MAX_DEPTH:
            for link in sub_links:
                if link not in visited_urls:
                    queue.append((link, depth + 1, ""))

    # PDF extraction (cap at MAX_PDFS_PER_COUNTY)
    pdf_saved = 0
    for pdf_url in all_pdf_links[:MAX_PDFS_PER_COUNTY]:
        if pdf_saved >= MAX_PDFS_PER_COUNTY:
            break
        pdf_text = _extract_pdf_text(pdf_url)
        if not pdf_text:
            continue
        ok, reason = _is_program_page(pdf_text)
        if not ok:
            continue
        fp = _fingerprint(pdf_text)
        if fp in seen_fingerprints:
            continue
        seen_fingerprints.add(fp)
        _, matched = _score_content(pdf_text)
        record = _make_record(county, pdf_url, pdf_text, {"phones": [], "emails": []},
                              [], matched, link_text="PDF document", source_depth=99)
        path = _save_raw(county, record)
        saved_paths.append(path)
        pdf_saved += 1
        print(f"   ✓ saved PDF ({len(matched)} signals): {os.path.basename(path)}")

    return saved_paths


# ─────────────────────────────────────────────────────────────────────────────
# Batch runner — all counties
# ─────────────────────────────────────────────────────────────────────────────

async def _run_all_async(
    counties: List[str],
    discovery_results: Optional[List[Dict]] = None,
) -> None:
    """
    For each county:
      • If in MATERNAL_HEALTH_URLS → crawl from seed (enhanced path)
      • Else → fall back to Phase 1 discovery links (scraper_extract.py behaviour)
    """
    semaphore = asyncio.Semaphore(CONCURRENCY)
    connector = aiohttp.TCPConnector(limit=CONCURRENCY * 2, ssl=False)
    seen_fingerprints: Set[str] = set()

    # Build Phase 1 lookup for the fallback path
    phase1_by_county: Dict[str, List[Dict]] = {}
    if discovery_results:
        for entry in discovery_results:
            name = entry.get("county_name", "")
            if name:
                phase1_by_county[name] = entry.get("programs", [])

    total_saved = 0
    total_skipped = 0

    async with aiohttp.ClientSession(connector=connector) as session:
        for county in counties:
            seed = MATERNAL_HEALTH_URLS.get(county)
            print(f"\nCounty: {county}  {'[seed crawl]' if seed else '[phase1 fallback]'}")

            if seed:
                paths = await _crawl_county(county, seed, session, semaphore, seen_fingerprints)
                total_saved += len(paths)
                if not paths:
                    print(f"   ⚠  No pages saved for {county} (seed crawl yielded nothing)")
            else:
                # Phase 1 fallback — behaves identically to scraper_extract.py
                programs = phase1_by_county.get(county, [])
                if not programs:
                    print(f"   ⚠  No Phase 1 links for {county} and no seed URL — skipping")
                    continue
                for p in programs:
                    url = p.get("url", "")
                    if not url or not url.startswith("http"):
                        continue
                    async with semaphore:
                        html = await _fetch_aiohttp(session, url)
                    if not html:
                        total_skipped += 1
                        continue
                    text, _, pdf_links, contacts = _parse_html(html, url)
                    ok, _ = _is_program_page(text)
                    if not ok:
                        total_skipped += 1
                        continue
                    fp = _fingerprint(text)
                    if fp in seen_fingerprints:
                        total_skipped += 1
                        continue
                    seen_fingerprints.add(fp)
                    _, matched = _score_content(text)
                    record = _make_record(county, url, text, contacts, pdf_links, matched,
                                          link_text=p.get("link_text", ""), source_depth=0)
                    path = _save_raw(county, record)
                    total_saved += 1
                    print(f"   ✓ saved: {os.path.basename(path)}")

    print(f"\n{'─'*60}")
    print(f"Phase 2 Enhanced complete")
    print(f"  Pages saved:   {total_saved}")
    print(f"  Pages skipped: {total_skipped}")


# ─────────────────────────────────────────────────────────────────────────────
# Public API — called from run_pipeline.py
# ─────────────────────────────────────────────────────────────────────────────

def run_phase2_enhanced(
    discovery_results: Optional[List[Dict]] = None,
    counties: Optional[List[str]] = None,
) -> None:
    """
    Drop-in replacement for run_phase_2() in run_pipeline.py.

    Args:
        discovery_results : Phase 1 output (used as fallback for counties
                            without a seed URL in MATERNAL_HEALTH_URLS)
        counties          : subset of counties to process; defaults to all 58
    """
    if counties is None:
        counties = list(MATERNAL_HEALTH_URLS.keys())
    os.makedirs(RAW_DIR, exist_ok=True)
    print(f"\n{'='*60}")
    print("Phase 2 Enhanced — seed crawl + sub-pages + PDFs")
    print(f"  Counties: {len(counties)}")
    print(f"  Playwright required: {len(PLAYWRIGHT_REQUIRED_COUNTIES)} counties")
    print(f"{'='*60}")
    asyncio.run(_run_all_async(counties, discovery_results))


# ─────────────────────────────────────────────────────────────────────────────
# Single-URL shim — backward-compatible with scraper_extract.process_program_page
# ─────────────────────────────────────────────────────────────────────────────

_shim_fingerprints: Set[str] = set()


def process_program_page(county: str, program: Dict) -> Optional[str]:
    """
    Sync single-URL entry point — identical signature to scraper_extract.py.
    Allows run_pipeline.py to swap imports without other changes.
    """
    import requests as _requests

    url = program.get("url", "")
    link_text = program.get("link_text", "") or program.get("name", "")
    if not url or not url.startswith("http"):
        return None

    try:
        resp = _requests.get(url, headers=BROWSER_HEADERS, timeout=FETCH_TIMEOUT)
        resp.raise_for_status()
        html = resp.text
    except Exception:
        return None

    text, _, pdf_links, contacts = _parse_html(html, url)
    ok, _ = _is_program_page(text)
    if not ok:
        return None

    fp = _fingerprint(text)
    if fp in _shim_fingerprints:
        return None
    _shim_fingerprints.add(fp)

    _, matched = _score_content(text)
    record = _make_record(county, url, text, contacts, pdf_links, matched,
                          link_text=link_text, source_depth=0)
    return _save_raw(county, record)


# ─────────────────────────────────────────────────────────────────────────────
# CLI entry point
# ─────────────────────────────────────────────────────────────────────────────

def _parse_args():
    import argparse
    p = argparse.ArgumentParser(description="Phase 2 Enhanced scraper")
    p.add_argument(
        "--counties",
        type=str,
        default=None,
        help="Comma-separated county names to process (default: all 58)",
    )
    return p.parse_args()


def main():
    args = _parse_args()
    counties = None
    if args.counties:
        counties = [c.strip() for c in args.counties.split(",") if c.strip()]
        unknown = [c for c in counties if c not in MATERNAL_HEALTH_URLS]
        if unknown:
            print(f"Warning: unknown counties (no seed URL): {unknown}")
    run_phase2_enhanced(counties=counties)


if __name__ == "__main__":
    main()
