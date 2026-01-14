"""
Evaluation metrics for the 3-phase pipeline.
"""

from typing import List, Dict, Set, Optional
from dataclasses import dataclass
from urllib.parse import urlparse

from schemas.discovery import DiscoveryResult, ProgramLink
from schemas.extraction import RawPage, Contacts
from schemas.structured import StructuredCounty, StructuredProgram
from eval.gold_schema import GoldCounty, GoldProgram


@dataclass
class Phase1Metrics:
    """Metrics for Phase 1 (Discovery)."""
    recall_at_10: float  # % of gold programs found in top 10 links
    recall_at_20: float  # % of gold programs found in top 20 links
    pages_crawled: int   # Number of pages crawled per county
    programs_found: int  # Total programs discovered
    
    def to_dict(self) -> Dict:
        return {
            "recall_at_10": self.recall_at_10,
            "recall_at_20": self.recall_at_20,
            "pages_crawled": self.pages_crawled,
            "programs_found": self.programs_found,
        }


@dataclass
class Phase2Metrics:
    """Metrics for Phase 2 (Extraction)."""
    contact_precision: float  # Precision of phone/email extraction
    contact_recall: float      # Recall of phone/email extraction
    pdf_precision: float       # Precision of PDF detection
    pdf_recall: float         # Recall of PDF detection
    
    def to_dict(self) -> Dict:
        return {
            "contact_precision": self.contact_precision,
            "contact_recall": self.contact_recall,
            "pdf_precision": self.pdf_precision,
            "pdf_recall": self.pdf_recall,
        }


@dataclass
class Phase3Metrics:
    """Metrics for Phase 3 (Structuring)."""
    schema_validity_rate: float           # % of programs that pass Pydantic validation
    critical_field_missing_rate: float    # % of programs missing eligibility/apply/contact
    field_exact_match_rate: float        # % of fields that exactly match gold labels
    
    def to_dict(self) -> Dict:
        return {
            "schema_validity_rate": self.schema_validity_rate,
            "critical_field_missing_rate": self.critical_field_missing_rate,
            "field_exact_match_rate": self.field_exact_match_rate,
        }


@dataclass
class CountyMetrics:
    """All metrics for a single county."""
    county_name: str
    phase1: Phase1Metrics
    phase2: Phase2Metrics
    phase3: Phase3Metrics
    
    def to_dict(self) -> Dict:
        return {
            "county_name": self.county_name,
            "phase1": self.phase1.to_dict(),
            "phase2": self.phase2.to_dict(),
            "phase3": self.phase3.to_dict(),
        }


def normalize_url(url: str) -> str:
    """Normalize URL for comparison (remove trailing slashes, lowercase)."""
    url = url.rstrip('/').lower()
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip('/')


def calculate_phase1_metrics(
    discovery: DiscoveryResult,
    gold: GoldCounty,
    top_k: int = 20
) -> Phase1Metrics:
    """Calculate Phase 1 metrics: Recall@K."""
    gold_urls = {normalize_url(p.program_url) for p in gold.programs}
    
    if not gold_urls:
        return Phase1Metrics(recall_at_10=0.0, recall_at_20=0.0, pages_crawled=0, programs_found=len(discovery.programs))
    
    discovered_urls = [normalize_url(p.url) for p in discovery.programs]
    
    # Recall@10
    top_10_urls = set(discovered_urls[:10])
    recall_at_10 = len(gold_urls & top_10_urls) / len(gold_urls) if gold_urls else 0.0
    
    # Recall@20
    top_20_urls = set(discovered_urls[:top_k])
    recall_at_20 = len(gold_urls & top_20_urls) / len(gold_urls) if gold_urls else 0.0
    
    # Estimate pages crawled (discovery.programs length is a proxy)
    pages_crawled = len(discovery.programs)
    
    return Phase1Metrics(
        recall_at_10=recall_at_10,
        recall_at_20=recall_at_20,
        pages_crawled=pages_crawled,
        programs_found=len(discovery.programs)
    )


def calculate_phase2_metrics(
    raw_pages: List[RawPage],
    gold: GoldCounty
) -> Phase2Metrics:
    """Calculate Phase 2 metrics: Contact and PDF extraction precision/recall."""
    # Build gold sets
    gold_phones: Set[str] = set()
    gold_emails: Set[str] = set()
    gold_pdfs: Set[str] = set()
    
    for program in gold.programs:
        if program.contact_phone:
            gold_phones.add(program.contact_phone.replace('-', '').replace(' ', '').replace('(', '').replace(')', ''))
        if program.contact_email:
            gold_emails.add(program.contact_email.lower())
        gold_pdfs.update({normalize_url(pdf) for pdf in program.pdf_links})
    
    # Build extracted sets
    extracted_phones: Set[str] = set()
    extracted_emails: Set[str] = set()
    extracted_pdfs: Set[str] = set()
    
    for page in raw_pages:
        for phone in page.contacts.phones:
            extracted_phones.add(phone.replace('-', '').replace(' ', '').replace('(', '').replace(')', ''))
        extracted_emails.update({e.lower() for e in page.contacts.emails})
        extracted_pdfs.update({normalize_url(pdf) for pdf in page.pdf_links})
    
    # Contact precision/recall
    contact_tp = len((gold_phones | gold_emails) & (extracted_phones | extracted_emails))
    contact_fp = len((extracted_phones | extracted_emails) - (gold_phones | gold_emails))
    contact_fn = len((gold_phones | gold_emails) - (extracted_phones | extracted_emails))
    
    contact_precision = contact_tp / (contact_tp + contact_fp) if (contact_tp + contact_fp) > 0 else 0.0
    contact_recall = contact_tp / (contact_tp + contact_fn) if (contact_tp + contact_fn) > 0 else 0.0
    
    # PDF precision/recall
    pdf_tp = len(gold_pdfs & extracted_pdfs)
    pdf_fp = len(extracted_pdfs - gold_pdfs)
    pdf_fn = len(gold_pdfs - extracted_pdfs)
    
    pdf_precision = pdf_tp / (pdf_tp + pdf_fp) if (pdf_tp + pdf_fp) > 0 else 0.0
    pdf_recall = pdf_tp / (pdf_tp + pdf_fn) if (pdf_tp + pdf_fn) > 0 else 0.0
    
    return Phase2Metrics(
        contact_precision=contact_precision,
        contact_recall=contact_recall,
        pdf_precision=pdf_precision,
        pdf_recall=pdf_recall
    )


def calculate_phase3_metrics(
    structured: StructuredCounty,
    gold: GoldCounty
) -> Phase3Metrics:
    """Calculate Phase 3 metrics: Schema validity and field matching."""
    # Schema validity (all programs should pass Pydantic validation if we got here)
    schema_validity_rate = 1.0 if structured.programs else 0.0
    
    # Critical field missing rate
    critical_missing_rate = structured.get_critical_fields_missing_rate()
    
    # Field exact match rate (compare structured programs to gold)
    if not structured.programs or not gold.programs:
        field_exact_match_rate = 0.0
    else:
        # Match programs by URL
        gold_by_url = {normalize_url(p.program_url): p for p in gold.programs}
        matched_programs = []
        
        for prog in structured.programs:
            prog_url = normalize_url(prog.program_website_url)
            if prog_url in gold_by_url:
                matched_programs.append((prog, gold_by_url[prog_url]))
        
        if not matched_programs:
            field_exact_match_rate = 0.0
        else:
            total_fields = 0
            exact_matches = 0
            
            for struct_prog, gold_prog in matched_programs:
                # Compare key fields
                fields_to_check = [
                    ("program_name", struct_prog.program_name, gold_prog.program_name),
                    ("eligibility_requirements", struct_prog.eligibility_requirements, gold_prog.eligibility_requirements or ""),
                    ("application_process", struct_prog.application_process, gold_prog.application_process or ""),
                ]
                
                for field_name, struct_val, gold_val in fields_to_check:
                    total_fields += 1
                    if struct_val.lower().strip() == gold_val.lower().strip():
                        exact_matches += 1
            
            field_exact_match_rate = exact_matches / total_fields if total_fields > 0 else 0.0
    
    return Phase3Metrics(
        schema_validity_rate=schema_validity_rate,
        critical_field_missing_rate=critical_missing_rate,
        field_exact_match_rate=field_exact_match_rate
    )

