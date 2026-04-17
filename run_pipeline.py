#!/usr/bin/env python3
"""
Run the 3-phase pipeline (Discovery → Extraction → Structuring) for a
selected set of California counties.

Default counties (10, excluding San Diego which you already ran):
  Alameda, Fresno, Sacramento, Kern, Los Angeles, San Francisco,
  Orange, Riverside, Santa Clara, Contra Costa
"""

import os
import json
import time
from typing import List, Dict
from datetime import datetime

# Import shared config
from src.config import CALIFORNIA_COUNTIES

# Phase 1 helpers
from scraper_discovery import (
    run_discovery_for_county,
)

# Phase 2 helpers — prefer the enhanced seed-crawl engine; fall back to basic extractor
try:
    from src.phase2_enhanced import run_phase2_enhanced as _run_phase2_enhanced
    _ENHANCED_AVAILABLE = True
except ImportError:
    _ENHANCED_AVAILABLE = False

from scraper_extract import (
    process_program_page,
)

# Phase 3 helpers
from scraper_structure import main as run_structure_main

# Phase 4 helpers — vectorstore build (optional, requires requirements-langchain.txt)
try:
    from src.vector_store import build_all_vectorstores as _build_vectorstores
    _VECTORSTORE_AVAILABLE = True
except ImportError:
    _VECTORSTORE_AVAILABLE = False

from eval.gap_detector import run_gap_analysis_from_pipeline_output

DATA_DIR = "data"
DISCOVERY_PATH = os.path.join(DATA_DIR, "discovery_results.json")
RAW_DIR = os.path.join(DATA_DIR, "raw")

TARGET_COUNTIES = list(CALIFORNIA_COUNTIES.keys())  # all 58 CA counties

def run_phase_1(county_names: List[str]) -> List[Dict]:
    print("\n=== Phase 1: Discovery ===")
    os.makedirs(DATA_DIR, exist_ok=True)
    results: List[Dict] = []
    for name in county_names:
        base = CALIFORNIA_COUNTIES.get(name)
        if not base:
            print(f"   ⚠ County not found in mapping: {name}")
            continue
        res = run_discovery_for_county(name, base)
        results.append(res)
        time.sleep(1)
    with open(DISCOVERY_PATH, "w", encoding="utf-8") as f:
        json.dump({"generated_at": datetime.now().isoformat(), "results": results}, f, ensure_ascii=False, indent=2)
    print(f"✓ Discovery saved: {DISCOVERY_PATH} ({len(results)} counties)")
    return results

def run_phase_2(discovery_results: List[Dict]) -> None:
    print("\n=== Phase 2: Deep Extraction ===")
    os.makedirs(RAW_DIR, exist_ok=True)

    if _ENHANCED_AVAILABLE:
        # Seed-crawl path: starts from MATERNAL_HEALTH_URLS, crawls 2 levels deep,
        # also extracts PDFs, uses Playwright for bot-blocked counties.
        # Passes discovery_results as fallback for counties without a seed URL.
        _run_phase2_enhanced(discovery_results=discovery_results)
        return

    # Basic fallback (scraper_extract.py) — used if requirements-langchain.txt not installed
    print("  (enhanced scraper not available — using basic scraper_extract)")
    total = 0
    for entry in discovery_results:
        county = entry.get("county_name", "")
        programs = entry.get("programs", [])
        print(f"County: {county} — {len(programs)} pages")
        for p in programs:
            try:
                out_path = process_program_page(county, p)
                if out_path:
                    print(f"   ✓ Saved raw: {out_path}")
                    total += 1
                else:
                    print("   ⚠ Skipped (fetch failed)")
            except Exception as e:
                print(f"   ✗ Error: {e}")
            time.sleep(0.5)
    print(f"✓ Phase 2 complete. Raw pages saved: {total}")

def run_phase_3(discovery_results: List[Dict]) -> None:
    print("\n=== Phase 3: LLM Structuring ===")
    run_structure_main()


def run_phase_4(counties: List[str]) -> None:
    """Build per-county ChromaDB vectorstores from Phase 2 raw data."""
    print("\n=== Phase 4: Vectorstore Build ===")
    if not _VECTORSTORE_AVAILABLE:
        print("  Skipped — install requirements-langchain.txt to enable vectorstore build.")
        return
    _build_vectorstores(counties=counties)


def main():
    print("\n" + "="*60)
    print(f"🚀 Run Pipeline for {len(TARGET_COUNTIES)} Counties")
    print("="*60)
    print("Counties:", ", ".join(TARGET_COUNTIES))
    results = run_phase_1(TARGET_COUNTIES)
    run_phase_2(results)
    run_phase_3(results)
    run_phase_4(TARGET_COUNTIES)

    print("\n=== Gap Analysis ===")
    run_gap_analysis_from_pipeline_output(
        structured_csv_dir=os.path.join("data", "structured"),
        raw_json_dir=RAW_DIR,
        state_code="CA",
        output_dir=os.path.join("data", "gap_analysis"),
    )
    print("\nDone.")

if __name__ == "__main__":
    main()


