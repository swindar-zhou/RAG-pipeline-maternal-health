#!/usr/bin/env python3
"""
Improved discovery using agentic system for counties that failed discovery.

This script uses the agentic discovery system to retry counties that
had empty programs arrays in the initial discovery.
"""

import os
import json
from typing import List, Dict
from datetime import datetime

from src.config import CALIFORNIA_COUNTIES
from agents.discovery_agent import DiscoveryAgent


def load_existing_discovery() -> Dict[str, Dict]:
    """Load existing discovery results."""
    discovery_path = "data/discovery_results.json"
    if not os.path.exists(discovery_path):
        return {}
    
    with open(discovery_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return {r["county_name"]: r for r in data.get("results", [])}


def find_counties_with_empty_programs() -> List[str]:
    """Find counties that have empty programs arrays."""
    existing = load_existing_discovery()
    empty = []
    
    for county_name, result in existing.items():
        programs = result.get("programs", [])
        if not programs or len(programs) == 0:
            empty.append(county_name)
    
    return empty


def improve_discovery_for_counties(county_names: List[str]) -> List[Dict]:
    """Use agentic discovery to improve results for counties."""
    print("\n" + "="*60)
    print("🤖 Agentic Discovery for Failed Counties")
    print("="*60)
    
    agent = DiscoveryAgent()
    results = []
    
    for county_name in county_names:
        county_url = CALIFORNIA_COUNTIES.get(county_name)
        if not county_url:
            print(f"   ⚠ County not found: {county_name}")
            continue
        
        print(f"\n→ Processing {county_name}...")
        try:
            discovery_result = agent.run(county_name, county_url)
            # Convert to dict format
            result_dict = {
                "county_name": discovery_result.county_name,
                "county_url": discovery_result.county_url,
                "health_dept_url": discovery_result.health_dept_url,
                "maternal_section_url": discovery_result.maternal_section_url,
                "programs": [
                    {
                        "name": p.name,
                        "url": p.url,
                        "link_text": p.link_text,
                        "nav_path": p.nav_path,
                        "score": p.score
                    }
                    for p in discovery_result.programs
                ]
            }
            results.append(result_dict)
            print(f"   ✓ Found {len(discovery_result.programs)} programs")
        except Exception as e:
            print(f"   ✗ Error: {e}")
            # Keep original result if agentic fails
            existing = load_existing_discovery()
            if county_name in existing:
                results.append(existing[county_name])
    
    return results


def main():
    print("\n" + "="*60)
    print("🔍 Finding Counties with Empty Programs")
    print("="*60)
    
    empty_counties = find_counties_with_empty_programs()
    
    if not empty_counties:
        print("\n✓ All counties have programs discovered!")
        return
    
    print(f"\nFound {len(empty_counties)} counties with empty programs:")
    for county in empty_counties:
        print(f"  • {county}")
    
    print("\n" + "="*60)
    print("Options:")
    print("="*60)
    print("1. Use agentic discovery to retry these counties")
    print("2. Show status and exit")
    
    choice = input("\nEnter choice (1-2): ").strip()
    
    if choice == "1":
        # Load existing results
        existing_results = load_existing_discovery()
        improved_results = improve_discovery_for_counties(empty_counties)
        
        # Merge: keep improved results, keep existing for others
        all_counties = set(list(existing_results.keys()) + [r["county_name"] for r in improved_results])
        final_results = []
        
        for county_name in sorted(all_counties):
            # Use improved result if available, otherwise existing
            improved = next((r for r in improved_results if r["county_name"] == county_name), None)
            if improved:
                final_results.append(improved)
            elif county_name in existing_results:
                final_results.append(existing_results[county_name])
        
        # Save updated discovery results
        output_path = "data/discovery_results.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({
                "generated_at": datetime.now().isoformat(),
                "results": final_results
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\n✓ Updated discovery results saved to {output_path}")
        print(f"  Total counties: {len(final_results)}")
        print(f"  Counties with programs: {sum(1 for r in final_results if r.get('programs'))}")
    else:
        print("\nExiting.")


if __name__ == "__main__":
    main()
