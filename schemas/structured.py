"""
Pydantic schemas for Phase 3 (LLM Structuring) outputs.
"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field, HttpUrl, validator


class StructuredProgram(BaseModel):
    """A structured healthcare program entry."""
    program_name: str = Field(..., description="Program name")
    program_category: str = Field(..., description="Maternal program category")
    program_description: str = Field(..., description="Brief description")
    target_population: str = Field(..., description="Who the program serves")
    eligibility_requirements: str = Field(..., description="Eligibility requirements or 'Not specified'")
    application_process: str = Field(..., description="How to apply or 'Not specified'")
    required_documentation: str = Field(..., description="Required documents or 'Not specified'")
    financial_assistance_available: Literal["Yes", "No", "Unknown"] = Field(..., description="Financial assistance availability")
    program_website_url: str = Field(..., description="Program URL")
    
    @validator('eligibility_requirements', 'application_process', 'required_documentation')
    def validate_not_specified(cls, v):
        """Allow 'Not specified' or 'Not found' as valid values."""
        if v in ["Not specified", "Not found", ""]:
            return "Not specified"
        return v

    @validator("program_category")
    def normalize_program_category(cls, v):
        """Normalize category string for downstream evaluation."""
        value = (v or "").strip()
        return value if value else "Other"


class StructuredCounty(BaseModel):
    """Structured data for a county with all programs."""
    county_name: str = Field(..., description="County name")
    state: str = Field(default="California", description="State name")
    county_website_url: str = Field(..., description="County homepage URL")
    health_department_name: str = Field(..., description="Health department name or 'Not found'")
    health_department_contact_email: str = Field(..., description="Health department email or 'Not found'")
    health_department_contact_phone: str = Field(..., description="Health department phone or 'Not found'")
    programs: List[StructuredProgram] = Field(default_factory=list, description="List of structured programs")
    notes: str = Field(default="", description="Data quality notes")
    
    def get_critical_fields_missing_rate(self) -> float:
        """Calculate the rate of programs missing critical fields."""
        if not self.programs:
            return 1.0
        
        missing_count = 0
        for program in self.programs:
            critical_missing = (
                program.eligibility_requirements in ["Not specified", "Not found", ""] or
                program.application_process in ["Not specified", "Not found", ""]
            )
            if critical_missing:
                missing_count += 1
        
        return missing_count / len(self.programs)

