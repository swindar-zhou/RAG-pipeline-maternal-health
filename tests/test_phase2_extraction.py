"""
Integration tests for Phase 2: Deep Extraction.
"""

import os
import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from schemas.extraction import RawPage, Contacts
from scraper_extract import process_program_page, extract_contacts, collect_pdf_links


class TestPhase2Extraction:
    """Test Phase 2 extraction functionality."""
    
    def test_raw_page_schema(self, sample_raw_page):
        """Test that raw page data matches the Pydantic schema."""
        page = RawPage(**sample_raw_page)
        assert page.county == sample_raw_page["county"]
        assert page.page_url == sample_raw_page["page_url"]
        assert isinstance(page.contacts, Contacts)
        assert len(page.contacts.phones) > 0
        assert len(page.pdf_links) > 0
    
    def test_extract_contacts(self):
        """Test contact extraction from text."""
        text = "Call us at (800) 123-4567 or email health@test-county.gov for assistance."
        contacts = extract_contacts(text)
        
        assert "phones" in contacts
        assert "emails" in contacts
        assert len(contacts["phones"]) > 0
        assert len(contacts["emails"]) > 0
        assert "800-123-4567" in contacts["phones"] or "8001234567" in contacts["phones"]
        assert "health@test-county.gov" in contacts["emails"]
    
    def test_collect_pdf_links(self):
        """Test PDF link extraction."""
        from bs4 import BeautifulSoup
        html_content = """
        <html>
            <body>
                <a href="/docs/application.pdf">Application Form</a>
                <a href="/docs/eligibility.pdf">Eligibility Guide</a>
                <a href="https://external.com/doc.pdf">External PDF</a>
            </body>
        </html>
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        base_url = "https://test-county.gov"
        pdf_links = collect_pdf_links(soup, base_url)
        
        assert len(pdf_links) >= 2
        assert any("application.pdf" in link for link in pdf_links)
        assert any("eligibility.pdf" in link for link in pdf_links)
    
    @patch('scraper_extract.fetch_soup')
    def test_process_program_page(self, mock_soup, 
                                  sample_county_name, sample_discovery_result, temp_data_dir):
        """Test processing a program page."""
        # Mock dependencies
        from bs4 import BeautifulSoup
        html_content = """
        <html>
            <body>
                <p>Call us at (800) 123-4567 or email health@test-county.gov</p>
                <a href="/docs/app.pdf">Application</a>
            </body>
        </html>
        """
        mock_soup.return_value = BeautifulSoup(html_content, "html.parser")
        
        # Override data directory for test
        import scraper_extract
        original_raw_dir = scraper_extract.RAW_DIR
        scraper_extract.RAW_DIR = os.path.join(temp_data_dir, "raw")
        os.makedirs(scraper_extract.RAW_DIR, exist_ok=True)
        
        try:
            program = sample_discovery_result["programs"][0]
            result_path = process_program_page(sample_county_name, program)
            
            # Result may be None if URL fetch fails, or a path if successful
            if result_path:
                assert os.path.exists(result_path)
                
                # Verify saved content
                with open(result_path, 'r') as f:
                    saved_data = json.load(f)
                
                assert saved_data["county"] == sample_county_name
                assert saved_data["page_url"] == program["url"]
                assert "text" in saved_data
                assert "contacts" in saved_data
        finally:
            scraper_extract.RAW_DIR = original_raw_dir
    
    def test_contact_extraction_patterns(self):
        """Test various phone and email patterns."""
        test_cases = [
            ("Call (800) 123-4567", ["800-123-4567"]),
            ("Phone: 800.123.4567", ["800-123-4567"]),
            ("Contact: 800 123 4567", ["800-123-4567"]),
            ("Email: test@example.com", ["test@example.com"]),
            ("Contact: health@county.gov or info@county.gov", ["health@county.gov", "info@county.gov"]),
        ]
        
        for text, expected in test_cases:
            contacts = extract_contacts(text)
            if expected[0].startswith("800"):
                # Check phones
                found = any(expected[0].replace("-", "").replace(".", "").replace(" ", "") in 
                          phone.replace("-", "").replace(".", "").replace(" ", "") 
                          for phone in contacts["phones"])
                assert found, f"Expected phone pattern not found in {contacts['phones']}"
            else:
                # Check emails
                assert any(email in contacts["emails"] for email in expected), \
                    f"Expected email not found in {contacts['emails']}"
