"""
Shared utility functions.
"""

import csv
import os
import re
from typing import List, Dict
from datetime import datetime

from .config import STATE_NAME, DATA_COLLECTOR_NAME


STRUCTURED_BASE = os.path.join("data", "structured")


def get_next_structured_version_dir() -> str:
    """
    Scans data/structured/ for existing vN folders and returns the path
    to the next version (e.g. if v1 and v2 exist, returns 'data/structured/v3').
    Creates the directory before returning.
    """
    os.makedirs(STRUCTURED_BASE, exist_ok=True)
    existing = [
        int(m.group(1))
        for d in os.listdir(STRUCTURED_BASE)
        if os.path.isdir(os.path.join(STRUCTURED_BASE, d))
        for m in [re.match(r"^v(\d+)$", d)]
        if m
    ]
    next_version = max(existing, default=0) + 1
    version_dir = os.path.join(STRUCTURED_BASE, f"v{next_version}")
    os.makedirs(version_dir, exist_ok=True)
    return version_dir


def save_to_csv(results: List[Dict], filename: str) -> None:
    """
    Save extracted data to CSV file.
    
    Args:
        results: List of county data dictionaries with programs
        filename: Output CSV file path
    """
    fieldnames = [
        'State', 'County_Name', 'County_Website_URL',
        'Health_Department_Name', 'Health_Department_Contact_Email', 'Health_Department_Contact_Phone',
        'Program_Name', 'Program_Category', 'Program_Description',
        'Target_Population', 'Eligibility_Requirements', 'Application_Process',
        'Required_Documentation', 'Financial_Assistance_Available', 'Program_Website_URL',
        'Last_Updated', 'Data_Collector_Name', 'Notes'
    ]
    
    rows = []
    
    for county_data in results:
        programs = county_data.get('programs', [])
        
        if not programs:
            # Still create a row even if no programs found
            rows.append({
                'State': county_data.get('state', STATE_NAME),
                'County_Name': county_data.get('county_name', ''),
                'County_Website_URL': county_data.get('county_website_url', ''),
                'Health_Department_Name': county_data.get('health_department_name', ''),
                'Health_Department_Contact_Email': county_data.get('health_department_contact_email', ''),
                'Health_Department_Contact_Phone': county_data.get('health_department_contact_phone', ''),
                'Program_Name': 'No programs found on main page',
                'Program_Category': '',
                'Program_Description': '',
                'Target_Population': '',
                'Eligibility_Requirements': '',
                'Application_Process': '',
                'Required_Documentation': '',
                'Financial_Assistance_Available': '',
                'Program_Website_URL': '',
                'Last_Updated': datetime.now().strftime('%Y-%m-%d'),
                'Data_Collector_Name': DATA_COLLECTOR_NAME,
                'Notes': county_data.get('notes', '')
            })
        else:
            # One row per program
            for program in programs:
                rows.append({
                    'State': county_data.get('state', STATE_NAME),
                    'County_Name': county_data.get('county_name', ''),
                    'County_Website_URL': county_data.get('county_website_url', ''),
                    'Health_Department_Name': county_data.get('health_department_name', ''),
                    'Health_Department_Contact_Email': county_data.get('health_department_contact_email', ''),
                    'Health_Department_Contact_Phone': county_data.get('health_department_contact_phone', ''),
                    'Program_Name': program.get('program_name', ''),
                    'Program_Category': program.get('program_category', ''),
                    'Program_Description': program.get('program_description', ''),
                    'Target_Population': program.get('target_population', ''),
                    'Eligibility_Requirements': program.get('eligibility_requirements', ''),
                    'Application_Process': program.get('application_process', ''),
                    'Required_Documentation': program.get('required_documentation', ''),
                    'Financial_Assistance_Available': program.get('financial_assistance_available', ''),
                    'Program_Website_URL': program.get('program_website_url', ''),
                    'Last_Updated': datetime.now().strftime('%Y-%m-%d'),
                    'Data_Collector_Name': DATA_COLLECTOR_NAME,
                    'Notes': county_data.get('notes', '')
                })
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"\n✓ Saved {len(rows)} rows to {filename}")

