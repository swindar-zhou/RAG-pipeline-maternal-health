"""
Pydantic schemas for Phase 1 (Discovery) outputs.
"""

from typing import List, Optional
from pydantic import BaseModel, HttpUrl, Field
from datetime import datetime


class ProgramLink(BaseModel):
    """A discovered program page link."""
    name: str = Field(..., description="Program name or link text")
    url: str = Field(..., description="Program page URL")
    link_text: str = Field(default="", description="Original link text from HTML")
    nav_path: str = Field(default="", description="Navigation path (e.g., 'Main → Health Dept → Maternal/Child')")
    score: Optional[float] = Field(default=None, description="Discovery score (if computed)")


class DiscoveryResult(BaseModel):
    """Discovery results for a single county."""
    county_name: str = Field(..., description="County name")
    county_url: str = Field(..., description="County homepage URL")
    health_dept_url: str = Field(default="", description="Health department URL if found")
    maternal_section_url: str = Field(default="", description="Maternal/child health section URL if found")
    programs: List[ProgramLink] = Field(default_factory=list, description="List of discovered program links")
    discovered_at: Optional[datetime] = Field(default=None, description="When discovery was run")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

