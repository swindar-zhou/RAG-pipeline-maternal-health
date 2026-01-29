"""
End-to-end integration tests for the full pipeline.
"""

import os
import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from run_pipeline import run_phase_1, run_phase_2, run_phase_3
from src.utils import save_to_csv


class TestPipelineIntegration:
    """Test the full pipeline integration."""
    
    @patch('scraper_discovery.run_discovery_for_county')
    def test_phase1_integration(self, mock_discovery, temp_data_dir, sample_discovery_result):
        """Test Phase 1 integration."""
        mock_discovery.return_value = sample_discovery_result
        
        # Override data directory
        import run_pipeline
        original_data_dir = run_pipeline.DATA_DIR
        original_discovery_path = run_pipeline.DISCOVERY_PATH
        run_pipeline.DATA_DIR = temp_data_dir
        run_pipeline.DISCOVERY_PATH = os.path.join(temp_data_dir, "discovery_results.json")
        
        try:
            results = run_phase_1(["Test County"])
            
            assert len(results) == 1
            assert results[0]["county_name"] == "Test County"
            assert os.path.exists(run_pipeline.DISCOVERY_PATH)
            
            # Verify saved JSON
            with open(run_pipeline.DISCOVERY_PATH, 'r') as f:
                saved = json.load(f)
            assert "results" in saved
            assert len(saved["results"]) == 1
        finally:
            run_pipeline.DATA_DIR = original_data_dir
            run_pipeline.DISCOVERY_PATH = original_discovery_path
    
    @patch('scraper_extract.process_program_page')
    def test_phase2_integration(self, mock_extract, temp_data_dir, sample_discovery_result):
        """Test Phase 2 integration."""
        mock_extract.return_value = os.path.join(temp_data_dir, "raw", "test-county", "program-test.json")
        
        # Override directories
        import run_pipeline
        original_raw_dir = run_pipeline.RAW_DIR
        run_pipeline.RAW_DIR = os.path.join(temp_data_dir, "raw")
        os.makedirs(run_pipeline.RAW_DIR, exist_ok=True)
        
        try:
            discovery_results = [sample_discovery_result]
            run_phase_2(discovery_results)
            
            # Verify extraction was called
            assert mock_extract.called
        finally:
            run_pipeline.RAW_DIR = original_raw_dir
    
    @patch('scraper_structure.extract_program_openai')
    @patch('scraper_structure.load_discovery')
    def test_phase3_integration(self, mock_load_discovery, mock_extract, 
                                temp_data_dir, sample_structured_program, sample_discovery_result):
        """Test Phase 3 integration."""
        # Mock dependencies
        mock_load_discovery.return_value = {
            "Test County": sample_discovery_result
        }
        mock_extract.return_value = sample_structured_program
        
        # Override directories
        import run_pipeline
        import scraper_structure
        original_raw_dir = scraper_structure.RAW_DIR
        original_structured_dir = os.path.join("data", "structured")
        
        # Create test raw files
        test_raw_dir = os.path.join(temp_data_dir, "raw", "test-county")
        os.makedirs(test_raw_dir, exist_ok=True)
        
        test_raw_file = os.path.join(test_raw_dir, "program-test.json")
        with open(test_raw_file, 'w') as f:
            json.dump({
                "county": "Test County",
                "page_url": "https://test-county.gov/health/medi-cal",
                "text": "Medi-Cal program information...",
                "contacts": {"phones": [], "emails": []},
                "pdf_links": []
            }, f)
        
        scraper_structure.RAW_DIR = os.path.join(temp_data_dir, "raw")
        
        try:
            discovery_results = [sample_discovery_result]
            run_phase_3(discovery_results)
            
            # Verify extraction was called
            assert mock_extract.called
        finally:
            scraper_structure.RAW_DIR = original_raw_dir
    
    def test_csv_output_format(self, temp_data_dir, sample_structured_program):
        """Test that CSV output has correct format."""
        csv_path = os.path.join(temp_data_dir, "test_output.csv")
        
        save_to_csv([sample_structured_program], csv_path)
        
        assert os.path.exists(csv_path)
        
        # Verify CSV structure
        import csv
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            assert len(rows) > 0
            required_fields = [
                'State', 'County_Name', 'Program_Name', 'Program_Category',
                'Eligibility_Requirements', 'Application_Process'
            ]
            for field in required_fields:
                assert field in rows[0]
    
    @patch('run_pipeline.run_phase_1')
    @patch('run_pipeline.run_phase_2')
    @patch('run_pipeline.run_phase_3')
    def test_full_pipeline_flow(self, mock_phase3, mock_phase2, mock_phase1):
        """Test that full pipeline calls all phases in order."""
        from run_pipeline import main
        
        mock_phase1.return_value = [{"county_name": "Test"}]
        
        main()
        
        # Verify all phases were called
        assert mock_phase1.called
        assert mock_phase2.called
        assert mock_phase3.called
        
        # Verify call order
        call_order = [call[0] for call in [mock_phase1, mock_phase2, mock_phase3] if call.called]
        assert len(call_order) == 3
