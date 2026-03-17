#!/usr/bin/env python3
"""
Evaluation script for the 3-phase pipeline.

Runs evaluation against gold dataset and outputs metrics table + CSV.
"""

import os
import json
import csv
import hashlib
import subprocess
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path

from schemas.discovery import DiscoveryResult
from schemas.extraction import RawPage
from schemas.structured import StructuredCounty, StructuredProgram
from eval.gold_schema import GoldCounty
from eval.metrics import (
    CountyMetrics,
    calculate_phase1_metrics,
    calculate_phase2_metrics,
    calculate_phase3_metrics,
)
from eval.gap_detector import run_gap_analysis_from_pipeline_output


# Paths
GOLD_DATASET_PATH = os.path.join("eval", "gold_maternal.jsonl")
DISCOVERY_PATH = os.path.join("data", "discovery_results.json")
RAW_DIR = os.path.join("data", "raw")
STRUCTURED_DIR = os.path.join("data", "structured")
RESULTS_DIR = os.path.join("eval", "results")


def get_run_id() -> str:
    """Generate a unique run ID with timestamp, model, and code hash."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Get git SHA
    try:
        git_sha = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL
        ).decode().strip()[:8]
    except:
        git_sha = "unknown"
    
    # Hash prompt/configuration (simplified)
    config_hash = hashlib.md5(
        f"{os.getenv('API_PROVIDER', 'openai')}{os.getenv('OPENAI_MODEL', 'gpt-4o-mini')}".encode()
    ).hexdigest()[:8]
    
    return f"{timestamp}_{git_sha}_{config_hash}"


def load_gold_dataset(path: str) -> Dict[str, GoldCounty]:
    """Load gold dataset from JSONL file."""
    gold_by_county = {}
    
    if not os.path.exists(path):
        print(f"⚠ Gold dataset not found at {path}")
        print("   Create eval/gold.jsonl with ground truth labels")
        return gold_by_county
    
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            county_data = json.loads(line)
            gold = GoldCounty(**county_data)
            gold_by_county[gold.county_name] = gold
    
    return gold_by_county


def load_discovery_results(path: str) -> Dict[str, DiscoveryResult]:
    """Load discovery results."""
    if not os.path.exists(path):
        return {}
    
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    results = {}
    for entry in data.get("results", []):
        discovery = DiscoveryResult(**entry)
        results[discovery.county_name] = discovery
    
    return results


def load_raw_pages_for_county(county_name: str) -> List[RawPage]:
    """Load all raw pages for a county."""
    county_slug = county_name.lower().replace(" ", "-")
    county_dir = os.path.join(RAW_DIR, county_slug)
    
    if not os.path.isdir(county_dir):
        return []
    
    pages = []
    for fname in os.listdir(county_dir):
        if not fname.endswith(".json"):
            continue
        
        path = os.path.join(county_dir, fname)
        try:
            with open(path, "r", encoding="utf-8") as f:
                page_data = json.load(f)
                pages.append(RawPage(**page_data))
        except Exception as e:
            print(f"   ⚠ Failed to load {path}: {e}")
    
    return pages


def load_structured_for_county(county_name: str, structured_dir: str = STRUCTURED_DIR) -> Optional[StructuredCounty]:
    """Load structured data for a county by parsing its per-county CSV."""
    county_slug = county_name.replace(" ", "_")

    # Search recursively so versioned subdirs (v1/, v2/) are included
    search_dir = Path(structured_dir)
    candidates = list(search_dir.rglob(f"*{county_slug}*.csv"))
    if not candidates:
        return None
    csv_path = candidates[0]

    programs = []
    county_url = ""
    health_dept_name = ""
    health_dept_email = ""
    health_dept_phone = ""

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            county_url = row.get("County_Website_URL", "")
            health_dept_name = row.get("Health_Department_Name", "")
            health_dept_email = row.get("Health_Department_Contact_Email", "")
            health_dept_phone = row.get("Health_Department_Contact_Phone", "")
            program_name = row.get("Program_Name", "").strip()
            if not program_name:
                continue
            try:
                programs.append(StructuredProgram(
                    program_name=program_name,
                    program_category=row.get("Program_Category", ""),
                    program_description=row.get("Program_Description", ""),
                    target_population=row.get("Target_Population", ""),
                    eligibility_requirements=row.get("Eligibility_Requirements", "Not specified"),
                    application_process=row.get("Application_Process", "Not specified"),
                    required_documentation=row.get("Required_Documentation", "Not specified"),
                    financial_assistance_available=row.get("Financial_Assistance_Available", "Unknown"),
                    program_website_url=row.get("Program_Website_URL", ""),
                ))
            except Exception:
                continue

    if not programs:
        return None

    return StructuredCounty(
        county_name=county_name,
        state="California",
        county_website_url=county_url,
        health_department_name=health_dept_name,
        health_department_contact_email=health_dept_email,
        health_department_contact_phone=health_dept_phone,
        programs=programs,
        notes="",
    )


def run_evaluation() -> Dict:
    """Run evaluation against gold dataset."""
    print("\n" + "="*60)
    print("🔍 Running Evaluation")
    print("="*60)
    
    # Load gold dataset
    gold_by_county = load_gold_dataset(GOLD_DATASET_PATH)
    
    if not gold_by_county:
        print("\n⚠ No gold dataset found. Skipping evaluation.")
        print("   Create eval/gold.jsonl with ground truth labels.")
        return {}
    
    print(f"\n✓ Loaded {len(gold_by_county)} counties from gold dataset")
    
    # Load pipeline outputs
    discovery_results = load_discovery_results(DISCOVERY_PATH)
    print(f"✓ Loaded discovery results for {len(discovery_results)} counties")
    
    # Calculate metrics per county
    county_metrics: Dict[str, CountyMetrics] = {}
    
    for county_name, gold in gold_by_county.items():
        print(f"\n📊 Evaluating {county_name}...")
        
        # Phase 1 metrics
        discovery = discovery_results.get(county_name)
        if not discovery:
            print(f"   ⚠ No discovery results for {county_name}")
            continue
        
        phase1_metrics = calculate_phase1_metrics(discovery, gold)
        
        # Phase 2 metrics
        raw_pages = load_raw_pages_for_county(county_name)
        phase2_metrics = calculate_phase2_metrics(raw_pages, gold)
        
        # Phase 3 metrics (simplified - would need CSV parsing)
        structured = load_structured_for_county(county_name)
        if structured:
            phase3_metrics = calculate_phase3_metrics(structured, gold)
        else:
            # Use defaults if structured data not available
            from eval.metrics import Phase3Metrics
            phase3_metrics = Phase3Metrics(
                schema_validity_rate=0.0,
                critical_field_missing_rate=1.0,
                field_exact_match_rate=0.0
            )
        
        county_metrics[county_name] = CountyMetrics(
            county_name=county_name,
            phase1=phase1_metrics,
            phase2=phase2_metrics,
            phase3=phase3_metrics
        )
        
        print(f"   Phase 1: Recall@20={phase1_metrics.recall_at_20:.2%}, Programs found={phase1_metrics.programs_found}")
        print(f"   Phase 2: Contact P/R={phase2_metrics.contact_precision:.2%}/{phase2_metrics.contact_recall:.2%}")
        print(f"   Phase 3: Schema validity={phase3_metrics.schema_validity_rate:.2%}, Missing fields={phase3_metrics.critical_field_missing_rate:.2%}")
    
    # Aggregate metrics
    if not county_metrics:
        print("\n⚠ No metrics calculated. Check that pipeline outputs exist.")
        return {}
    
    # Calculate averages
    avg_recall_at_20 = sum(m.phase1.recall_at_20 for m in county_metrics.values()) / len(county_metrics)
    avg_contact_precision = sum(m.phase2.contact_precision for m in county_metrics.values()) / len(county_metrics)
    avg_contact_recall = sum(m.phase2.contact_recall for m in county_metrics.values()) / len(county_metrics)
    avg_schema_validity = sum(m.phase3.schema_validity_rate for m in county_metrics.values()) / len(county_metrics)
    avg_missing_fields = sum(m.phase3.critical_field_missing_rate for m in county_metrics.values()) / len(county_metrics)
    
    print("\n" + "="*60)
    print("📈 Aggregate Metrics")
    print("="*60)
    print(f"Average Recall@20:        {avg_recall_at_20:.2%}")
    print(f"Average Contact Precision: {avg_contact_precision:.2%}")
    print(f"Average Contact Recall:    {avg_contact_recall:.2%}")
    print(f"Average Schema Validity:   {avg_schema_validity:.2%}")
    print(f"Average Missing Fields:    {avg_missing_fields:.2%}")
    print("="*60)
    
    # Save results
    run_id = get_run_id()
    os.makedirs(RESULTS_DIR, exist_ok=True)
    
    results_summary = {
        "run_id": run_id,
        "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        "timestamp": datetime.now().isoformat(),
        "counties_evaluated": len(county_metrics),
        "aggregate_metrics": {
            "avg_recall_at_20": avg_recall_at_20,
            "avg_contact_precision": avg_contact_precision,
            "avg_contact_recall": avg_contact_recall,
            "avg_schema_validity": avg_schema_validity,
            "avg_missing_fields": avg_missing_fields,
        },
        "county_metrics": {name: m.to_dict() for name, m in county_metrics.items()}
    }
    
    # Save JSON
    json_path = os.path.join(RESULTS_DIR, f"metrics_{run_id}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results_summary, f, indent=2, ensure_ascii=False)
    print(f"\n✓ Saved metrics to {json_path}")
    
    # Save CSV
    csv_path = os.path.join(RESULTS_DIR, f"metrics_{run_id}.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "County", "Recall@20", "Contact_Precision", "Contact_Recall",
            "Schema_Validity", "Missing_Fields", "Field_Exact_Match"
        ])
        for name, metrics in county_metrics.items():
            writer.writerow([
                name,
                f"{metrics.phase1.recall_at_20:.4f}",
                f"{metrics.phase2.contact_precision:.4f}",
                f"{metrics.phase2.contact_recall:.4f}",
                f"{metrics.phase3.schema_validity_rate:.4f}",
                f"{metrics.phase3.critical_field_missing_rate:.4f}",
                f"{metrics.phase3.field_exact_match_rate:.4f}",
            ])
    print(f"✓ Saved CSV to {csv_path}")

    # Run gap analysis against the same pipeline output
    print("\n" + "="*60)
    print("🔎 Running Gap Analysis")
    print("="*60)
    gap_report = run_gap_analysis_from_pipeline_output(
        structured_csv_dir=STRUCTURED_DIR,
        raw_json_dir=RAW_DIR,
        state_code="CA",
        output_dir=os.path.join("data", "gap_analysis"),
    )
    results_summary["gap_analysis"] = {
        "unmatched_rate": gap_report.unmatched_rate,
        "gap_candidates": len(gap_report.candidates),
        "alias_miss_signals": len(gap_report.absence_signals),
    }

    return results_summary


if __name__ == "__main__":
    run_evaluation()

