"""
Gold dataset schema for evaluation.
Each entry represents a ground-truth program page that should be discovered and extracted.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class GoldProgram(BaseModel):
    """Ground truth for a single program."""
    program_name: str = Field(..., description="Official program name")
    program_url: str = Field(..., description="Official program page URL")
    category: str = Field(..., description="Program category")
    description: Optional[str] = Field(None, description="Program description")
    target_population: Optional[str] = Field(None, description="Target population")
    eligibility_requirements: Optional[str] = Field(None, description="Eligibility requirements")
    application_process: Optional[str] = Field(None, description="How to apply")
    contact_phone: Optional[str] = Field(None, description="Contact phone number")
    contact_email: Optional[str] = Field(None, description="Contact email")
    pdf_links: List[str] = Field(default_factory=list, description="Expected PDF links (application/eligibility forms)")


class GoldCounty(BaseModel):
    """Ground truth for a county."""
    county_name: str = Field(..., description="County name")
    county_url: str = Field(..., description="County homepage URL")
    programs: List[GoldProgram] = Field(..., description="List of programs that should be discovered")

