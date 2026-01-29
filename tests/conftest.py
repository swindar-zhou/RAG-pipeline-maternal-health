"""
Pytest configuration and shared fixtures for integration tests.
"""

import os
import json
import pytest
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List
from datetime import datetime

from schemas.discovery import DiscoveryResult, ProgramLink
from schemas.extraction import RawPage, Contacts


@pytest.fixture
def temp_data_dir():
    """Create a temporary data directory for tests."""
    temp_dir = tempfile.mkdtemp(prefix="itreds_test_")
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_county_name():
    """Sample county name for testing."""
    return "Test County"


@pytest.fixture
def sample_county_url():
    """Sample county URL for testing."""
    return "https://test-county.gov/"


@pytest.fixture
def sample_discovery_result(sample_county_name, sample_county_url):
    """Sample discovery result for Phase 1."""
    return {
        "county_name": sample_county_name,
        "county_url": sample_county_url,
        "health_dept_url": f"{sample_county_url}health",
        "maternal_section_url": f"{sample_county_url}health/maternal",
        "programs": [
            {
                "name": "Medi-Cal",
                "url": f"{sample_county_url}health/medi-cal",
                "link_text": "Medi-Cal Program",
                "nav_path": "Main → Health Dept → Maternal/Child",
                "score": 5.0
            },
            {
                "name": "CalFresh",
                "url": f"{sample_county_url}health/calfresh",
                "link_text": "CalFresh Food Assistance",
                "nav_path": "Main → Health Dept → Maternal/Child",
                "score": 4.0
            }
        ]
    }


@pytest.fixture
def sample_discovery_results_json(sample_discovery_result):
    """Sample discovery results JSON structure."""
    return {
        "generated_at": datetime.now().isoformat(),
        "results": [sample_discovery_result]
    }


@pytest.fixture
def sample_raw_page(sample_county_name):
    """Sample raw page data for Phase 2."""
    return {
        "county": sample_county_name,
        "page_url": "https://test-county.gov/health/medi-cal",
        "link_text": "Medi-Cal Program",
        "program_name_guess": "Medi-Cal",
        "nav_path": "Main → Health Dept → Maternal/Child",
        "scraped_at": datetime.now().isoformat(),
        "text": "Medi-Cal is California's Medicaid program that provides free or low-cost health coverage to children and adults. Eligibility requirements include income limits. To apply, visit the county office or apply online. For questions call 1-800-123-4567.",
        "contacts": {
            "phones": ["800-123-4567"],
            "emails": ["health@test-county.gov"]
        },
        "pdf_links": [
            "https://test-county.gov/docs/medi-cal-application.pdf",
            "https://test-county.gov/docs/eligibility-guide.pdf"
        ]
    }


@pytest.fixture
def sample_structured_program():
    """Sample structured program output from Phase 3."""
    return {
        "county_name": "Test County",
        "state": "California",
        "county_website_url": "https://test-county.gov/",
        "health_department_name": "Test County Health Department",
        "health_department_contact_email": "health@test-county.gov",
        "health_department_contact_phone": "800-123-4567",
        "programs": [
            {
                "program_name": "Medi-Cal",
                "program_category": "Primary Care",
                "program_description": "Medi-Cal provides health coverage for low-income individuals",
                "target_population": "Low-income individuals and families",
                "eligibility_requirements": "Income-based eligibility",
                "application_process": "Apply online or visit county office",
                "required_documentation": "Proof of income, identification",
                "financial_assistance_available": "Yes",
                "program_website_url": "https://test-county.gov/health/medi-cal"
            }
        ],
        "notes": "Test data"
    }


@pytest.fixture
def mock_html_content():
    """Mock HTML content for web scraping tests."""
    return """
    <html>
        <head><title>Test County Health Department</title></head>
        <body>
            <nav>Navigation</nav>
            <header>Header</header>
            <main>
                <h1>Health Department</h1>
                <p>Contact us at health@test-county.gov or call (800) 123-4567</p>
                <a href="/health/medi-cal">Medi-Cal Program</a>
                <a href="/health/calfresh">CalFresh Food Assistance</a>
                <a href="/docs/application.pdf">Application Form</a>
            </main>
            <footer>Footer</footer>
        </body>
    </html>
    """


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response for Phase 3."""
    return {
        "choices": [{
            "message": {
                "content": json.dumps({
                    "county_name": "Test County",
                    "state": "California",
                    "county_website_url": "https://test-county.gov/",
                    "health_department_name": "Test County Health Department",
                    "health_department_contact_email": "health@test-county.gov",
                    "health_department_contact_phone": "800-123-4567",
                    "programs": [{
                        "program_name": "Medi-Cal",
                        "program_category": "Primary Care",
                        "program_description": "Medi-Cal provides health coverage",
                        "target_population": "Low-income individuals",
                        "eligibility_requirements": "Income-based eligibility",
                        "application_process": "Apply online",
                        "required_documentation": "Proof of income",
                        "financial_assistance_available": "Yes",
                        "program_website_url": "https://test-county.gov/health/medi-cal"
                    }],
                    "notes": "Test extraction"
                })
            }
        }]
    }
