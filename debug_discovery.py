#!/usr/bin/env python3
"""
Debug script to examine why some counties find 0 programs even with known health dept URLs.
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from typing import List, Tuple
from src.config import HEALTH_DEPT_URLS, PROGRAM_KEYWORDS, SECTION_KEYWORDS

def fetch_soup(url: str):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    try:
        resp = requests.get(url, headers=headers, timeout=20)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.content, "lxml")
        for el in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
            el.decompose()
        return soup
    except Exception as e:
        print(f"   ✗ Error fetching {url}: {e}")
        return None

def extract_links(soup: BeautifulSoup, base_url: str) -> List[Tuple[str, str]]:
    links = []
    for a in soup.find_all("a", href=True):
        href = urljoin(base_url, a["href"])
        text = a.get_text(strip=True)
        links.append((href, text))
    return links

def score_link(href: str, text: str, level: str) -> int:
    value = 0
    t = (text or "").lower()
    h = (href or "").lower()
    
    def contains_any(words: List[str]) -> bool:
        return any(w in t or w in h for w in words)
    
    if level == "program":
        if contains_any(PROGRAM_KEYWORDS):
            value += 2
        if any(seg in h for seg in ["/apply", "/program", "/services", "/maternal", "/perinatal"]):
            value += 1
    elif level == "section":
        if contains_any(SECTION_KEYWORDS):
            value += 3
        if any(seg in h for seg in ["/mch", "/mcah", "/maternal", "/perinatal", "/family-health"]):
            value += 2
    
    if any(d in h for d in ["facebook.com", "twitter.com", "instagram.com", "youtube.com", "linkedin.com"]):
        value -= 3
    return value

def analyze_county(county_name: str, health_dept_url: str):
    print(f"\n{'='*80}")
    print(f"Analyzing: {county_name}")
    print(f"Health Dept URL: {health_dept_url}")
    print(f"{'='*80}")
    
    soup = fetch_soup(health_dept_url)
    if not soup:
        print("   ✗ Could not fetch page")
        return
    
    # Get page title and some text
    title = soup.find("title")
    title_text = title.get_text(strip=True) if title else "No title"
    print(f"\nPage Title: {title_text}")
    
    # Extract all links
    links = extract_links(soup, health_dept_url)
    print(f"\nTotal links found: {len(links)}")
    
    # Check for maternal section links
    print("\n--- Maternal Section Links (top 10 by score) ---")
    maternal_links = []
    for href, text in links:
        if not href.startswith("http"):
            continue
        score = score_link(href, text, "section")
        if score > 0:
            maternal_links.append((score, href, text))
    
    maternal_links.sort(key=lambda x: x[0], reverse=True)
    for score, href, text in maternal_links[:10]:
        print(f"  [{score}] {text[:60]:<60} -> {href[:80]}")
    
    if not maternal_links:
        print("  (none found)")
    
    # Check for program links
    print("\n--- Program Links (top 20 by score) ---")
    program_links = []
    for href, text in links:
        if not href.startswith("http"):
            continue
        score = score_link(href, text, "program")
        if score > 0:
            program_links.append((score, href, text))
    
    program_links.sort(key=lambda x: x[0], reverse=True)
    for score, href, text in program_links[:20]:
        print(f"  [{score}] {text[:60]:<60} -> {href[:80]}")
    
    if not program_links:
        print("  (none found)")
        print("\n--- All Links (first 30, for debugging) ---")
        for i, (href, text) in enumerate(links[:30]):
            if href.startswith("http"):
                print(f"  [{i+1}] {text[:60]:<60} -> {href[:80]}")
    
    # Check page content for keywords
    page_text = soup.get_text(separator=" ", strip=True).lower()
    print(f"\n--- Keyword Analysis ---")
    found_program_keywords = [kw for kw in PROGRAM_KEYWORDS if kw in page_text]
    found_section_keywords = [kw for kw in SECTION_KEYWORDS if kw in page_text]
    
    print(f"Program keywords found in page text: {len(found_program_keywords)}/{len(PROGRAM_KEYWORDS)}")
    if found_program_keywords:
        print(f"  Found: {', '.join(found_program_keywords[:10])}")
    
    print(f"Section keywords found in page text: {len(found_section_keywords)}/{len(SECTION_KEYWORDS)}")
    if found_section_keywords:
        print(f"  Found: {', '.join(found_section_keywords[:10])}")

def main():
    print("\n" + "="*80)
    print("🔍 Discovery Debug Tool")
    print("="*80)
    print("\nAnalyzing counties with known health dept URLs but 0 programs found:")
    print("  - Alameda")
    print("  - Orange")
    print("  - Santa Clara")
    print("  - Contra Costa")
    
    counties_to_check = [
        ("Alameda", HEALTH_DEPT_URLS["Alameda"]),
        ("Orange", HEALTH_DEPT_URLS["Orange"]),
        ("Santa Clara", HEALTH_DEPT_URLS["Santa Clara"]),
        ("Contra Costa", HEALTH_DEPT_URLS["Contra Costa"]),
    ]
    
    for county_name, url in counties_to_check:
        analyze_county(county_name, url)
    
    print("\n" + "="*80)
    print("✓ Analysis complete")
    print("="*80)

if __name__ == "__main__":
    main()
