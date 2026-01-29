#!/usr/bin/env python3
"""
Phase 1 - Discovery Scraper (Pilot: 5 Counties)

Finds Health Department pages → Maternal/Child Health sections → candidate
program links for maternal health using heuristic scoring. Persists results
to data/discovery_results.json without calling any LLMs.
"""

import os
import re
import json
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin, urlparse
from typing import List, Dict, Optional, Tuple

# Import shared configuration
from src.config import (
    CALIFORNIA_COUNTIES,
    HEALTH_DEPT_URLS,
    REQUEST_TIMEOUT,
    DELAY_BETWEEN_REQUESTS,
    DEPT_KEYWORDS,
    SECTION_KEYWORDS,
    PROGRAM_KEYWORDS,
)

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

PILOT_COUNTIES = ["San Diego", "Alameda", "Fresno", "Sacramento", "Kern"]

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

def fetch_soup(url: str) -> Optional[BeautifulSoup]:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }
    try:
        resp = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.content, "lxml")
        for el in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
            el.decompose()
        return soup
    except Exception:
        return None

def normalize_url(base_url: str, href: str) -> str:
    try:
        return urljoin(base_url, href)
    except Exception:
        return href

def extract_links(soup: BeautifulSoup, base_url: str) -> List[Tuple[str, str]]:
    links: List[Tuple[str, str]] = []
    for a in soup.find_all("a", href=True):
        href = normalize_url(base_url, a["href"])
        text = a.get_text(strip=True)
        links.append((href, text))
    return links

def is_same_domain(base_url: str, candidate_url: str) -> bool:
    try:
        b = urlparse(base_url)
        c = urlparse(candidate_url)
        return (c.netloc == b.netloc) or (c.netloc.endswith("." + b.netloc))
    except Exception:
        return False

def score_link(href: str, text: str, level: str) -> int:
    value = 0
    t = (text or "").lower()
    h = (href or "").lower()
    def contains_any(words: List[str]) -> bool:
        return any(w in t or w in h for w in words)
    if level == "dept":
        if contains_any(DEPT_KEYWORDS):
            value += 3
        if "/health" in h or "/public-health" in h:
            value += 2
    elif level == "section":
        if contains_any(SECTION_KEYWORDS):
            value += 3
        if any(seg in h for seg in ["/mch", "/mcah", "/maternal", "/perinatal", "/family-health"]):
            value += 2
    elif level == "program":
        if contains_any(PROGRAM_KEYWORDS):
            value += 2
        if any(seg in h for seg in ["/apply", "/program", "/services", "/maternal", "/perinatal"]):
            value += 1
    if any(d in h for d in ["facebook.com", "twitter.com", "instagram.com", "youtube.com", "linkedin.com"]):
        value -= 3
    return value

def choose_best_link(links: List[Tuple[str, str]], base_url: str, level: str) -> Optional[str]:
    best = None
    best_score = -999
    for href, text in links:
        if not href.startswith("http"):
            continue
        if not is_same_domain(base_url, href):
            continue
        sc = score_link(href, text, level)
        if sc > best_score:
            best_score = sc
            best = href
    return best

def find_health_dept_page(county_root_url: str) -> Optional[str]:
    soup = fetch_soup(county_root_url)
    if not soup:
        return None
    links = extract_links(soup, county_root_url)
    return choose_best_link(links, county_root_url, "dept")

def find_maternal_section(health_dept_url: str) -> Optional[str]:
    soup = fetch_soup(health_dept_url)
    if not soup:
        return None
    links = extract_links(soup, health_dept_url)
    return choose_best_link(links, health_dept_url, "section")

def collect_program_links(seed_url: str, max_links: int = 25) -> List[Dict[str, str]]:
    soup = fetch_soup(seed_url)
    if not soup:
        return []
    links = extract_links(soup, seed_url)
    scored: List[Tuple[int, str, str]] = []
    for href, text in links:
        if not href.startswith("http"):
            continue
        sc = score_link(href, text, "program")
        if sc <= 0:
            continue
        scored.append((sc, href, text))
    scored.sort(key=lambda t: t[0], reverse=True)
    seen = set()
    programs: List[Dict[str, str]] = []
    for _, href, text in scored:
        if href in seen:
            continue
        seen.add(href)
        programs.append({
            "name": text or "",
            "url": href,
            "link_text": text or "",
            "nav_path": ""
        })
        if len(programs) >= max_links:
            break
    return programs

# -----------------------------------------------------------------------------
# Workflow
# -----------------------------------------------------------------------------

def run_discovery_for_county(county_name: str, county_root_url: str) -> Dict:
    print(f"→ Discovery: {county_name}")
    result: Dict = {
        "county_name": county_name,
        "county_url": county_root_url,
        "health_dept_url": "",
        "maternal_section_url": "",
        "programs": []
    }
    # Check if we have a known health department URL first
    known_dept_url = HEALTH_DEPT_URLS.get(county_name)
    if known_dept_url:
        print(f"   ✓ Using known health department URL: {known_dept_url}")
        result["health_dept_url"] = known_dept_url
        dept = known_dept_url
    else:
        dept = find_health_dept_page(county_root_url)
        if dept:
            result["health_dept_url"] = dept
        else:
            print("   ⚠ Health department page not found; continuing from root")
            dept = county_root_url
    time.sleep(1)
    mch = find_maternal_section(dept)
    if mch:
        result["maternal_section_url"] = mch
    else:
        print("   ⚠ Maternal section not found; using health department page")
        mch = dept
    time.sleep(1)
    programs = collect_program_links(mch)
    for p in programs:
        p["nav_path"] = "Main → Health Dept → Maternal/Child" if result["maternal_section_url"] else "Main → Health Dept"
    result["programs"] = programs
    print(f"   ✓ Found {len(programs)} candidate program links")
    return result

def run_discovery_pilot() -> None:
    os.makedirs("data", exist_ok=True)
    results: List[Dict] = []
    for name in PILOT_COUNTIES:
        base = CALIFORNIA_COUNTIES.get(name)
        if not base:
            print(f"   ⚠ County not found in mapping: {name}")
            continue
        try:
            res = run_discovery_for_county(name, base)
            results.append(res)
        except Exception as e:
            print(f"   ✗ Discovery error for {name}: {e}")
        time.sleep(DELAY_BETWEEN_REQUESTS)
    out_path = os.path.join("data", "discovery_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"generated_at": datetime.now().isoformat(), "results": results}, f, ensure_ascii=False, indent=2)
    print(f"\n✓ Discovery results saved to {out_path}")

def main():
    print("\n" + "="*60)
    print("🔎 Phase 1 - Discovery (Pilot: 5 Counties)")
    print("="*60 + "\n")
    run_discovery_pilot()

if __name__ == "__main__":
    main()


