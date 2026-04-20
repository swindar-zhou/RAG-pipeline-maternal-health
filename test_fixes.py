#!/usr/bin/env python3
"""
Test CLI for the 4 Phase-1 failure cases.

Usage:
  python test_fixes.py --case 1                  # bot-blocked valid link
  python test_fixes.py --case 2                  # URL integrity check
  python test_fixes.py --case 3                  # PDF seed (Yuba)
  python test_fixes.py --case 4                  # manual HTML override (Glenn)
  python test_fixes.py --county "Contra Costa"   # single county end-to-end
  python test_fixes.py --all                     # run all 4 cases
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from typing import Set

# ── make sure src/ is importable when running from project root ───────────────
sys.path.insert(0, os.path.dirname(__file__))

import aiohttp

from src.config import (
    MANUAL_HTML_DIR,
    MATERNAL_HEALTH_URLS,
    PLAYWRIGHT_REQUIRED_COUNTIES,
)
from src.phase2_enhanced import (
    _crawl_county,
    _extract_pdf_text,
    _is_program_page,
    _parse_html,
    _score_content,
    fetch_html,
)

PASS = "  ✓"
FAIL = "  ✗"
INFO = "  ·"

# ─────────────────────────────────────────────────────────────────────────────
# Case 1 — bot-blocked valid link
# ─────────────────────────────────────────────────────────────────────────────

CASE1_COUNTIES = ["Contra Costa", "Kern", "Madera", "Mendocino", "Amador"]

async def test_case1(counties: list[str] | None = None) -> bool:
    print("\n=== Case 1: Bot-blocked valid links ===")
    print("Strategy: curl-cffi → Playwright → aiohttp, then score the returned HTML\n")

    targets = counties or CASE1_COUNTIES
    connector = aiohttp.TCPConnector(ssl=False)
    any_pass = False

    async with aiohttp.ClientSession(connector=connector) as session:
        for county in targets:
            url = MATERNAL_HEALTH_URLS.get(county)
            if not url:
                print(f"{FAIL} {county}: no seed URL configured")
                continue
            tier = "bot-blocked" if county in PLAYWRIGHT_REQUIRED_COUNTIES else "plain"
            print(f"{INFO} {county} [{tier}]  {url[:100]}")

            html = await fetch_html(county, url, session)
            if not html:
                print(f"{FAIL} {county}: all fetch tiers returned nothing")
                continue

            text, sub_links, _, _ = _parse_html(html, url)
            ok, reason = _is_program_page(text)
            score, matched = _score_content(text)
            snippet = text[:200].replace("\n", " ").strip()

            print(f"     chars={len(text)}  score={score}  sub_links={len(sub_links)}")
            print(f"     snippet: {snippet!r}")
            if matched:
                print(f"     aliases matched: {matched[:5]}")
            if ok:
                print(f"{PASS} {county}: page scored ({reason})")
                any_pass = True
            else:
                print(f"{FAIL} {county}: content gate failed — {reason}")
                if sub_links:
                    print(f"     {len(sub_links)} sub-links found — depth-1 crawl may recover")
                else:
                    print(f"     no sub-links found — check if nav elements strip too aggressively")

    return any_pass


# ─────────────────────────────────────────────────────────────────────────────
# Case 2 — URL integrity check
# ─────────────────────────────────────────────────────────────────────────────

async def test_case2() -> bool:
    print("\n=== Case 2: URL integrity (all 58 counties) ===")
    print("Checks: URL present, not truncated, returns HTTP < 400\n")

    connector = aiohttp.TCPConnector(ssl=False)
    failures: list[str] = []

    async with aiohttp.ClientSession(connector=connector) as session:
        for county, url in sorted(MATERNAL_HEALTH_URLS.items()):
            # Heuristic: a URL ending in a partial word is likely truncated
            last_seg = url.rstrip("/").split("/")[-1]
            suspicious = len(last_seg) > 3 and not any(
                c in last_seg for c in ("-", "_", ".", "?", "=")
            ) and last_seg.isalpha() and last_seg not in {
                "mcah", "mch", "wic", "nursing", "health", "programs", "services",
                "families", "children", "women", "program", "home", "birth",
            }

            try:
                async with session.head(
                    url,
                    headers={"User-Agent": "Mozilla/5.0"},
                    timeout=aiohttp.ClientTimeout(total=10),
                    allow_redirects=True,
                ) as resp:
                    status = resp.status
            except Exception as exc:
                status = f"ERR({exc.__class__.__name__})"

            warn = " ⚠ suspicious slug" if suspicious else ""
            ok = isinstance(status, int) and status < 400
            sym = PASS if ok else FAIL
            print(f"{sym} {county:20s}  HTTP {status}  {url[:90]}{warn}")
            if not ok:
                failures.append(county)

    if failures:
        print(f"\n{FAIL} {len(failures)} URL(s) unreachable: {', '.join(failures)}")
        return False
    print(f"\n{PASS} All URLs reachable")
    return True


# ─────────────────────────────────────────────────────────────────────────────
# Case 3 — PDF seed (Yuba)
# ─────────────────────────────────────────────────────────────────────────────

async def test_case3() -> bool:
    print("\n=== Case 3: PDF seed URL (Yuba) ===")
    url = MATERNAL_HEALTH_URLS.get("Yuba", "")
    print(f"{INFO} URL: {url}\n")

    if not url:
        print(f"{FAIL} Yuba has no seed URL")
        return False

    seed_lower = url.lower()
    is_pdf_seed = url.endswith(".pdf") or "getfile" in seed_lower
    print(f"{INFO} PDF seed detected: {is_pdf_seed}")

    if not is_pdf_seed:
        print(f"{FAIL} URL not recognised as a PDF seed — check detection heuristic")
        return False

    print(f"{INFO} Calling _extract_pdf_text ...")
    text = _extract_pdf_text(url)
    if not text:
        print(f"{FAIL} PDF extraction returned nothing (check pdfplumber / PyPDFLoader install)")
        return False

    ok, reason = _is_program_page(text)
    score, matched = _score_content(text)
    snippet = text[:300].replace("\n", " ").strip()
    print(f"{INFO} chars={len(text)}  score={score}  aliases={matched[:5]}")
    print(f"{INFO} snippet: {snippet!r}")

    if ok:
        print(f"{PASS} PDF scored ({reason})")
        return True
    else:
        print(f"{FAIL} PDF content gate failed — {reason}")
        print(f"     (content may be images-only or use non-alias terminology)")
        return False


# ─────────────────────────────────────────────────────────────────────────────
# Case 4 — manual HTML override (Glenn / Cloudflare)
# ─────────────────────────────────────────────────────────────────────────────

async def test_case4() -> bool:
    print("\n=== Case 4: Manual HTML override (Glenn / Cloudflare) ===")
    county = "Glenn"
    override_path = os.path.join(MANUAL_HTML_DIR, f"{county}.html")
    print(f"{INFO} Expected override file: {override_path}\n")

    if not os.path.exists(override_path):
        print(f"{FAIL} Override file not found.")
        print(f"     To fix: open the page in Chrome, File → Save As → Webpage Complete")
        print(f"     then save as: {override_path}")
        print(f"     URL: {MATERNAL_HEALTH_URLS.get(county, 'N/A')}")
        return False

    with open(override_path, encoding="utf-8", errors="replace") as fh:
        html = fh.read()

    print(f"{INFO} Loaded {len(html):,} bytes from override file")
    seed_url = MATERNAL_HEALTH_URLS.get(county, "https://example.com")
    text, sub_links, _, _ = _parse_html(html, seed_url)
    ok, reason = _is_program_page(text)
    score, matched = _score_content(text)
    snippet = text[:300].replace("\n", " ").strip()

    print(f"{INFO} chars={len(text)}  score={score}  sub_links={len(sub_links)}")
    print(f"{INFO} aliases: {matched[:5]}")
    print(f"{INFO} snippet: {snippet!r}")

    if ok:
        print(f"{PASS} Manual HTML scored ({reason})")
        return True
    else:
        print(f"{FAIL} Manual HTML content gate failed — {reason}")
        return False


# ─────────────────────────────────────────────────────────────────────────────
# Single-county end-to-end crawl
# ─────────────────────────────────────────────────────────────────────────────

async def test_county(county: str) -> bool:
    print(f"\n=== End-to-end crawl: {county} ===")
    url = MATERNAL_HEALTH_URLS.get(county)
    if not url:
        print(f"{FAIL} No seed URL for '{county}'")
        return False

    print(f"{INFO} Seed: {url}\n")
    semaphore = asyncio.Semaphore(3)
    connector = aiohttp.TCPConnector(ssl=False)
    seen: Set[str] = set()

    async with aiohttp.ClientSession(connector=connector) as session:
        paths = await _crawl_county(county, url, session, semaphore, seen)

    if paths:
        print(f"\n{PASS} Saved {len(paths)} file(s):")
        for p in paths:
            print(f"     {p}")
        return True
    else:
        print(f"\n{FAIL} No files saved for {county}")
        return False


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Test Phase-1 fixes for 4 failure cases")
    parser.add_argument("--case", type=int, choices=[1, 2, 3, 4],
                        help="Run a specific test case (1–4)")
    parser.add_argument("--county", type=str,
                        help="Run a full end-to-end crawl for a single county")
    parser.add_argument("--all", action="store_true",
                        help="Run all 4 test cases")
    args = parser.parse_args()

    if not (args.case or args.county or args.all):
        parser.print_help()
        sys.exit(0)

    results: dict[str, bool] = {}

    async def _run() -> None:
        if args.county:
            results["county"] = await test_county(args.county)
            return

        cases = [1, 2, 3, 4] if args.all else [args.case]
        for c in cases:
            if c == 1:
                results["case1"] = await test_case1()
            elif c == 2:
                results["case2"] = await test_case2()
            elif c == 3:
                results["case3"] = await test_case3()
            elif c == 4:
                results["case4"] = await test_case4()

    asyncio.run(_run())

    print("\n" + "=" * 60)
    for label, passed in results.items():
        sym = PASS if passed else FAIL
        print(f"{sym} {label}")
    print("=" * 60)
    sys.exit(0 if all(results.values()) else 1)


if __name__ == "__main__":
    main()
