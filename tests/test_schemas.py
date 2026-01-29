"""
Tests for Pydantic schemas validation.
"""

import pytest
from datetime import datetime

from schemas.discovery import DiscoveryResult, ProgramLink
from schemas.extraction import RawPage, Contacts
from schemas.structured import StructuredProgram, StructuredCounty


class TestSchemas:
    """Test Pydantic schema validation."""
    
    def test_program_link_schema(self):
        """Test ProgramLink schema."""
        link = ProgramLink(
            name="Medi-Cal",
            url="https://test.gov/medi-cal",
            link_text="Medi-Cal Program",
            nav_path="Main → Health Dept",
            score=5.0
        )
        assert link.name == "Medi-Cal"
        assert link.score == 5.0
    
    def test_discovery_result_schema(self):
        """Test DiscoveryResult schema."""
        result = DiscoveryResult(
            county_name="Test County",
            county_url="https://test.gov/",
            health_dept_url="https://test.gov/health",
            programs=[
                ProgramLink(name="Medi-Cal", url="https://test.gov/medi-cal")
            ]
        )
        assert result.county_name == "Test County"
        assert len(result.programs) == 1
    
    def test_contacts_schema(self):
        """Test Contacts schema."""
        contacts = Contacts(
            phones=["800-123-4567", "800-987-6543"],
            emails=["health@test.gov"]
        )
        assert len(contacts.phones) == 2
        assert len(contacts.emails) == 1
    
    def test_raw_page_schema(self):
        """Test RawPage schema."""
        page = RawPage(
            county="Test County",
            page_url="https://test.gov/page",
            text="Test content",
            contacts=Contacts(phones=[], emails=[]),
            scraped_at=datetime.now()
        )
        assert page.county == "Test County"
        assert isinstance(page.scraped_at, datetime)
    
    def test_structured_program_schema(self):
        """Test StructuredProgram schema."""
        program = StructuredProgram(
            program_name="Medi-Cal",
            program_category="Primary Care",
            program_description="Health coverage program",
            target_population="Low-income individuals",
            eligibility_requirements="Income-based",
            application_process="Apply online",
            required_documentation="Proof of income",
            financial_assistance_available="Yes",
            program_website_url="https://test.gov/medi-cal"
        )
        assert program.program_category == "Primary Care"
        assert program.financial_assistance_available == "Yes"
    
    def test_structured_county_schema(self):
        """Test StructuredCounty schema."""
        county = StructuredCounty(
            county_name="Test County",
            county_website_url="https://test.gov/",
            health_department_name="Test Health Dept",
            health_department_contact_email="health@test.gov",
            health_department_contact_phone="800-123-4567",
            programs=[
                StructuredProgram(
                    program_name="Medi-Cal",
                    program_category="Primary Care",
                    program_description="Test",
                    target_population="Test",
                    eligibility_requirements="Test",
                    application_process="Test",
                    required_documentation="Test",
                    financial_assistance_available="Yes",
                    program_website_url="https://test.gov/medi-cal"
                )
            ]
        )
        assert county.county_name == "Test County"
        assert len(county.programs) == 1
        assert county.get_critical_fields_missing_rate() == 0.0
    
    def test_schema_validation_errors(self):
        """Test that invalid data raises validation errors."""
        with pytest.raises(Exception):  # Pydantic validation error
            StructuredProgram(
                program_name="Test",
                program_category="Invalid Category",  # Invalid category
                program_description="Test",
                target_population="Test",
                eligibility_requirements="Test",
                application_process="Test",
                required_documentation="Test",
                financial_assistance_available="Yes",
                program_website_url="https://test.com"
            )
