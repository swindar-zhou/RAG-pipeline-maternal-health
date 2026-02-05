#!/usr/bin/env python3
"""
Phase 3 - Structuring (Pilot)

Reads Phase 2 raw page JSON under data/raw/** and converts them into structured
program entries using an LLM (OpenAI gpt-4o-mini by default). Aggregates per
county and writes the CSV using scraper.save_to_csv.
"""

import os
import re
import json
import glob
import time
from typing import Dict, List, Optional
from datetime import datetime
# Try to load .env file, but don't fail if dotenv is not installed
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Import shared utilities and config
from src.utils import save_to_csv
from src.config import STATE_NAME, MAX_INPUT_CHARS, OPENAI_MODEL, OPENAI_MAX_TOKENS, TEMPERATURE, SLEEP_BETWEEN_CALLS

# Import taxonomy for maternal health focus (per advisor feedback)
from src.maternal_taxonomy import generate_few_shot_examples, MATERNAL_PROGRAM_TYPES

# -----------------------------------------------------------------------------
# Config
# -----------------------------------------------------------------------------

API_PROVIDER = os.getenv("API_PROVIDER", "openai")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

RAW_DIR = os.path.join("data", "raw")
DISCOVERY_PATH = os.path.join("data", "discovery_results.json")
OUTPUT_FILE = "California_County_Healthcare_Data.csv"

# Budget guardrails (imported from src.config)

# -----------------------------------------------------------------------------
# Utilities
# -----------------------------------------------------------------------------

def load_discovery(path: str) -> Dict[str, Dict]:
    """Return mapping county_name -> discovery entry (to get county_url, etc.)."""
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    results = data.get("results", [])
    return {r.get("county_name", ""): r for r in results}

def iter_raw_pages() -> List[str]:
    return glob.glob(os.path.join(RAW_DIR, "*", "*.json"))

def get_maternal_categories() -> str:
    """Get the list of maternal health categories from taxonomy."""
    categories = list(set(pt.category for pt in MATERNAL_PROGRAM_TYPES))
    return " | ".join(sorted(categories))


def build_prompt(county_name: str, county_url: str, page: Dict) -> str:
    """
    Build LLM prompt with maternal health focus and few-shot examples.
    
    Per advisor feedback: Use state-level programs as training data to help
    the model recognize what constitutes a maternal health program.
    """
    text = page.get("text", "")[:MAX_INPUT_CHARS]
    contacts = page.get("contacts", {})
    pdf_links = page.get("pdf_links", [])
    page_url = page.get("page_url", "")
    link_text = page.get("link_text", "")
    nav_path = page.get("nav_path", "")
    
    # Generate few-shot examples from taxonomy (per advisor's training data suggestion)
    few_shot = generate_few_shot_examples()
    
    # Get maternal-specific categories
    maternal_categories = get_maternal_categories()
    
    return f"""You are extracting structured MATERNAL HEALTH program data from a {STATE_NAME} county website page.

IMPORTANT: Focus ONLY on maternal health programs. These include programs for:
- Pregnant women, new mothers, and infants
- WIC, home visiting, prenatal care, postpartum support
- Breastfeeding/lactation support
- Family planning and reproductive health
- Programs addressing infant/maternal mortality

Do NOT extract general health programs like Medi-Cal, CalFresh, behavioral health, senior services, etc.

EXAMPLES OF MATERNAL HEALTH PROGRAMS (from California and Florida state health departments):
{few_shot}

---

COUNTY: {county_name} County
COUNTY WEBSITE: {county_url}
PAGE URL: {page_url}
LINK TEXT: {link_text}
NAVIGATION PATH: {nav_path}
CONTACTS FOUND: {json.dumps(contacts)}
DOC LINKS: {json.dumps(pdf_links[:8])}

PAGE CONTENT:
{text}

---
TASK: If this page describes a MATERNAL HEALTH program, return a JSON object using this schema.
If the page is NOT about maternal health, return {{"programs": [], "notes": "Not a maternal health program"}}.

Schema:
{{
  "county_name": "{county_name}",
  "state": "{STATE_NAME}",
  "county_website_url": "{county_url}",
  "health_department_name": "Official name or 'Not found'",
  "health_department_contact_email": "Email or 'Not found'",
  "health_department_contact_phone": "Phone or 'Not found'",
  "programs": [
    {{
      "program_name": "Name of maternal health program",
      "program_category": "{maternal_categories} | Other",
      "program_description": "Brief description (1-2 sentences)",
      "target_population": "Who the program serves (e.g., pregnant women, new mothers, infants)",
      "eligibility_requirements": "Requirements or 'Not specified'",
      "services_provided": ["list", "of", "services"],
      "application_process": "How to apply or 'Not specified'",
      "required_documentation": "Documents needed or 'Not specified'",
      "financial_assistance_available": "Yes | No | Unknown",
      "program_website_url": "{page_url}"
    }}
  ],
  "notes": "Any data quality observations"
}}

RULES:
1) Extract ONLY maternal health programs. Skip general health services.
2) Extract only from provided content/metadata; never invent facts.
3) If a field is missing, use 'Not found' or 'Not specified' as appropriate.
4) Return ONLY the JSON object, no extra text.
"""

def extract_program_openai(prompt: str) -> Optional[Dict]:
    if not OPENAI_API_KEY:
        print("   ✗ OPENAI_API_KEY not set")
        return None
    try:
        import openai
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        resp = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are a precise data extraction assistant. Return valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=TEMPERATURE,
            max_tokens=OPENAI_MAX_TOKENS
        )
        content = resp.choices[0].message.content.strip()
        if content.startswith("```"):
            content = re.sub(r'^```(?:json)?\n?', '', content)
            content = re.sub(r'\n?```$', '', content)
        return json.loads(content)
    except Exception as e:
        print(f"   ✗ OpenAI extraction error: {e}")
        return None

# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

def main():
    print("\n" + "="*60)
    print("🧠 Phase 3 - LLM Structuring (Pilot)")
    print("="*60 + "\n")
    if API_PROVIDER != "openai":
        print("⚠ This script currently supports OpenAI only. Set API_PROVIDER=openai in .env")
        return
    county_meta = load_discovery(DISCOVERY_PATH)
    files = iter_raw_pages()
    if not files:
        print("⚠ No raw pages found. Run Phase 2 first: python scraper_extract.py")
        return
    print(f"Found {len(files)} raw pages\n")
    # Aggregate per county
    county_to_data: Dict[str, Dict] = {}
    for path in files:
        try:
            with open(path, "r", encoding="utf-8") as f:
                page = json.load(f)
        except Exception as e:
            print(f"   ✗ Failed to read {path}: {e}")
            continue
        county_name = page.get("county", "")
        meta = county_meta.get(county_name, {})
        county_url = meta.get("county_url", "")
        prompt = build_prompt(county_name, county_url, page)
        result = extract_program_openai(prompt)
        time.sleep(SLEEP_BETWEEN_CALLS)
        if not result:
            print(f"   ⚠ Skipping (no result) for {os.path.basename(path)}")
            continue
        # Initialize county object if needed
        if county_name not in county_to_data:
            county_to_data[county_name] = {
                "county_name": county_name,
                "state": STATE_NAME,
                "county_website_url": county_url,
                "health_department_name": result.get("health_department_name", "Not found"),
                "health_department_contact_email": result.get("health_department_contact_email", "Not found"),
                "health_department_contact_phone": result.get("health_department_contact_phone", "Not found"),
                "programs": [],
                "notes": ""
            }
        # Append programs (expecting 1, but support multiple)
        programs = result.get("programs", [])
        county_to_data[county_name]["programs"].extend(programs)
        # Merge any notes
        if result.get("notes"):
            joined = county_to_data[county_name].get("notes", "")
            county_to_data[county_name]["notes"] = (joined + " " + str(result["notes"])).strip()
        print(f"   ✓ Structured {os.path.basename(path)} → {len(programs)} program(s)")
    # Convert to list and write CSV
    results_list = list(county_to_data.values())
    if not results_list:
        print("\n⚠ No structured data produced")
        return
    # Save per-county CSVs under data/structured
    os.makedirs(os.path.join("data", "structured"), exist_ok=True)
    def safe_name(name: str) -> str:
        return name.replace(" ", "_")
    for county in results_list:
        county_name = county.get("county_name", "Unknown")
        filename = os.path.join("data", "structured", f"{STATE_NAME}_{safe_name(county_name)}_Healthcare_Data.csv")
        save_to_csv([county], filename)
        print(f"✓ Wrote county CSV: {filename}")
    # Also write combined CSV (backward compatible)
    save_to_csv(results_list, OUTPUT_FILE)
    total_programs = sum(len(c.get("programs", [])) for c in results_list)
    print("\n" + "="*60)
    print("📊 Phase 3 Summary")
    print("="*60)
    print(f"Counties with data: {len(results_list)}")
    print(f"Total programs structured: {total_programs}")
    print(f"Output file (combined): {OUTPUT_FILE}")
    print(f"Per-county files: data/structured/{STATE_NAME}_<County>_Healthcare_Data.csv")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()


