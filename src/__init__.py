"""
Core modules for the iTREDS healthcare data scraper.
Focused on maternal health programs per advisor feedback.
"""

from .config import (
    STATE_NAME,
    CALIFORNIA_COUNTIES,
    HEALTH_DEPT_URLS,
    MATERNAL_HEALTH_URLS,
    STATE_REFERENCE_URLS,
    DATA_COLLECTOR_NAME,
    SECTION_KEYWORDS,
    PROGRAM_KEYWORDS,
)
from .utils import save_to_csv
from .maternal_taxonomy import (
    MATERNAL_PROGRAM_TYPES,
    classify_program,
    is_maternal_health_program,
    is_non_maternal_program,
    score_maternal_relevance,
    generate_few_shot_examples,
    get_program_categories,
    get_all_keywords,
)

__all__ = [
    # Config
    "STATE_NAME",
    "CALIFORNIA_COUNTIES",
    "DATA_COLLECTOR_NAME",
    "HEALTH_DEPT_URLS",
    "MATERNAL_HEALTH_URLS",
    "STATE_REFERENCE_URLS",
    "SECTION_KEYWORDS",
    "PROGRAM_KEYWORDS",
    # Utils
    "save_to_csv",
    # Taxonomy
    "MATERNAL_PROGRAM_TYPES",
    "classify_program",
    "is_maternal_health_program",
    "is_non_maternal_program",
    "score_maternal_relevance",
    "generate_few_shot_examples",
    "get_program_categories",
    "get_all_keywords",
]

