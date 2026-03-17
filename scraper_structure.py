#!/usr/bin/env python3
"""
Phase 3 - LLM Structuring v2
==============================
Key improvements over v1:

  1. Registry-grounded prompt  — LLM is given the federal program list as
                                 ground truth, not just keyword hints
  2. program_id in output      — every extracted program maps back to the
                                 registry, enabling gap analysis
  3. Removed second LLM pass   — registry match replaces the
                                 LLMProgramClassifier re-classification call
  4. Async batch LLM calls     — concurrent OpenAI requests, ~3x faster
  5. Best-value contact merge  — county metadata picks the most informative
                                 value across all files, not just the first
  6. Structured skip logging   — Phase 3 now reports WHY files were skipped

USAGE:  python scraper_structure_v2.py
        (drop-in replacement; same outputs as v1)
"""

from __future__ import annotations

import asyncio
import glob
import json
import os
import re
import time
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(PROJECT_ROOT, ".env")


def _load_env(path: str) -> None:
    if not os.path.exists(path):
        return
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k, v = k.strip(), v.strip().strip("'\"")
                if k:
                    os.environ.setdefault(k, v)
    except Exception:
        pass


try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=ENV_PATH, override=True)
except ImportError:
    _load_env(ENV_PATH)

from src.utils import save_to_csv, get_next_structured_version_dir
from src.config import (
    STATE_NAME, MAX_INPUT_CHARS, OPENAI_MODEL,
    OPENAI_MAX_TOKENS, TEMPERATURE, SLEEP_BETWEEN_CALLS,
)
from src.federal_program_registry import (
    FEDERAL_PROGRAM_REGISTRY,
    FederalProgram,
    get_aliases_flat,
    get_applicable_programs,
)

# ─────────────────────────────────────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────────────────────────────────────

OPENAI_API_KEY  = os.getenv("OPENAI_API_KEY", "")
RAW_DIR         = os.path.join("data", "raw")
DISCOVERY_PATH  = os.path.join("data", "discovery_results.json")
OUTPUT_FILE     = "California_County_Healthcare_Data.csv"
CONCURRENCY     = 5   # simultaneous OpenAI requests (stay under rate limit)

# ─────────────────────────────────────────────────────────────────────────────
# Registry helpers
# ─────────────────────────────────────────────────────────────────────────────

# Programs applicable to California (universal + CA-specific)
_CA_PROGRAMS: List[FederalProgram] = get_applicable_programs("CA")
_CA_ALIAS_MAP: Dict[str, str] = get_aliases_flat("CA")  # alias → program_id

def _registry_snapshot() -> str:
    """
    Build a compact registry reference block for the LLM prompt.
    Groups programs by tier so the LLM understands which are universal
    vs. California-specific.
    """
    lines = ["FEDERAL / STATE PROGRAM REGISTRY (California):"]
    lines.append("Use these canonical program_ids when a page mentions a known program.\n")

    by_tier = defaultdict(list)
    for p in _CA_PROGRAMS:
        by_tier[p.tier].append(p)

    tier_labels = {
        1: "Tier 1 — Universal (every county should list these)",
        2: "Tier 2 — State-wide (all counties receive funding, local presence varies)",
        3: "Tier 3 — Selective (CA-specific or evidence-based models, not every county)",
    }
    for tier in [1, 2, 3]:
        lines.append(f"  {tier_labels[tier]}:")
        for p in by_tier[tier]:
            state_tag = f" [{p.state_specific}]" if p.state_specific else ""
            aliases_short = ", ".join(p.county_aliases[:4])
            lines.append(
                f"    program_id={p.program_id}{state_tag}\n"
                f"      name: {p.canonical_name}\n"
                f"      aliases: {aliases_short}\n"
                f"      serves: {p.target_population[:80]}"
            )
    return "\n".join(lines)


def match_to_registry(program_name: str, description: str, services: List[str]) -> Tuple[Optional[str], float]:
    """
    Attempt to match an extracted program name to a registry program_id.
    Returns (program_id, confidence) where confidence is 0.0–1.0.

    Three-pass matching:
      Pass 1: exact alias match (confidence 1.0)
      Pass 2: partial alias match (confidence 0.8)
      Pass 3: keyword overlap with canonical name (confidence 0.5)
    """
    combined = (program_name + " " + description + " " + " ".join(services)).lower()

    # Pass 1: exact alias match
    for alias, pid in _CA_ALIAS_MAP.items():
        if alias in combined:
            return pid, 1.0

    # Pass 2: partial match — alias tokens in combined text
    for alias, pid in _CA_ALIAS_MAP.items():
        tokens = alias.split()
        if len(tokens) >= 2 and all(t in combined for t in tokens):
            return pid, 0.8

    # Pass 3: canonical name word overlap
    best_pid, best_overlap = None, 0
    name_tokens = set(re.findall(r"[a-z]{4,}", combined))
    for p in _CA_PROGRAMS:
        canon_tokens = set(re.findall(r"[a-z]{4,}", p.canonical_name.lower()))
        overlap = len(name_tokens & canon_tokens)
        if overlap > best_overlap:
            best_overlap = overlap
            best_pid = p.program_id

    if best_overlap >= 2:
        return best_pid, 0.5

    return None, 0.0


def enrich_with_registry(program: Dict) -> Dict:
    """
    Add registry fields to an extracted program dict:
      program_id, registry_match_confidence, tier,
      blueprint_goal, category (from registry if match found)
    """
    name = program.get("program_name", "")
    desc = program.get("program_description", "")
    svcs = program.get("services_provided", [])
    if isinstance(svcs, str):
        svcs = [svcs]

    pid, conf = match_to_registry(name, desc, svcs)

    program["program_id"] = pid or "UNMATCHED"
    program["registry_match_confidence"] = round(conf, 2)

    if pid:
        reg = next((p for p in _CA_PROGRAMS if p.program_id == pid), None)
        if reg:
            program.setdefault("program_category", reg.category)
            program["blueprint_goal"] = reg.blueprint_goal
            program["tier"] = reg.tier
            program["registry_canonical_name"] = reg.canonical_name
    else:
        program["blueprint_goal"] = None
        program["tier"] = None
        program["registry_canonical_name"] = None

    return program

# ─────────────────────────────────────────────────────────────────────────────
# Prompt builder
# ─────────────────────────────────────────────────────────────────────────────

_REGISTRY_BLOCK = _registry_snapshot()  # compute once at module load

def build_prompt(county_name: str, county_url: str, page: Dict) -> str:
    text        = page.get("text", "")[:MAX_INPUT_CHARS]
    contacts    = page.get("contacts", {})
    pdf_links   = page.get("pdf_links", [])[:8]
    page_url    = page.get("page_url", "")
    link_text   = page.get("link_text", "")
    nav_path    = page.get("nav_path", "")
    reg_signals = page.get("registry_signals", [])   # from Phase 2 v2

    # Hint the LLM about which programs Phase 2 already detected on this page
    signal_hint = ""
    if reg_signals:
        signal_hint = (
            f"\nPHASE 2 DETECTED these registry signals on this page: {reg_signals}\n"
            "These are strong hints about which programs are described here.\n"
        )

    return f"""You are extracting structured MATERNAL HEALTH program data from a California county website page.

{_REGISTRY_BLOCK}

---
COUNTY: {county_name} County
COUNTY WEBSITE: {county_url}
PAGE URL: {page_url}
LINK TEXT: {link_text}
NAV PATH: {nav_path}
CONTACTS: {json.dumps(contacts)}
PDF LINKS: {json.dumps(pdf_links)}{signal_hint}

PAGE CONTENT:
{text}

---
TASK:
Extract ONLY maternal health programs from the page content above.
For each program found, attempt to match it to a program_id from the registry above.
If no match exists, set program_id to "UNMATCHED".
If the page contains no maternal health programs, return {{"programs": [], "notes": "reason"}}.

Return a JSON object with this exact schema — no extra text, no markdown:

{{
  "health_department_name": "string or Not found",
  "health_department_contact_email": "string or Not found",
  "health_department_contact_phone": "string or Not found",
  "programs": [
    {{
      "program_name": "exact name from page",
      "program_id": "registry program_id or UNMATCHED",
      "program_category": "category string",
      "program_description": "1-2 sentence description",
      "target_population": "who it serves",
      "eligibility_requirements": "requirements or Not specified",
      "services_provided": ["list", "of", "services"],
      "application_process": "how to apply or Not specified",
      "required_documentation": "documents needed or Not specified",
      "financial_assistance_available": "Yes | No | Unknown",
      "program_website_url": "{page_url}"
    }}
  ],
  "notes": "data quality observations or empty string"
}}

RULES:
1. Extract ONLY maternal/infant/reproductive health programs.
2. Use registry program_ids wherever possible — this enables gap analysis.
3. Never invent facts. Use only information present in the page content above.
4. If a field is missing from the page, use "Not found" or "Not specified".
5. Return ONLY valid JSON. No markdown, no preamble.
"""

# ─────────────────────────────────────────────────────────────────────────────
# LLM call (async)
# ─────────────────────────────────────────────────────────────────────────────

async def _call_openai_async(
    prompt: str,
    semaphore: asyncio.Semaphore,
) -> Optional[Dict]:
    """Single async OpenAI call, under semaphore for rate limiting."""
    async with semaphore:
        try:
            import openai
            client = openai.AsyncOpenAI(api_key=OPENAI_API_KEY)
            resp = await client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a precise data extraction assistant. "
                            "Return valid JSON only. No markdown. No extra text."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=TEMPERATURE,
                max_tokens=OPENAI_MAX_TOKENS,
            )
            content = resp.choices[0].message.content.strip()
            # Strip markdown fences if present
            content = re.sub(r"^```(?:json)?\s*", "", content)
            content = re.sub(r"\s*```$", "", content)
            return json.loads(content)
        except json.JSONDecodeError as e:
            print(f"   ✗ JSON parse error: {e}")
            return None
        except Exception as e:
            print(f"   ✗ OpenAI error: {e}")
            return None


# ─────────────────────────────────────────────────────────────────────────────
# County metadata merge
# ─────────────────────────────────────────────────────────────────────────────

def _is_real(val: Any) -> bool:
    """True if val is a non-empty, non-placeholder string."""
    return bool(val) and str(val).strip().lower() not in (
        "not found", "not specified", "", "none", "n/a"
    )


def _merge_county_meta(existing: Dict, new_result: Dict) -> Dict:
    """
    Fix 6: update county metadata fields only if the new value is more
    informative than the existing one. Prevents first-file "Not found"
    from locking out real values found in later files.
    """
    for field in (
        "health_department_name",
        "health_department_contact_email",
        "health_department_contact_phone",
    ):
        existing_val = existing.get(field, "")
        new_val = new_result.get(field, "")
        if _is_real(new_val) and not _is_real(existing_val):
            existing[field] = new_val
    return existing


# ─────────────────────────────────────────────────────────────────────────────
# Core processing
# ─────────────────────────────────────────────────────────────────────────────

def _load_discovery(path: str) -> Dict[str, Dict]:
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return {r.get("county_name", ""): r for r in data.get("results", [])}


async def _process_file(
    path: str,
    county_meta: Dict[str, Dict],
    semaphore: asyncio.Semaphore,
) -> Tuple[str, Optional[Dict], str]:
    """
    Process one raw JSON file.
    Returns (file_basename, result_dict_or_None, status_message).
    """
    fname = os.path.basename(path)
    try:
        with open(path, encoding="utf-8") as f:
            page = json.load(f)
    except Exception as e:
        return fname, None, f"read error: {e}"

    county_name = page.get("county", "")
    meta = county_meta.get(county_name, {})
    county_url = meta.get("county_url", "")

    prompt = build_prompt(county_name, county_url, page)
    result = await _call_openai_async(prompt, semaphore)

    if result is None:
        return fname, None, "LLM call failed"

    programs = result.get("programs", [])
    if not isinstance(programs, list):
        return fname, None, "LLM returned malformed programs field"

    # Enrich each program with registry match (replaces second LLM pass)
    result["programs"] = [enrich_with_registry(p) for p in programs]
    result["county_name"] = county_name
    result["county_url"] = county_url

    n = len(result["programs"])
    unmatched = sum(1 for p in result["programs"] if p.get("program_id") == "UNMATCHED")
    status = f"{n} program(s)"
    if unmatched:
        status += f"  [{unmatched} unmatched → gap candidates]"

    return fname, result, status


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

async def _run_async():
    county_meta = _load_discovery(DISCOVERY_PATH)
    files = sorted(glob.glob(os.path.join(RAW_DIR, "*", "*.json")))

    if not files:
        print("⚠  No raw pages found. Run Phase 2 first.")
        return

    print(f"Found {len(files)} raw pages\n")

    semaphore = asyncio.Semaphore(CONCURRENCY)
    tasks = [_process_file(path, county_meta, semaphore) for path in files]

    # Aggregate results
    county_to_data: Dict[str, Dict] = {}
    skip_counts: Dict[str, int] = defaultdict(int)

    # Run all tasks concurrently, print as each completes
    for coro in asyncio.as_completed(tasks):
        fname, result, status = await coro

        if result is None:
            skip_counts[status] += 1
            print(f"   ○ {fname:<50} skipped: {status}")
            continue

        county_name = result.get("county_name", "")
        programs = result.get("programs", [])

        if not programs:
            skip_counts["no maternal programs found"] += 1
            note = result.get("notes", "")
            print(f"   ○ {fname:<50} 0 programs  [{note[:60]}]")
            continue

        print(f"   ✓ {fname:<50} {status}")

        if county_name not in county_to_data:
            county_to_data[county_name] = {
                "county_name": county_name,
                "state": STATE_NAME,
                "county_website_url": result.get("county_url", ""),
                "health_department_name": result.get("health_department_name", "Not found"),
                "health_department_contact_email": result.get("health_department_contact_email", "Not found"),
                "health_department_contact_phone": result.get("health_department_contact_phone", "Not found"),
                "programs": [],
                "notes": "",
            }
        else:
            # Fix 6: best-value merge for contact fields
            county_to_data[county_name] = _merge_county_meta(
                county_to_data[county_name], result
            )

        county_to_data[county_name]["programs"].extend(programs)

        if result.get("notes"):
            prev = county_to_data[county_name].get("notes", "")
            county_to_data[county_name]["notes"] = (prev + " " + str(result["notes"])).strip()

    # ── Write output ──────────────────────────────────────────────────────────
    results_list = list(county_to_data.values())
    if not results_list:
        print("\n⚠  No structured data produced.")
        return

    version_dir = get_next_structured_version_dir()
    print(f"\n📁 Output directory: {version_dir}")

    def _safe(name: str) -> str:
        return name.replace(" ", "_")

    for county in results_list:
        name = county.get("county_name", "Unknown")
        fpath = os.path.join(version_dir, f"{STATE_NAME}_{_safe(name)}_Healthcare_Data.csv")
        save_to_csv([county], fpath)
        print(f"✓ {fpath}")

    combined = os.path.join(version_dir, OUTPUT_FILE)
    save_to_csv(results_list, combined)

    # ── Summary ───────────────────────────────────────────────────────────────
    total_programs = sum(len(c.get("programs", [])) for c in results_list)
    matched = sum(
        1 for c in results_list
        for p in c.get("programs", [])
        if p.get("program_id") != "UNMATCHED"
    )
    unmatched = total_programs - matched

    print(f"\n{'='*60}")
    print("📊 Phase 3 Summary")
    print(f"{'='*60}")
    print(f"  Files processed:       {len(files)}")
    print(f"  Counties with data:    {len(results_list)}")
    print(f"  Total programs:        {total_programs}")
    print(f"  Registry matched:      {matched}  ({matched/max(total_programs,1):.0%})")
    print(f"  Unmatched (gaps):      {unmatched}  → run gap_detector.py")
    print(f"\n  Skips by reason:")
    for reason, count in sorted(skip_counts.items(), key=lambda x: -x[1]):
        print(f"    {count:3d}  {reason}")
    print(f"\n  Output: {version_dir}/")
    print(f"{'='*60}\n")


def main():
    if not OPENAI_API_KEY:
        print("✗ OPENAI_API_KEY not set in .env")
        return
    try:
        import openai  # noqa: F401
    except ImportError:
        print("✗ openai package not installed. Run: pip install openai")
        return

    print("\n" + "="*60)
    print("🧠 Phase 3 - LLM Structuring v2")
    print("="*60 + "\n")

    asyncio.run(_run_async())


if __name__ == "__main__":
    main()