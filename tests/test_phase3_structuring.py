"""
Integration tests for Phase 3: LLM Structuring.
"""

import os
import json
import pytest
from unittest.mock import Mock, patch, MagicMock

from schemas.structured import StructuredProgram, StructuredCounty
from scraper_structure import build_prompt, extract_program_openai, load_discovery


class TestPhase3Structuring:
    """Test Phase 3 structuring functionality."""
    
    def test_structured_program_schema(self, sample_structured_program):
        """Test that structured program matches the Pydantic schema."""
        county = StructuredCounty(**sample_structured_program)
        assert county.county_name == sample_structured_program["county_name"]
        assert len(county.programs) > 0
        assert isinstance(county.programs[0], StructuredProgram)
    
    def test_build_prompt(self, sample_raw_page):
        """Test prompt building for LLM."""
        county_name = "Test County"
        county_url = "https://test-county.gov/"
        
        prompt = build_prompt(county_name, county_url, sample_raw_page)
        
        assert county_name in prompt
        assert county_url in prompt
        assert sample_raw_page["page_url"] in prompt
        assert "JSON" in prompt or "json" in prompt
        assert "program_name" in prompt
    
    @patch('scraper_structure.openai.OpenAI')
    def test_extract_program_openai(self, mock_openai_class, mock_openai_response):
        """Test OpenAI extraction."""
        # Mock OpenAI client
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        # Mock the chat completion response
        mock_response = MagicMock()
        mock_message = MagicMock()
        mock_message.content = json.dumps(mock_openai_response["choices"][0]["message"]["content"])
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        
        # Mock API key
        import scraper_structure
        original_key = scraper_structure.OPENAI_API_KEY
        scraper_structure.OPENAI_API_KEY = "test-key"
        
        try:
            prompt = "Extract program information from this text..."
            result = extract_program_openai(prompt)
            
            assert result is not None
            assert "programs" in result
            assert len(result["programs"]) > 0
            assert result["programs"][0]["program_name"] == "Medi-Cal"
        finally:
            scraper_structure.OPENAI_API_KEY = original_key
    
    def test_load_discovery(self, temp_data_dir, sample_discovery_results_json):
        """Test loading discovery results."""
        discovery_path = os.path.join(temp_data_dir, "discovery_results.json")
        os.makedirs(temp_data_dir, exist_ok=True)
        
        with open(discovery_path, 'w') as f:
            json.dump(sample_discovery_results_json, f)
        
        # Override DISCOVERY_PATH for test
        import scraper_structure
        original_path = scraper_structure.DISCOVERY_PATH
        scraper_structure.DISCOVERY_PATH = discovery_path
        
        try:
            discovery_map = load_discovery(discovery_path)
            assert len(discovery_map) > 0
            assert "Test County" in discovery_map
        finally:
            scraper_structure.DISCOVERY_PATH = original_path
    
    def test_critical_fields_missing_rate(self, sample_structured_program):
        """Test calculation of critical fields missing rate."""
        county = StructuredCounty(**sample_structured_program)
        
        # All fields present - should be 0.0
        rate = county.get_critical_fields_missing_rate()
        assert rate == 0.0
        
        # Test with missing fields
        county.programs[0].eligibility_requirements = "Not specified"
        rate = county.get_critical_fields_missing_rate()
        assert rate > 0.0
    
    def test_program_category_validation(self):
        """Test that program categories are valid."""
        valid_categories = [
            "Maternal Health", "Mental Health", "Substance Abuse",
            "Immunization", "Chronic Disease", "Emergency Services",
            "Primary Care", "Dental", "Vision", "Other"
        ]
        
        for category in valid_categories:
            program = StructuredProgram(
                program_name="Test",
                program_category=category,
                program_description="Test",
                target_population="Test",
                eligibility_requirements="Test",
                application_process="Test",
                required_documentation="Test",
                financial_assistance_available="Yes",
                program_website_url="https://test.com"
            )
            assert program.program_category == category
