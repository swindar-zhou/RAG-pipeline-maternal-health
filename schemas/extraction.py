"""
Pydantic schemas for Phase 2 (Deep Extraction) outputs.
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class Contacts(BaseModel):
    """Contact information extracted from a page."""
    phones: List[str] = Field(default_factory=list, description="Phone numbers found")
    emails: List[str] = Field(default_factory=list, description="Email addresses found")


class RawPage(BaseModel):
    """Raw page content extracted from a program page."""
    county: str = Field(..., description="County name")
    page_url: str = Field(..., description="URL of the page")
    link_text: str = Field(default="", description="Link text that led to this page")
    program_name_guess: str = Field(default="", description="Guessed program name")
    nav_path: str = Field(default="", description="Navigation path")
    scraped_at: datetime = Field(default_factory=datetime.now, description="When page was scraped")
    text: str = Field(..., description="Main text content (cleaned HTML)")
    contacts: Contacts = Field(default_factory=Contacts, description="Extracted contact information")
    pdf_links: List[str] = Field(default_factory=list, description="PDF links found on page")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

