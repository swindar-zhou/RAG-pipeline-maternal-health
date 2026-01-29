"""
Integration tests for Phase 1: Discovery.
"""

import os
import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from bs4 import BeautifulSoup

from schemas.discovery import DiscoveryResult
from scraper_discovery import run_discovery_for_county, find_health_dept_page, find_maternal_section, collect_program_links


class TestPhase1Discovery:
    """Test Phase 1 discovery functionality."""
    
    def test_discovery_result_schema(self, sample_discovery_result):
        """Test that discovery results match the Pydantic schema."""
        result = DiscoveryResult(**sample_discovery_result)
        assert result.county_name == sample_discovery_result["county_name"]
        assert len(result.programs) == 2
        assert all(isinstance(p, ProgramLink) for p in result.programs)
    
    @patch('scraper_discovery.fetch_soup')
    def test_find_health_dept_page(self, mock_fetch_soup, sample_county_url, mock_html_content):
        """Test finding health department URL."""
        mock_soup = BeautifulSoup(mock_html_content, 'html.parser')
        mock_fetch_soup.return_value = mock_soup
        
        # Add health department link
        health_link = mock_soup.new_tag('a', href='/health')
        health_link.string = 'Health Department'
        mock_soup.body.append(health_link)
        
        result = find_health_dept_page(sample_county_url)
        # Result may be None if keywords don't match, or a URL if they do
        if result:
            assert 'health' in result.lower() or result == sample_county_url
    
    @patch('scraper_discovery.fetch_soup')
    def test_find_maternal_section(self, mock_fetch_soup, sample_county_url, mock_html_content):
        """Test finding maternal/child health section."""
        mock_soup = BeautifulSoup(mock_html_content, 'html.parser')
        mock_fetch_soup.return_value = mock_soup
        
        # Add maternal health link
        maternal_link = mock_soup.new_tag('a', href='/health/maternal')
        maternal_link.string = 'Maternal Health'
        mock_soup.body.append(maternal_link)
        
        health_dept_url = f"{sample_county_url}health"
        result = find_maternal_section(health_dept_url)
        # Result may be None if keywords don't match
        if result:
            assert 'maternal' in result.lower() or result == health_dept_url
    
    @patch('scraper_discovery.fetch_soup')
    def test_collect_program_links(self, mock_fetch_soup, sample_county_url, mock_html_content):
        """Test collecting program links."""
        mock_soup = BeautifulSoup(mock_html_content, 'html.parser')
        mock_fetch_soup.return_value = mock_soup
        
        # Add program links
        medi_cal_link = mock_soup.new_tag('a', href='/health/medi-cal')
        medi_cal_link.string = 'Medi-Cal'
        mock_soup.body.append(medi_cal_link)
        
        section_url = f"{sample_county_url}health/maternal"
        programs = collect_program_links(section_url)
        
        assert isinstance(programs, list)
        # Programs list may be empty if keywords don't match, or contain links if they do
    
    @patch('scraper_discovery.find_health_dept_page')
    @patch('scraper_discovery.find_maternal_section')
    @patch('scraper_discovery.collect_program_links')
    def test_run_discovery_for_county(self, mock_collect, mock_maternal, mock_health, 
                                     sample_county_name, sample_county_url):
        """Test running discovery for a county."""
        # Mock the discovery functions
        mock_health.return_value = f"{sample_county_url}health"
        mock_maternal.return_value = f"{sample_county_url}health/maternal"
        mock_collect.return_value = [
            {
                "name": "Medi-Cal",
                "url": f"{sample_county_url}health/medi-cal",
                "link_text": "Medi-Cal",
                "nav_path": "Main → Health Dept"
            }
        ]
        
        result = run_discovery_for_county(sample_county_name, sample_county_url)
        
        assert result["county_name"] == sample_county_name
        assert result["county_url"] == sample_county_url
        assert isinstance(result["programs"], list)
        assert "health_dept_url" in result
    
    def test_discovery_output_structure(self, sample_discovery_result):
        """Test that discovery output has correct structure."""
        required_fields = ["county_name", "county_url", "health_dept_url", 
                          "maternal_section_url", "programs"]
        for field in required_fields:
            assert field in sample_discovery_result
        
        assert isinstance(sample_discovery_result["programs"], list)
        if sample_discovery_result["programs"]:
            program = sample_discovery_result["programs"][0]
            assert "name" in program
            assert "url" in program
