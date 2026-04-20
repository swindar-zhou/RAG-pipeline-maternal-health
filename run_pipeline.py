#!/usr/bin/env python3
"""
iTREDS California Maternal Health — 3-Phase Pipeline
=====================================================

Now that all 58 MCAH seed URLs are human-verified and baked into
src/config.py (MATERNAL_HEALTH_URLS), URL discovery via DuckDuckGo is no
longer a pipeline step.  The three phases are:

  Phase 1 — Crawl
      BFS crawl from each county's verified seed URL (depth ≤ 2, up to 30
      pages/county).  Playwright is used automatically for the 10 counties
      that block aiohttp.  PDFs are extracted (≤ 5/county).
      Output: data/raw/{county}/*.json

  Phase 2 — Structure
      Concurrent LLM (GPT-4o) calls turn raw pages into structured program
      records, grounded against the federal program registry for reliable
      program_id assignment and gap analysis.
      Output: data/structured/v{N}/California_County_Healthcare_Data.csv

  Phase 3 — Index
      Per-county ChromaDB vectorstores are built from the raw pages so the
      LangGraph ZIP → county → programs agent can answer user queries over
      semantic search.
      Output: data/vectorstore/{county}/

After all three phases, a gap analysis report is written to
data/gap_analysis/.

USAGE
  python run_pipeline.py                          # all 58 CA counties
  python run_pipeline.py --counties "Fresno,Kern" # subset
  python run_pipeline.py --phase 1                # single phase
  python run_pipeline.py --skip-index             # skip Phase 3

Adding a new county (not in MATERNAL_HEALTH_URLS):
  Use scraper_discovery.py as a standalone utility to find its MCAH URL,
  then add the entry to src/config.py before running the pipeline.
"""

import argparse
import os
import time
import json
from typing import List
from datetime import datetime

from src.config import CALIFORNIA_COUNTIES, MATERNAL_HEALTH_URLS

# ── Phase 1: Crawl ────────────────────────────────────────────────────────────
from src.phase2_enhanced import run_phase2_enhanced

# ── Phase 2: Structure ────────────────────────────────────────────────────────
from scraper_structure import main as run_structure_main

# ── Phase 3: Index (optional — requires requirements-langchain.txt) ───────────
try:
    from src.vector_store import build_all_vectorstores as _build_vectorstores
    _VECTORSTORE_AVAILABLE = True
except ImportError:
    _VECTORSTORE_AVAILABLE = False

# ── Gap analysis ──────────────────────────────────────────────────────────────
from eval.gap_detector import run_gap_analysis_from_pipeline_output

# ─────────────────────────────────────────────────────────────────────────────
DATA_DIR   = "data"
RAW_DIR    = os.path.join(DATA_DIR, "raw")

# Default: all counties that have a verified seed URL.
# Counties not yet in MATERNAL_HEALTH_URLS won't be crawled; run
# scraper_discovery.py for those and add the URL to src/config.py first.
TARGET_COUNTIES = list(MATERNAL_HEALTH_URLS.keys())


# ─────────────────────────────────────────────────────────────────────────────
# Phase 1 — Crawl
# ─────────────────────────────────────────────────────────────────────────────

def run_phase_1(counties: List[str]) -> None:
    """
    BFS-crawl each county's verified seed URL (MATERNAL_HEALTH_URLS).
    Playwright is used automatically for bot-blocked counties.
    Writes raw JSON pages to data/raw/{county}/.
    """
    print("\n=== Phase 1: Crawl ===")
    os.makedirs(RAW_DIR, exist_ok=True)
    run_phase2_enhanced(
        discovery_results=None,  # no Phase 0 discovery needed
        counties=counties,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Phase 2 — Structure
# ─────────────────────────────────────────────────────────────────────────────

def run_phase_2() -> None:
    """
    LLM-structure all raw pages in data/raw/.
    County URLs come from MATERNAL_HEALTH_URLS (via scraper_structure._load_discovery)
    so the LLM prompt always has a valid COUNTY WEBSITE value even when
    scraper_discovery.py was not run.
    """
    print("\n=== Phase 2: Structure ===")
    run_structure_main()


# ─────────────────────────────────────────────────────────────────────────────
# Phase 3 — Index
# ─────────────────────────────────────────────────────────────────────────────

def run_phase_3(counties: List[str]) -> None:
    """
    Build per-county ChromaDB vectorstores from Phase 1 raw data.
    Requires: pip install -r requirements-langchain.txt
    """
    print("\n=== Phase 3: Index ===")
    if not _VECTORSTORE_AVAILABLE:
        print("  Skipped — install requirements-langchain.txt to enable vectorstore build.")
        return
    _build_vectorstores(counties=counties)


# ─────────────────────────────────────────────────────────────────────────────
# Gap analysis
# ─────────────────────────────────────────────────────────────────────────────

def run_gap_analysis() -> None:
    print("\n=== Gap Analysis ===")
    run_gap_analysis_from_pipeline_output(
        structured_csv_dir=os.path.join(DATA_DIR, "structured"),
        raw_json_dir=RAW_DIR,
        state_code="CA",
        output_dir=os.path.join(DATA_DIR, "gap_analysis"),
    )


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def _parse_args():
    p = argparse.ArgumentParser(
        description="iTREDS 3-phase pipeline: Crawl → Structure → Index",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument(
        "--counties",
        type=str,
        default=None,
        help=(
            "Comma-separated county names to process. "
            "Default: all 58 counties in MATERNAL_HEALTH_URLS."
        ),
    )
    p.add_argument(
        "--phase",
        type=int,
        choices=[1, 2, 3],
        default=None,
        help="Run only a single phase (1=Crawl, 2=Structure, 3=Index).",
    )
    p.add_argument(
        "--skip-index",
        action="store_true",
        help="Skip Phase 3 (vectorstore build). Useful when LangChain deps are not installed.",
    )
    p.add_argument(
        "--skip-gap",
        action="store_true",
        help="Skip the gap analysis step.",
    )
    return p.parse_args()


def main():
    args = _parse_args()

    counties: List[str] = TARGET_COUNTIES
    if args.counties:
        # Build a case-insensitive lookup so "mendocino" → "Mendocino"
        _ci = {k.lower(): k for k in CALIFORNIA_COUNTIES}
        raw = [c.strip() for c in args.counties.split(",") if c.strip()]
        counties = []
        unknown = []
        for c in raw:
            canonical = _ci.get(c.lower())
            if canonical:
                counties.append(canonical)
            else:
                unknown.append(c)
        if unknown:
            print(f"⚠  Unknown counties (not in CALIFORNIA_COUNTIES): {unknown}")
            print("   Check spelling or add the county to src/config.py first.")
        if not counties:
            print("   No valid counties — exiting.")
            return

    print("\n" + "=" * 60)
    print(f"🚀  iTREDS Pipeline — {len(counties)} counties")
    print("=" * 60)
    print("Counties:", ", ".join(counties))
    print()

    if args.phase == 1:
        run_phase_1(counties)
    elif args.phase == 2:
        run_phase_2()
    elif args.phase == 3:
        run_phase_3(counties)
    else:
        # Full pipeline
        run_phase_1(counties)
        run_phase_2()
        if not args.skip_index:
            run_phase_3(counties)
        if not args.skip_gap:
            run_gap_analysis()

    print("\nDone.")


if __name__ == "__main__":
    main()
