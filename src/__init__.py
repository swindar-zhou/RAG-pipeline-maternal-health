"""
Core modules for the iTREDS healthcare data scraper.
Focused on maternal health programs.

Theoretical Framework:
- Social Determinants of Health (SDOH) - Solar & Irwin (2010)
- White House Blueprint for Addressing the Maternal Health Crisis (2022)
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
    # Core types
    MATERNAL_PROGRAM_TYPES,
    ProgramType,
    SDOHDomain,
    BlueprintGoal,
    # Classification functions
    classify_program,
    is_maternal_health_program,
    is_non_maternal_program,
    score_maternal_relevance,
    # Helper functions
    generate_few_shot_examples,
    get_program_categories,
    get_all_keywords,
    get_keywords_by_category,
    get_keywords_by_sdoh_domain,
    get_keywords_by_blueprint_goal,
    get_federal_programs,
    get_programs_by_sdoh_domain,
    get_programs_by_blueprint_goal,
    get_framework_summary,
)
from .llm_program_classifier import (
    ProgramClassification,
    LLMProgramClassifier,
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
    # Taxonomy - Core types
    "MATERNAL_PROGRAM_TYPES",
    "ProgramType",
    "SDOHDomain",
    "BlueprintGoal",
    # Taxonomy - Classification
    "classify_program",
    "is_maternal_health_program",
    "is_non_maternal_program",
    "score_maternal_relevance",
    # Taxonomy - Helpers
    "generate_few_shot_examples",
    "get_program_categories",
    "get_all_keywords",
    "get_keywords_by_category",
    "get_keywords_by_sdoh_domain",
    "get_keywords_by_blueprint_goal",
    "get_federal_programs",
    "get_programs_by_sdoh_domain",
    "get_programs_by_blueprint_goal",
    "get_framework_summary",
    # LLM classifier
    "ProgramClassification",
    "LLMProgramClassifier",
]

