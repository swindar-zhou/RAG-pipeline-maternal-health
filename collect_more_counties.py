#!/usr/bin/env python3
"""
Collect data for counties that don't have structured data yet.

This script identifies counties missing structured CSVs and runs the pipeline
for them.
"""

import os
import json
from pathlib import Path
from typing import List, Set

from src.config import CALIFORNIA_COUNTIES
from run_pipeline import run_phase_1, run_phase_2, run_phase_3


def get_counties_with_data() -> Set[str]:
    """Get set of counties that already have structured CSV files."""
    structured_dir = Path("data/structured")
    counties_with_data = set()
    
    if structured_dir.exists():
        for csv_file in structured_dir.glob("California_*.csv"):
            # Extract county name from filename
            # Format: California_County_Name_Healthcare_Data.csv
            name = csv_file.stem.replace("California_", "").replace("_Healthcare_Data", "")
            name = name.replace("_", " ")
            counties_with_data.add(name)
    
    return counties_with_data


def get_counties_with_raw_data() -> Set[str]:
    """Get set of counties that have raw JSON files."""
    raw_dir = Path("data/raw")
    counties_with_raw = set()
    
    if raw_dir.exists():
        for county_dir in raw_dir.iterdir():
            if county_dir.is_dir():
                # Convert slug back to county name
                slug = county_dir.name
                # Find matching county name
                for county_name in CALIFORNIA_COUNTIES.keys():
                    if slug == county_name.lower().replace(" ", "-"):
                        counties_with_raw.add(county_name)
                        break
    
    return counties_with_raw


def identify_missing_counties(target_counties: List[str]) -> List[str]:
    """Identify which target counties are missing structured data."""
    counties_with_data = get_counties_with_data()
    missing = [c for c in target_counties if c not in counties_with_data]
    return missing


def main():
    print("\n" + "="*60)
    print("🔍 Identifying Counties Missing Data")
    print("="*60)
    
    # Check current data status
    counties_with_data = get_counties_with_data()
    counties_with_raw = get_counties_with_raw_data()
    
    print(f"\nCounties with structured data: {len(counties_with_data)}")
    if counties_with_data:
        print(f"  {', '.join(sorted(counties_with_data))}")
    
    print(f"\nCounties with raw data only: {len(counties_with_raw - counties_with_data)}")
    raw_only = counties_with_raw - counties_with_data
    if raw_only:
        print(f"  {', '.join(sorted(raw_only))}")
    
    # Target counties from run_pipeline.py
    target_counties = [
        "Alameda", "Fresno", "Sacramento", "Kern", "Los Angeles",
        "San Francisco", "Orange", "Riverside", "Santa Clara", "Contra Costa"
    ]
    
    missing = identify_missing_counties(target_counties)
    
    print(f"\nCounties missing structured data: {len(missing)}")
    if missing:
        print(f"  {', '.join(missing)}")
    else:
        print("  ✓ All target counties have data!")
        return
    
    # Ask user which counties to process
    print("\n" + "="*60)
    print("📊 Data Collection Options")
    print("="*60)
    print("\n1. Collect data for ALL missing counties")
    print("2. Collect data for specific counties")
    print("3. Skip (exit)")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "3":
        print("Exiting.")
        return
    
    counties_to_process = []
    if choice == "1":
        counties_to_process = missing
        print(f"\n✓ Will process {len(counties_to_process)} counties")
    elif choice == "2":
        print("\nAvailable counties:")
        for i, county in enumerate(missing, 1):
            print(f"  {i}. {county}")
        selection = input("\nEnter county numbers (comma-separated, e.g., 1,2,3): ").strip()
        try:
            indices = [int(x.strip()) - 1 for x in selection.split(",")]
            counties_to_process = [missing[i] for i in indices if 0 <= i < len(missing)]
        except (ValueError, IndexError):
            print("Invalid selection. Exiting.")
            return
    else:
        print("Invalid choice. Exiting.")
        return
    
    if not counties_to_process:
        print("No counties selected. Exiting.")
        return
    
    print(f"\n🚀 Processing {len(counties_to_process)} counties...")
    print(f"Counties: {', '.join(counties_to_process)}")
    
    # Run pipeline for selected counties
    print("\n" + "="*60)
    print("Phase 1: Discovery")
    print("="*60)
    discovery_results = run_phase_1(counties_to_process)
    
    print("\n" + "="*60)
    print("Phase 2: Deep Extraction")
    print("="*60)
    run_phase_2(discovery_results)
    
    print("\n" + "="*60)
    print("Phase 3: LLM Structuring")
    print("="*60)
    run_phase_3(discovery_results)
    
    print("\n" + "="*60)
    print("✅ Data Collection Complete")
    print("="*60)
    print(f"\nProcessed {len(counties_to_process)} counties:")
    for county in counties_to_process:
        csv_path = f"data/structured/California_{county.replace(' ', '_')}_Healthcare_Data.csv"
        if os.path.exists(csv_path):
            print(f"  ✓ {county}: {csv_path}")
        else:
            print(f"  ⚠ {county}: No CSV generated")


if __name__ == "__main__":
    main()
