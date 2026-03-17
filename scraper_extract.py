#!/usr/bin/env python3
"""
Phase 2 - Deep Content Extraction v2
======================================
Key improvements over v1:

  1. URL pre-filter    — reject clearly non-program URLs before fetching
  2. Content quality gate — reject pages with no registry signal after fetching
  3. Deduplication    — skip near-identical pages (same text fingerprint)
  4. Async fetching   — aiohttp concurrent fetches, ~10x faster than v1

INSTALL:  pip install aiohttp beautifulsoup4 lxml
USAGE:    python scraper_extract_v2.py
          (drop-in replacement; reads data/discovery_results.json,
           writes data/raw/{county}/*.json, same schema as v1)
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse

import aiohttp
from bs4 import BeautifulSoup

from src.config import MAX_TEXT_CHARS
from src.federal_program_registry import get_aliases_flat

# ─────────────────────────────────────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────────────────────────────────────

INPUT_PATH  = os.path.join("data", "discovery_results.json")
RAW_DIR     = os.path.join("data", "raw")
CONCURRENCY = 10          # simultaneous HTTP fetches
FETCH_TIMEOUT = 15        # seconds per request
MIN_TEXT_CHARS = 200      # pages shorter than this are nav/login pages → skip
MIN_SIGNAL_SCORE = 1      # minimum registry signal score to save a page

PHONE_RE = re.compile(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}')
EMAIL_RE = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

# ─────────────────────────────────────────────────────────────────────────────
# Registry signal set (CA) — used for URL pre-filter and content gate
# ─────────────────────────────────────────────────────────────────────────────

_CA_ALIASES: Set[str] = set(get_aliases_flat("CA").keys())

# URL path segments that are reliable indicators of program pages
_GOOD_URL_SEGMENTS = {
    "wic", "maternal", "prenatal", "perinatal", "mcah", "mch",
    "home-visit", "home_visit", "home-visiting", "infant", "postpartum",
    "breastfeed", "lactation", "family-health", "women-health",
    "black-infant", "nurse-family", "healthy-families", "healthy-start",
    "family-planning", "reproductive", "newborn", "pregnancy",
    "birth", "doula", "midwife", "obstetric", "ob-gyn", "prenatal-care",
    "title-v", "title_v", "miechv",
}

# URL path segments that reliably indicate non-program pages → skip before fetching
_BAD_URL_SEGMENTS = {
    "login", "staff-login", "sign-in", "logout", "admin",
    "news", "press-release", "press_release", "blog", "announcement",
    "event", "calendar", "permit", "license", "fee", "fee-schedule",
    "job", "career", "employment", "bid", "rfp", "procurement",
    "agendas", "minutes", "board", "meeting",
    "facebook", "twitter", "instagram", "youtube", "linkedin",
    "donate", "volunteer",
    "#",   # anchor-only links
}

# Link text that signals a nav/UI element rather than a program page
_BAD_LINK_TEXT_EXACT = {
    "skip to main content", "skip to content", "click here to learn more",
    "click here", "learn more", "read more", "find out more",
    "more information", "staff login", "login", "sign in",
    "back to top", "print this page", "share", "email this page",
    "home", "contact us", "sitemap", "accessibility",
}

# ─────────────────────────────────────────────────────────────────────────────
# Fix 1 — URL + link-text pre-filter (no network call needed)
# ─────────────────────────────────────────────────────────────────────────────

def url_is_worth_fetching(url: str, link_text: str) -> Tuple[bool, str]:
    """
    Returns (should_fetch, reason).
    Rejects obvious non-program URLs before making any HTTP request.
    """
    if not url or not url.startswith("http"):
        return False, "invalid url"

    path = urlparse(url).path.lower()
    text = (link_text or "").lower().strip()

    # Reject bad link text (nav elements, generic CTAs)
    if text in _BAD_LINK_TEXT_EXACT:
        return False, f"generic link text: '{text}'"
    if len(text) < 3:
        return False, "link text too short"

    # Reject bad URL path segments
    path_parts = set(re.split(r'[/\-_.]', path))
    bad_hits = path_parts & _BAD_URL_SEGMENTS
    if bad_hits:
        return False, f"bad url segment: {bad_hits}"

    # Accept if URL has a known good segment (high confidence)
    good_hits = path_parts & _GOOD_URL_SEGMENTS
    if good_hits:
        return True, f"good url segment: {good_hits}"

    # Accept if link text matches any registry alias
    if any(alias in text for alias in _CA_ALIASES):
        return True, f"registry alias in link text"

    # Accept if URL path contains any registry alias
    if any(alias.replace(" ", "-") in path or alias.replace(" ", "_") in path
           for alias in _CA_ALIASES):
        return True, "registry alias in url path"

    # Accept if link text is substantive (>4 words, likely a program name)
    if len(text.split()) >= 4:
        return True, "substantive link text"

    # Default: accept but flag as low confidence
    return True, "low confidence — no strong signal"


# ─────────────────────────────────────────────────────────────────────────────
# Fix 2 — Content quality gate (post-fetch)
# ─────────────────────────────────────────────────────────────────────────────

def score_page_content(text: str, url: str) -> Tuple[int, List[str]]:
    """
    Score page text against registry signals.
    Returns (score, matched_aliases).
    score >= MIN_SIGNAL_SCORE → save the page.
    """
    text_lower = text.lower()
    matched: List[str] = []

    for alias in _CA_ALIASES:
        if alias in text_lower:
            matched.append(alias)

    # Additional program-page signals beyond the alias set
    program_indicators = [
        "eligibility", "how to apply", "to apply", "application",
        "services include", "program provides", "program offers",
        "to enroll", "enrollment", "contact us", "call us",
        "phone:", "hours:", "location:", "address:",
        "pregnant", "prenatal", "postpartum", "infant", "newborn",
    ]
    indicator_hits = sum(1 for ind in program_indicators if ind in text_lower)

    score = len(matched) + (1 if indicator_hits >= 3 else 0)
    return score, matched


def content_is_program_page(text: str, url: str) -> Tuple[bool, str]:
    """
    Returns (is_program_page, reason).
    Filters out pages that passed the URL check but contain no useful content.
    """
    if len(text) < MIN_TEXT_CHARS:
        return False, f"page too short ({len(text)} chars) — likely nav/login page"

    score, matched = score_page_content(text, url)

    if score < MIN_SIGNAL_SCORE:
        return False, f"no registry signal found in content (score={score})"

    return True, f"score={score}, aliases={matched[:5]}"


# ─────────────────────────────────────────────────────────────────────────────
# Fix 3 — Deduplication via content fingerprint
# ─────────────────────────────────────────────────────────────────────────────

def content_fingerprint(text: str) -> str:
    """
    SHA1 of the first 2000 chars of cleaned text.
    Pages with matching fingerprints are near-duplicates.
    """
    cleaned = re.sub(r'\s+', ' ', text[:2000]).strip().lower()
    return hashlib.sha1(cleaned.encode()).hexdigest()


# ─────────────────────────────────────────────────────────────────────────────
# HTTP helpers (async)
# ─────────────────────────────────────────────────────────────────────────────

async def async_fetch(
    session: aiohttp.ClientSession, url: str
) -> Optional[str]:
    try:
        async with session.get(
            url, headers=HEADERS,
            timeout=aiohttp.ClientTimeout(total=FETCH_TIMEOUT),
            allow_redirects=True,
        ) as resp:
            if resp.status >= 400:
                return None
            return await resp.text(errors="replace")
    except Exception:
        return None


def parse_page(html: str, base_url: str) -> Tuple[str, List[str], Dict]:
    """Extract text, PDF links, and contacts from raw HTML."""
    soup = BeautifulSoup(html, "lxml")
    for el in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
        el.decompose()

    # Text
    text = soup.get_text(separator="\n", strip=True)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    if len(text) > MAX_TEXT_CHARS:
        text = text[:MAX_TEXT_CHARS] + "\n\n[Content truncated...]"

    # PDF links
    pdf_links: List[str] = []
    seen_pdfs: Set[str] = set()
    for a in soup.find_all("a", href=True):
        href = urljoin(base_url, a["href"])
        href_l = href.lower()
        if href_l.endswith(".pdf") or "pdf" in href_l:
            if href not in seen_pdfs:
                seen_pdfs.add(href)
                pdf_links.append(href)
    pdf_links = pdf_links[:20]

    # Contacts
    contacts = {
        "phones": sorted(set(PHONE_RE.findall(text))),
        "emails": sorted(set(EMAIL_RE.findall(text))),
    }

    return text, pdf_links, contacts


# ─────────────────────────────────────────────────────────────────────────────
# File helpers
# ─────────────────────────────────────────────────────────────────────────────

def slugify(text: str) -> str:
    s = re.sub(r'[^a-zA-Z0-9]+', '-', (text or "").strip().lower())
    s = re.sub(r'-{2,}', '-', s).strip('-')
    return s[:60] or "item"


def page_hash(url: str) -> str:
    return hashlib.sha1(url.encode()).hexdigest()[:10]


def save_raw(county: str, record: Dict) -> str:
    county_dir = os.path.join(RAW_DIR, slugify(county))
    os.makedirs(county_dir, exist_ok=True)
    base = slugify(record.get("program_name_guess") or record.get("link_text") or "program")
    fname = f"{base}-{page_hash(record['page_url'])}.json"
    out_path = os.path.join(county_dir, fname)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=2)
    return out_path


# ─────────────────────────────────────────────────────────────────────────────
# Core per-program processor (async)
# ─────────────────────────────────────────────────────────────────────────────

async def process_program_page(
    session: aiohttp.ClientSession,
    county: str,
    program: Dict,
    seen_fingerprints: Set[str],
    semaphore: asyncio.Semaphore,
) -> Tuple[Optional[str], str]:
    """
    Fetch, filter, deduplicate, and save one program page.
    Returns (saved_path_or_None, status_message).
    """
    url = program.get("url", "")
    link_text = program.get("link_text", "") or program.get("name", "")

    # Fix 1 — URL pre-filter
    worth_fetching, url_reason = url_is_worth_fetching(url, link_text)
    if not worth_fetching:
        return None, f"skipped (url filter): {url_reason}"

    async with semaphore:
        html = await async_fetch(session, url)

    if not html:
        return None, "skipped (fetch failed)"

    text, pdf_links, contacts = parse_page(html, url)

    # Fix 2 — Content quality gate
    is_program, content_reason = content_is_program_page(text, url)
    if not is_program:
        return None, f"skipped (content gate): {content_reason}"

    # Fix 3 — Deduplication
    fp = content_fingerprint(text)
    if fp in seen_fingerprints:
        return None, "skipped (duplicate content)"
    seen_fingerprints.add(fp)

    # Save
    _, matched_aliases = score_page_content(text, url)
    record = {
        "county": county,
        "page_url": url,
        "link_text": link_text,
        "program_name_guess": program.get("name", ""),
        "nav_path": program.get("nav_path", ""),
        "scraped_at": datetime.now().isoformat(),
        "registry_signals": matched_aliases[:10],   # NEW: which aliases matched
        "text": text,
        "contacts": contacts,
        "pdf_links": pdf_links,
    }
    out_path = save_raw(county, record)
    return out_path, f"saved ({len(matched_aliases)} registry signals: {matched_aliases[:3]})"


# ─────────────────────────────────────────────────────────────────────────────
# Batch runner
# ─────────────────────────────────────────────────────────────────────────────

async def run_extraction_async(discovery_results: List[Dict]) -> None:
    semaphore = asyncio.Semaphore(CONCURRENCY)
    connector = aiohttp.TCPConnector(limit=CONCURRENCY * 2, ssl=False)

    # Track content fingerprints globally to deduplicate across counties
    seen_fingerprints: Set[str] = set()

    # Counters
    total_saved = 0
    total_skipped_url = 0
    total_skipped_content = 0
    total_skipped_dupe = 0
    total_fetch_failed = 0

    async with aiohttp.ClientSession(connector=connector) as session:
        for entry in discovery_results:
            county = entry.get("county_name", "")
            programs = entry.get("programs", [])
            if not programs:
                continue

            print(f"County: {county} — {len(programs)} candidate pages")

            tasks = [
                process_program_page(session, county, p, seen_fingerprints, semaphore)
                for p in programs
            ]
            results = await asyncio.gather(*tasks)

            county_saved = 0
            for out_path, status in results:
                if out_path:
                    county_saved += 1
                    total_saved += 1
                    print(f"   ✓ {os.path.basename(out_path)}  [{status}]")
                else:
                    # Bucket the skip reason for summary stats
                    if "url filter" in status:
                        total_skipped_url += 1
                    elif "content gate" in status:
                        total_skipped_content += 1
                    elif "duplicate" in status:
                        total_skipped_dupe += 1
                    elif "fetch failed" in status:
                        total_fetch_failed += 1
                    print(f"   ○ {status}")

            if county_saved == 0 and programs:
                print(f"   ⚠  No pages saved for {county}")

    print(f"\n{'─'*60}")
    print(f"Phase 2 complete")
    print(f"  Saved:              {total_saved}")
    print(f"  Skipped (url):      {total_skipped_url}  ← bad link text / non-program URL")
    print(f"  Skipped (content):  {total_skipped_content}  ← fetched but no registry signal")
    print(f"  Skipped (dupe):     {total_skipped_dupe}  ← near-identical to already-saved page")
    print(f"  Fetch failed:       {total_fetch_failed}  ← timeout / 4xx / network error")


# ─────────────────────────────────────────────────────────────────────────────
# Sync wrapper — drop-in replacement for v1's process_program_page()
# ─────────────────────────────────────────────────────────────────────────────

# Module-level fingerprint set so deduplication works across calls
# when run_pipeline.py calls process_program_page() in a loop
_global_fingerprints: Set[str] = set()

def process_program_page_sync(county: str, program: Dict) -> Optional[str]:
    """
    Sync drop-in for run_pipeline.py.
    Applies all 4 fixes but runs one URL at a time.
    Import this as `process_program_page` in run_pipeline.py.
    """
    import requests as _requests

    url = program.get("url", "")
    link_text = program.get("link_text", "") or program.get("name", "")

    # Fix 1 — URL pre-filter
    worth_fetching, reason = url_is_worth_fetching(url, link_text)
    if not worth_fetching:
        return None

    headers = HEADERS.copy()
    try:
        resp = _requests.get(url, headers=headers, timeout=FETCH_TIMEOUT)
        resp.raise_for_status()
        html = resp.text
    except Exception:
        return None

    text, pdf_links, contacts = parse_page(html, url)

    # Fix 2 — Content quality gate
    is_program, _ = content_is_program_page(text, url)
    if not is_program:
        return None

    # Fix 3 — Deduplication
    fp = content_fingerprint(text)
    if fp in _global_fingerprints:
        return None
    _global_fingerprints.add(fp)

    _, matched_aliases = score_page_content(text, url)
    record = {
        "county": county,
        "page_url": url,
        "link_text": link_text,
        "program_name_guess": program.get("name", ""),
        "nav_path": program.get("nav_path", ""),
        "scraped_at": datetime.now().isoformat(),
        "registry_signals": matched_aliases[:10],
        "text": text,
        "contacts": contacts,
        "pdf_links": pdf_links,
    }
    return save_raw(county, record)


# alias for run_pipeline.py import compatibility
process_program_page = process_program_page_sync


# ─────────────────────────────────────────────────────────────────────────────
# Main — async fast path
# ─────────────────────────────────────────────────────────────────────────────

def main():
    if not os.path.exists(INPUT_PATH):
        print(f"❌ {INPUT_PATH} not found. Run Phase 1 first.")
        return

    with open(INPUT_PATH, encoding="utf-8") as f:
        data = json.load(f)
    discovery_results = data.get("results", [])

    os.makedirs(RAW_DIR, exist_ok=True)

    print(f"\n{'='*60}")
    print("🕸️  Phase 2 - Deep Content Extraction v2")
    print(f"{'='*60}\n")

    asyncio.run(run_extraction_async(discovery_results))


if __name__ == "__main__":
    main()