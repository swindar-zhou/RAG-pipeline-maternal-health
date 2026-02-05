"""
Maternal Health Program Taxonomy

Based on state-level reference pages (California CDPH, Florida DOH) as recommended
by advisor for training/learning what constitutes a maternal health program.

Reference sources:
- California: https://www.cdph.ca.gov/Programs/CFH/DMCAH/Pages/Domains/Maternal-Health.aspx
- Florida: https://www.floridahealth.gov/individual-family-health/womens-health/pregnancy/
- Florida WIC: https://www.floridahealth.gov/individual-family-health/womens-health/wic/

This taxonomy serves three purposes:
1. Improved discovery scoring (keyword matching)
2. Program classification (categorizing discovered programs)
3. Validation (checking if extracted programs are maternal health related)
"""

from typing import List, Dict, Optional
from dataclasses import dataclass, field


@dataclass
class ProgramType:
    """A known type of maternal health program."""
    name: str
    category: str
    description: str
    keywords: List[str]  # Keywords that indicate this program type
    federal_program: bool = False  # Is this a federal/state-mandated program?
    examples: List[str] = field(default_factory=list)  # Example program names


# =============================================================================
# MATERNAL HEALTH PROGRAM TAXONOMY
# Based on California CDPH MCAH and Florida DOH maternal health pages
# =============================================================================

MATERNAL_PROGRAM_TYPES: List[ProgramType] = [
    # ---------------------------------------------------------------------
    # NUTRITION PROGRAMS
    # ---------------------------------------------------------------------
    ProgramType(
        name="WIC",
        category="Nutrition",
        description="Women, Infants, and Children - supplemental nutrition program providing "
                    "food, nutrition education, and breastfeeding support",
        keywords=[
            "wic", "women infants children", "women, infants, and children",
            "supplemental nutrition", "wic program", "wic clinic",
            "wic benefits", "wic foods", "wic eligibility",
        ],
        federal_program=True,
        examples=["WIC Program", "WIC Nutrition Services", "WIC Clinic"],
    ),
    
    # ---------------------------------------------------------------------
    # HOME VISITING PROGRAMS
    # ---------------------------------------------------------------------
    ProgramType(
        name="Nurse-Family Partnership",
        category="Home Visiting",
        description="Evidence-based nurse home visiting program for first-time, "
                    "low-income mothers from pregnancy through child's second birthday",
        keywords=[
            "nurse-family partnership", "nfp", "nurse family partnership",
            "nurse home visiting", "first-time mothers", "nurse home visits",
        ],
        federal_program=True,
        examples=["Nurse-Family Partnership", "NFP Program"],
    ),
    ProgramType(
        name="Healthy Families America",
        category="Home Visiting",
        description="Home visiting program for new and expectant families at-risk "
                    "for child maltreatment",
        keywords=[
            "healthy families", "healthy families america", "hfa",
            "family support home visiting",
        ],
        federal_program=True,
        examples=["Healthy Families America", "Healthy Families Program"],
    ),
    ProgramType(
        name="Parents as Teachers",
        category="Home Visiting",
        description="Home visiting program focused on parent education and "
                    "child development from pregnancy through kindergarten",
        keywords=[
            "parents as teachers", "pat program", "parent education",
            "parent-child interaction",
        ],
        federal_program=True,
        examples=["Parents as Teachers", "PAT Program"],
    ),
    ProgramType(
        name="MIECHV",
        category="Home Visiting",
        description="Maternal, Infant, and Early Childhood Home Visiting - "
                    "federal program supporting voluntary home visiting",
        keywords=[
            "miechv", "maternal infant early childhood home visiting",
            "home visiting program", "early childhood home visiting",
        ],
        federal_program=True,
        examples=["MIECHV Program", "Home Visiting Initiative"],
    ),
    ProgramType(
        name="California Home Visiting Program",
        category="Home Visiting",
        description="California's coordinated home visiting program for "
                    "at-risk pregnant women and families",
        keywords=[
            "california home visiting", "chvp", "ca home visiting",
            "calworks home visiting",
        ],
        federal_program=False,
        examples=["CHVP", "California Home Visiting Program"],
    ),
    
    # ---------------------------------------------------------------------
    # PERINATAL/PRENATAL PROGRAMS
    # ---------------------------------------------------------------------
    ProgramType(
        name="Comprehensive Perinatal Services Program",
        category="Perinatal Care",
        description="California program providing enhanced prenatal and "
                    "postpartum care for Medi-Cal eligible women",
        keywords=[
            "comprehensive perinatal services", "cpsp", "perinatal services program",
            "enhanced prenatal care", "medi-cal prenatal",
        ],
        federal_program=False,
        examples=["CPSP", "Comprehensive Perinatal Services Program"],
    ),
    ProgramType(
        name="Prenatal Care Programs",
        category="Perinatal Care",
        description="General prenatal care and pregnancy services",
        keywords=[
            "prenatal care", "prenatal services", "prenatal program",
            "pregnancy care", "pregnancy services", "prenatal clinic",
            "prenatal health", "maternity care", "obstetric care",
            # Also match perinatal (covers both prenatal and postnatal)
            "perinatal", "perinatal care", "perinatal network", "perinatal_care",
            "perinatal services", "perinatal program", "perinatal health",
            "perinatal outreach", "pcn",  # Perinatal Care Network
        ],
        federal_program=False,
        examples=["Prenatal Care Program", "Pregnancy Services", "Perinatal Care Network"],
    ),
    ProgramType(
        name="Postpartum Support",
        category="Perinatal Care",
        description="Services for mothers after childbirth including "
                    "physical and mental health support",
        keywords=[
            "postpartum", "postpartum support", "postpartum care",
            "postpartum depression", "postpartum services",
            "after birth", "new mother support",
        ],
        federal_program=False,
        examples=["Postpartum Support Program", "New Mother Services"],
    ),
    
    # ---------------------------------------------------------------------
    # INFANT HEALTH EQUITY PROGRAMS
    # ---------------------------------------------------------------------
    ProgramType(
        name="Black Infant Health",
        category="Health Equity",
        description="California program addressing African American infant "
                    "mortality through group education and case management",
        keywords=[
            "black infant health", "bih", "african american infant",
            "black maternal health", "infant mortality reduction",
            "racial equity maternal", "birth equity",
        ],
        federal_program=False,
        examples=["Black Infant Health Program", "BIH"],
    ),
    ProgramType(
        name="Healthy Start",
        category="Health Equity",
        description="Federal program to reduce infant mortality and improve "
                    "perinatal outcomes in high-risk communities",
        keywords=[
            "healthy start", "infant mortality", "high-risk communities",
            "community health workers", "perinatal outcomes",
        ],
        federal_program=True,
        examples=["Healthy Start Initiative", "Healthy Start Program"],
    ),
    ProgramType(
        name="Perinatal Equity Initiative",
        category="Health Equity",
        description="Programs focused on reducing racial disparities in "
                    "maternal and infant health outcomes",
        keywords=[
            "perinatal equity", "birth equity", "maternal equity",
            "racial disparities birth", "health equity maternal",
        ],
        federal_program=False,
        examples=["Perinatal Equity Initiative", "Birth Equity Program"],
    ),
    
    # ---------------------------------------------------------------------
    # BREASTFEEDING/LACTATION
    # ---------------------------------------------------------------------
    ProgramType(
        name="Breastfeeding Support",
        category="Breastfeeding",
        description="Programs providing lactation support, education, and "
                    "breastfeeding resources",
        keywords=[
            "breastfeeding", "lactation", "lactation support",
            "lactation consultant", "breastfeeding education",
            "nursing mother", "breast pump", "milk bank",
        ],
        federal_program=False,
        examples=["Breastfeeding Support Program", "Lactation Services"],
    ),
    
    # ---------------------------------------------------------------------
    # ADOLESCENT/TEEN PROGRAMS
    # ---------------------------------------------------------------------
    ProgramType(
        name="Adolescent Family Life Program",
        category="Adolescent Health",
        description="California program providing comprehensive services to "
                    "pregnant and parenting teens",
        keywords=[
            "adolescent family life", "aflp", "teen pregnancy",
            "pregnant teens", "parenting teens", "adolescent pregnancy",
            "teen parent", "young parent",
        ],
        federal_program=False,
        examples=["AFLP", "Adolescent Family Life Program", "Teen Parent Program"],
    ),
    
    # ---------------------------------------------------------------------
    # FAMILY PLANNING
    # ---------------------------------------------------------------------
    ProgramType(
        name="Family Planning",
        category="Family Planning",
        description="Reproductive health and family planning services",
        keywords=[
            "family planning", "reproductive health", "birth control",
            "contraception", "family planning services", "title x",
            "planned parenthood",
        ],
        federal_program=False,
        examples=["Family Planning Program", "Reproductive Health Services"],
    ),
    
    # ---------------------------------------------------------------------
    # TITLE V / MCH BLOCK GRANT
    # ---------------------------------------------------------------------
    ProgramType(
        name="Title V MCH",
        category="Maternal Child Health",
        description="Federal Title V Maternal and Child Health Block Grant "
                    "programs and services",
        keywords=[
            "title v", "title five", "mch block grant",
            "maternal child health block", "mch services",
            "mcah", "maternal child adolescent health",
        ],
        federal_program=True,
        examples=["Title V Program", "MCH Services", "MCAH Program"],
    ),
    
    # ---------------------------------------------------------------------
    # BIRTH SUPPORT SERVICES
    # ---------------------------------------------------------------------
    ProgramType(
        name="Doula Services",
        category="Birth Support",
        description="Community health worker/doula support during pregnancy, "
                    "birth, and postpartum",
        keywords=[
            "doula", "birth doula", "community doula", "doula services",
            "birth support", "labor support", "birth companion",
        ],
        federal_program=False,
        examples=["Doula Program", "Community Doula Services"],
    ),
    ProgramType(
        name="Midwifery Services",
        category="Birth Support",
        description="Midwife-led prenatal, birth, and postpartum care",
        keywords=[
            "midwife", "midwifery", "certified nurse midwife",
            "cnm", "licensed midwife", "birth center",
        ],
        federal_program=False,
        examples=["Midwifery Program", "Birth Center"],
    ),
    
    # ---------------------------------------------------------------------
    # FIRST 5 / EARLY CHILDHOOD
    # ---------------------------------------------------------------------
    ProgramType(
        name="First 5",
        category="Early Childhood",
        description="California First 5 programs supporting children ages 0-5 "
                    "and their families",
        keywords=[
            "first 5", "first five", "proposition 10", "prop 10",
            "children ages 0-5", "early childhood", "kindergarten readiness",
        ],
        federal_program=False,
        examples=["First 5 California", "First 5 LA", "First 5 Commission"],
    ),
]


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_all_keywords() -> List[str]:
    """Get all keywords from all program types for discovery scoring."""
    keywords = []
    for pt in MATERNAL_PROGRAM_TYPES:
        keywords.extend(pt.keywords)
    return list(set(keywords))


def get_keywords_by_category(category: str) -> List[str]:
    """Get keywords for a specific category."""
    keywords = []
    for pt in MATERNAL_PROGRAM_TYPES:
        if pt.category.lower() == category.lower():
            keywords.extend(pt.keywords)
    return list(set(keywords))


def classify_program(text: str, url: str = "") -> Optional[ProgramType]:
    """
    Classify a program based on its text and URL.
    Returns the best matching ProgramType or None.
    """
    text_lower = text.lower()
    url_lower = url.lower()
    combined = text_lower + " " + url_lower
    
    best_match = None
    best_score = 0
    
    for pt in MATERNAL_PROGRAM_TYPES:
        score = 0
        for keyword in pt.keywords:
            if keyword in combined:
                # Longer keywords are more specific, give them more weight
                score += len(keyword.split())
        
        if score > best_score:
            best_score = score
            best_match = pt
    
    # Only return if we have a meaningful match (at least one keyword)
    return best_match if best_score > 0 else None


def is_maternal_health_program(text: str, url: str = "") -> bool:
    """
    Determine if a program is maternal health related.
    Uses the taxonomy to make this determination.
    """
    return classify_program(text, url) is not None


def get_program_categories() -> List[str]:
    """Get all unique program categories."""
    return list(set(pt.category for pt in MATERNAL_PROGRAM_TYPES))


def get_federal_programs() -> List[ProgramType]:
    """Get all federal/state-mandated programs."""
    return [pt for pt in MATERNAL_PROGRAM_TYPES if pt.federal_program]


def score_maternal_relevance(text: str, url: str = "") -> float:
    """
    Score how relevant a page/program is to maternal health (0.0 to 1.0).
    Higher score = more likely to be maternal health related.
    """
    text_lower = text.lower()
    url_lower = url.lower()
    combined = text_lower + " " + url_lower
    
    total_keywords = 0
    matched_keywords = 0
    
    for pt in MATERNAL_PROGRAM_TYPES:
        for keyword in pt.keywords:
            total_keywords += 1
            if keyword in combined:
                matched_keywords += 1
    
    if total_keywords == 0:
        return 0.0
    
    # Cap at 1.0 (matching many keywords doesn't mean > 100% relevant)
    return min(1.0, matched_keywords / 5)  # Normalize: 5+ matches = 1.0


def generate_few_shot_examples() -> str:
    """
    Generate few-shot examples for LLM prompts based on the taxonomy.
    This implements the advisor's suggestion of using state programs as training data.
    """
    examples = []
    
    # Select representative examples from each category
    categories_shown = set()
    for pt in MATERNAL_PROGRAM_TYPES:
        if pt.category in categories_shown:
            continue
        categories_shown.add(pt.category)
        
        examples.append(f"""
Program: {pt.name}
Category: {pt.category}
Description: {pt.description}
Is Maternal Health Program: Yes
""".strip())
    
    return "\n\n".join(examples)


# =============================================================================
# NON-MATERNAL PROGRAMS (for negative examples / exclusion)
# =============================================================================

NON_MATERNAL_KEYWORDS = [
    # General health (not maternal-specific)
    "medi-cal", "medicaid", "medicare", "calfresh", "food stamps", "snap",
    # Aging services
    "senior", "elderly", "aging", "older adults", "adult protective", "elder abuse",
    # Mental health (general)
    "behavioral health", "substance abuse", "addiction", "drug treatment",
    # Housing
    "housing", "homeless", "shelter",
    # General social services
    "child protective", "foster care", "adoption", "calworks", "tanf",
    # Veterans
    "veteran", "va services",
    # Vital records / administrative (not programs)
    "birth certificate", "death certificate", "marriage certificate",
    "vital records", "recorder-clerk", "vital_records",
    # Other non-maternal services
    "tobacco", "tobacco control", "immunization", "flu shot", "vaccination",
    "dental", "vision", "animal", "pet", "rabies",
    "environmental health", "food safety", "restaurant inspection",
    "public records", "foia", "customer service", "call center",
    "employment", "job", "career", "workforce",
]


def is_non_maternal_program(text: str, url: str = "") -> bool:
    """
    Check if a program is clearly NOT maternal health (general health/social services).
    Per advisor feedback: keep maternal health focused, don't mix with broader programs.
    """
    combined = (text + " " + url).lower()
    
    # Check for non-maternal keywords
    non_maternal_matches = sum(1 for kw in NON_MATERNAL_KEYWORDS if kw in combined)
    
    # Check for maternal keywords
    maternal_match = is_maternal_health_program(text, url)
    
    # If has maternal keywords, it's likely maternal even if has some general terms
    if maternal_match:
        return False
    
    # If no maternal keywords but has non-maternal keywords, it's not maternal
    return non_maternal_matches > 0


# =============================================================================
# PRINT TAXONOMY SUMMARY (for debugging/review)
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("MATERNAL HEALTH PROGRAM TAXONOMY")
    print("=" * 60)
    print(f"\nTotal program types: {len(MATERNAL_PROGRAM_TYPES)}")
    print(f"Categories: {', '.join(get_program_categories())}")
    print(f"Federal programs: {len(get_federal_programs())}")
    print(f"Total keywords: {len(get_all_keywords())}")
    
    print("\n" + "-" * 60)
    print("PROGRAM TYPES BY CATEGORY")
    print("-" * 60)
    
    for category in sorted(get_program_categories()):
        programs = [pt for pt in MATERNAL_PROGRAM_TYPES if pt.category == category]
        print(f"\n{category}:")
        for pt in programs:
            federal = " [Federal]" if pt.federal_program else ""
            print(f"  - {pt.name}{federal}")
    
    print("\n" + "-" * 60)
    print("EXAMPLE CLASSIFICATIONS")
    print("-" * 60)
    
    test_cases = [
        ("WIC Nutrition Program", "/wic/"),
        ("Medi-Cal Health Coverage", "/medi-cal/"),
        ("Black Infant Health Support", "/bih/"),
        ("Senior Services", "/aging/"),
        ("Prenatal Care Clinic", "/prenatal/"),
        ("CalFresh Food Assistance", "/calfresh/"),
        ("Nurse-Family Partnership", "/nfp/"),
    ]
    
    for text, url in test_cases:
        is_maternal = is_maternal_health_program(text, url)
        is_excluded = is_non_maternal_program(text, url)
        classification = classify_program(text, url)
        cat = classification.category if classification else "N/A"
        print(f"  '{text}': maternal={is_maternal}, excluded={is_excluded}, category={cat}")
