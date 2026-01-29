#!/usr/bin/env python3
"""
Collect data for counties missing structured CSV files.

This script identifies counties that need data collection and runs the pipeline.
"""

import os
import json
from pathlib import Path
from typing import List, Set

# Import shared config
from src.config import CALIFORNIA_COUNTIES


def get_counties_with_structured_data() -> Set[str]:
    """Get set of counties that already have structured CSV files."""
    structured_dir = Path("data/structured")
    counties_with_data = set()
    
    if structured_dir.exists():
        for csv_file in structured_dir.glob("California_*.csv"):
            # Extract county name from filename
            # Formats:
            #   - California_County_Name_Healthcare_Data.csv -> "County Name"
            #   - California_County_Healthcare_Data_San_Diego.csv -> "San Diego"
            stem = csv_file.stem  # e.g., "California_County_Healthcare_Data_San_Diego"
            name = stem.replace("California_", "")
            
            # Handle legacy format: "County_Healthcare_Data_San_Diego"
            if "_County_Healthcare_Data_" in stem:
                # Extract everything after "County_Healthcare_Data_"
                parts = stem.split("_County_Healthcare_Data_")
                if len(parts) > 1:
                    name = parts[1]  # e.g., "San_Diego"
                else:
                    name = name.replace("County_Healthcare_Data_", "")
            else:
                # Standard format: "County_Name_Healthcare_Data"
                name = name.replace("_Healthcare_Data", "")
                if name.startswith("County_"):
                    name = name.replace("County_", "", 1)
            
            name = name.replace("_", " ")
            counties_with_data.add(name)
    
    return counties_with_data


def main():
    print("\n" + "="*60)
    print("🔍 County Data Status Check")
    print("="*60)
    
    # Check current data status
    counties_with_data = get_counties_with_structured_data()
    
    print(f"\n✓ Counties with structured data: {len(counties_with_data)}")
    if counties_with_data:
        for county in sorted(counties_with_data):
            # Try both filename formats
            csv_path1 = f"data/structured/California_{county.replace(' ', '_')}_Healthcare_Data.csv"
            csv_path2 = f"data/structured/California_County_Healthcare_Data_{county.replace(' ', '_')}.csv"
            csv_path = csv_path1 if os.path.exists(csv_path1) else csv_path2
            if os.path.exists(csv_path):
                # Count lines (rough program count)
                with open(csv_path, 'r') as f:
                    lines = len(f.readlines()) - 1  # Subtract header
                print(f"  • {county}: {lines} programs")
    
    # Target counties from run_pipeline.py
    target_counties = [
        "Alameda", "Fresno", "Sacramento", "Kern", "Los Angeles",
        "San Francisco", "Orange", "Riverside", "Santa Clara", "Contra Costa"
    ]
    
    missing = [c for c in target_counties if c not in counties_with_data]
    
    print(f"\n⚠ Counties missing structured data: {len(missing)}")
    if missing:
        for county in missing:
            print(f"  • {county}")
    else:
        print("  ✓ All target counties have data!")
        return
    
    print("\n" + "="*60)
    print("📋 Next Steps")
    print("="*60)
    print("\nTo collect data for missing counties, run:")
    print(f"\n  python run_pipeline.py")
    print("\nThis will run all 3 phases for the target counties.")
    print("\nOr run phases individually:")
    print("  1. python scraper_discovery.py  # Phase 1: Discovery")
    print("  2. python scraper_extract.py    # Phase 2: Extraction")
    print("  3. python scraper_structure.py # Phase 3: Structuring")
    print("\nNote: Some counties may have empty programs arrays if")
    print("      discovery couldn't find health department pages.")
    print("      You may need to improve discovery or use agentic system.")


if __name__ == "__main__":
    main()
