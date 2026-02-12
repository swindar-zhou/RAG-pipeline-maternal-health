"""
Maternal Health Program Taxonomy

Theoretical Framework:
This taxonomy is grounded in the Social Determinants of Health (SDOH) framework
and aligned with the White House Blueprint for Addressing the Maternal Health Crisis (2022).

Key References:
- Braveman, P., Egerter, S., & Williams, D. R. (2011). The social determinants of health: 
  coming of age. Annual Review of Public Health, 32(1), 381-398.
- Braveman, P., & Gottlieb, L. (2014). The social determinants of health: it's time to 
  consider the causes of the causes. Public Health Reports, 129(1_suppl2), 19-31.
- Solar, O., & Irwin, A. (2010). A conceptual framework for action on the social 
  determinants of health. WHO Document Production Services.
- White House Blueprint for Addressing the Maternal Health Crisis (June 2022).
  https://bidenwhitehouse.archives.gov/wp-content/uploads/2022/06/Maternal-Health-Blueprint.pdf

Blueprint Goals (used as category framework):
1. Healthcare Access & Coverage - comprehensive high-quality maternal health services
2. Quality of Care & Patient Voice - accountable systems where patients are heard
3. Data & Research - evidence-based practices and outcomes tracking
4. Perinatal Workforce - expand and diversify providers (doulas, midwives, CHWs)
5. Social & Economic Supports - address SDOH (housing, food, economic stability)

SDOH Framework Domains (Solar & Irwin, 2010):
- Structural Determinants: socioeconomic position, education, occupation
- Intermediary Determinants: material circumstances, behaviors, biological factors
- Health System: access, quality, coverage

State-Level Reference Sources:
- California CDPH MCAH: https://www.cdph.ca.gov/Programs/CFH/DMCAH/Pages/Domains/Maternal-Health.aspx
- Florida DOH: https://www.floridahealth.gov/individual-family-health/womens-health/pregnancy/
"""

from typing import List, Dict, Optional
from dataclasses import dataclass, field
from enum import Enum


# =============================================================================
# THEORETICAL FRAMEWORK: SDOH-ALIGNED CATEGORIES
# =============================================================================

class SDOHDomain(Enum):
    """Social Determinants of Health domains (Solar & Irwin, 2010)"""
    HEALTHCARE_ACCESS = "Healthcare Access & Coverage"
    QUALITY_OF_CARE = "Quality of Care & Patient Voice"
    SOCIAL_SUPPORT = "Social Support & Community"
    ECONOMIC_STABILITY = "Economic Stability"
    NUTRITION_FOOD = "Nutrition & Food Security"
    EDUCATION_LITERACY = "Education & Health Literacy"
    NEIGHBORHOOD_ENVIRONMENT = "Neighborhood & Physical Environment"


class BlueprintGoal(Enum):
    """White House Maternal Health Blueprint Goals (2022)"""
    GOAL_1_ACCESS = "Goal 1: Healthcare Access & Coverage"
    GOAL_2_QUALITY = "Goal 2: Quality of Care & Patient Voice"
    GOAL_3_DATA = "Goal 3: Data Collection & Research"
    GOAL_4_WORKFORCE = "Goal 4: Perinatal Workforce"
    GOAL_5_SOCIAL = "Goal 5: Social & Economic Supports"


@dataclass
class ProgramType:
    """A maternal health program type with SDOH and Blueprint alignment."""
    name: str
    category: str  # Primary category for display
    description: str
    keywords: List[str]
    sdoh_domain: SDOHDomain  # SDOH framework alignment
    blueprint_goal: BlueprintGoal  # White House Blueprint alignment
    federal_program: bool = False
    examples: List[str] = field(default_factory=list)


# =============================================================================
# MATERNAL HEALTH PROGRAM TAXONOMY
# Organized by Blueprint Goals with SDOH alignment
# =============================================================================

MATERNAL_PROGRAM_TYPES: List[ProgramType] = [
    
    # =========================================================================
    # GOAL 1: HEALTHCARE ACCESS & COVERAGE
    # SDOH Domain: Healthcare Access
    # =========================================================================
    
    ProgramType(
        name="Comprehensive Perinatal Services Program",
        category="Perinatal Care",
        description="Enhanced prenatal and postpartum care for Medi-Cal eligible women, "
                    "including health education, nutrition, and psychosocial assessments",
        keywords=[
            "comprehensive perinatal services", "cpsp", "perinatal services program",
            "enhanced prenatal care", "medi-cal prenatal", "perinatal care",
            "perinatal", "perinatal care network", "pcn", "perinatal_care",
            "perinatal services", "perinatal program", "perinatal health",
            "perinatal outreach",
        ],
        sdoh_domain=SDOHDomain.HEALTHCARE_ACCESS,
        blueprint_goal=BlueprintGoal.GOAL_1_ACCESS,
        federal_program=False,
        examples=["CPSP", "Perinatal Care Network", "Comprehensive Perinatal Services"],
    ),
    ProgramType(
        name="Prenatal Care Programs",
        category="Perinatal Care",
        description="General prenatal care and pregnancy services ensuring access to "
                    "quality care during pregnancy",
        keywords=[
            "prenatal care", "prenatal services", "prenatal program",
            "pregnancy care", "pregnancy services", "prenatal clinic",
            "prenatal health", "maternity care", "obstetric care",
            "prenatal visit", "ob-gyn", "obgyn",
        ],
        sdoh_domain=SDOHDomain.HEALTHCARE_ACCESS,
        blueprint_goal=BlueprintGoal.GOAL_1_ACCESS,
        federal_program=False,
        examples=["Prenatal Care Program", "Pregnancy Services", "Maternity Clinic"],
    ),
    ProgramType(
        name="Postpartum Care & Support",
        category="Perinatal Care",
        description="Services for mothers after childbirth including physical health, "
                    "mental health support, and care coordination",
        keywords=[
            "postpartum", "postpartum support", "postpartum care",
            "postpartum depression", "postpartum services",
            "after birth", "new mother support", "postpartum visit",
            "fourth trimester", "maternal recovery",
        ],
        sdoh_domain=SDOHDomain.HEALTHCARE_ACCESS,
        blueprint_goal=BlueprintGoal.GOAL_1_ACCESS,
        federal_program=False,
        examples=["Postpartum Support Program", "New Mother Services"],
    ),
    ProgramType(
        name="Maternal Mental Health Services",
        category="Behavioral Health",
        description="Mental health services for pregnant and postpartum individuals, "
                    "including screening, counseling, and treatment for perinatal mood disorders",
        keywords=[
            "maternal mental health", "perinatal mental health",
            "postpartum depression", "perinatal mood", "pregnancy depression",
            "maternal anxiety", "perinatal psychiatry", "maternal behavioral health",
            "perinatal mood disorder", "prenatal depression",
        ],
        sdoh_domain=SDOHDomain.HEALTHCARE_ACCESS,
        blueprint_goal=BlueprintGoal.GOAL_1_ACCESS,
        federal_program=False,
        examples=["Maternal Mental Health Program", "Perinatal Mood Support"],
    ),
    ProgramType(
        name="Substance Use Disorder Services",
        category="Behavioral Health",
        description="Perinatal addiction services and support for pregnant and postpartum "
                    "individuals with substance use disorders",
        keywords=[
            "perinatal addiction", "substance use pregnancy", "neonatal abstinence",
            "opioid pregnancy", "maternal substance use", "recovery pregnancy",
            "neonatal withdrawal", "medication assisted treatment pregnancy",
        ],
        sdoh_domain=SDOHDomain.HEALTHCARE_ACCESS,
        blueprint_goal=BlueprintGoal.GOAL_1_ACCESS,
        federal_program=False,
        examples=["Perinatal Substance Use Program", "Recovery Support for Moms"],
    ),
    ProgramType(
        name="Family Planning Services",
        category="Reproductive Health",
        description="Reproductive health and family planning services including "
                    "preconception health, contraception, and Title X services",
        keywords=[
            "family planning", "reproductive health", "birth control",
            "contraception", "family planning services", "title x",
            "preconception", "preconception health", "planned parenthood",
            "reproductive services",
        ],
        sdoh_domain=SDOHDomain.HEALTHCARE_ACCESS,
        blueprint_goal=BlueprintGoal.GOAL_1_ACCESS,
        federal_program=False,
        examples=["Family Planning Program", "Title X Services"],
    ),
    
    # =========================================================================
    # GOAL 2: QUALITY OF CARE & PATIENT VOICE
    # SDOH Domain: Quality of Care
    # =========================================================================
    
    ProgramType(
        name="Black Infant Health",
        category="Health Equity",
        description="California program addressing African American infant mortality "
                    "through culturally-specific group education, peer support, and case management. "
                    "Addresses systemic racism and health disparities in maternal care.",
        keywords=[
            "black infant health", "bih", "african american infant",
            "black maternal health", "infant mortality reduction",
            "racial equity maternal", "birth equity", "black mothers",
            "african american maternal", "aaimm",
        ],
        sdoh_domain=SDOHDomain.QUALITY_OF_CARE,
        blueprint_goal=BlueprintGoal.GOAL_2_QUALITY,
        federal_program=False,
        examples=["Black Infant Health Program", "BIH", "AAIMM"],
    ),
    ProgramType(
        name="Perinatal Equity Initiative",
        category="Health Equity",
        description="Programs focused on reducing racial disparities in maternal and infant "
                    "health outcomes, addressing implicit bias and structural racism",
        keywords=[
            "perinatal equity", "birth equity", "maternal equity",
            "racial disparities birth", "health equity maternal",
            "equity initiative", "maternal mortality disparity",
            "black maternal mortality", "implicit bias training",
        ],
        sdoh_domain=SDOHDomain.QUALITY_OF_CARE,
        blueprint_goal=BlueprintGoal.GOAL_2_QUALITY,
        federal_program=False,
        examples=["Perinatal Equity Initiative", "Birth Equity Program"],
    ),
    ProgramType(
        name="Healthy Start",
        category="Health Equity",
        description="Federal program to reduce infant mortality and improve perinatal "
                    "outcomes in high-risk communities through community health workers and outreach",
        keywords=[
            "healthy start", "infant mortality", "high-risk communities",
            "community health workers", "perinatal outcomes",
            "fetal infant mortality", "fimr",
        ],
        sdoh_domain=SDOHDomain.QUALITY_OF_CARE,
        blueprint_goal=BlueprintGoal.GOAL_2_QUALITY,
        federal_program=True,
        examples=["Healthy Start Initiative", "Healthy Start Program"],
    ),
    ProgramType(
        name="Maternal Mortality Review",
        category="Quality Improvement",
        description="Maternal Mortality Review Committees (MMRCs) that analyze pregnancy-related "
                    "deaths to identify preventable factors and improve systems of care",
        keywords=[
            "maternal mortality review", "mmrc", "pregnancy related death",
            "maternal death review", "perinatal quality", "quality improvement",
            "aim alliance", "perinatal quality collaborative", "pqc",
        ],
        sdoh_domain=SDOHDomain.QUALITY_OF_CARE,
        blueprint_goal=BlueprintGoal.GOAL_2_QUALITY,
        federal_program=False,
        examples=["MMRC", "Perinatal Quality Collaborative"],
    ),
    
    # =========================================================================
    # GOAL 4: PERINATAL WORKFORCE
    # SDOH Domain: Social Support
    # =========================================================================
    
    ProgramType(
        name="Nurse-Family Partnership",
        category="Home Visiting",
        description="Evidence-based nurse home visiting program for first-time, low-income "
                    "mothers from pregnancy through child's second birthday",
        keywords=[
            "nurse-family partnership", "nfp", "nurse family partnership",
            "nurse home visiting", "first-time mothers", "nurse home visits",
            "public health nurse", "phn",
        ],
        sdoh_domain=SDOHDomain.SOCIAL_SUPPORT,
        blueprint_goal=BlueprintGoal.GOAL_4_WORKFORCE,
        federal_program=True,
        examples=["Nurse-Family Partnership", "NFP Program"],
    ),
    ProgramType(
        name="MIECHV Home Visiting",
        category="Home Visiting",
        description="Maternal, Infant, and Early Childhood Home Visiting - federal program "
                    "supporting voluntary evidence-based home visiting for at-risk families",
        keywords=[
            "miechv", "maternal infant early childhood home visiting",
            "home visiting program", "early childhood home visiting",
            "california home visiting", "chvp",
        ],
        sdoh_domain=SDOHDomain.SOCIAL_SUPPORT,
        blueprint_goal=BlueprintGoal.GOAL_4_WORKFORCE,
        federal_program=True,
        examples=["MIECHV Program", "Home Visiting Initiative", "CHVP"],
    ),
    ProgramType(
        name="Healthy Families America",
        category="Home Visiting",
        description="Home visiting program for new and expectant families at-risk "
                    "for child maltreatment, promoting positive parenting",
        keywords=[
            "healthy families", "healthy families america", "hfa",
            "family support home visiting",
        ],
        sdoh_domain=SDOHDomain.SOCIAL_SUPPORT,
        blueprint_goal=BlueprintGoal.GOAL_4_WORKFORCE,
        federal_program=True,
        examples=["Healthy Families America", "Healthy Families Program"],
    ),
    ProgramType(
        name="Parents as Teachers",
        category="Home Visiting",
        description="Home visiting program focused on parent education and child development "
                    "from pregnancy through kindergarten",
        keywords=[
            "parents as teachers", "pat program", "parent education",
            "parent-child interaction",
        ],
        sdoh_domain=SDOHDomain.SOCIAL_SUPPORT,
        blueprint_goal=BlueprintGoal.GOAL_4_WORKFORCE,
        federal_program=True,
        examples=["Parents as Teachers", "PAT Program"],
    ),
    ProgramType(
        name="Doula Services",
        category="Birth Support",
        description="Community-based doula support during pregnancy, birth, and postpartum. "
                    "Associated with lower rates of pregnancy complications and improved outcomes.",
        keywords=[
            "doula", "birth doula", "community doula", "doula services",
            "birth support", "labor support", "birth companion",
            "doula program", "aaimm doula",
        ],
        sdoh_domain=SDOHDomain.SOCIAL_SUPPORT,
        blueprint_goal=BlueprintGoal.GOAL_4_WORKFORCE,
        federal_program=False,
        examples=["Doula Program", "Community Doula Services", "AAIMM Doula"],
    ),
    ProgramType(
        name="Midwifery Services",
        category="Birth Support",
        description="Licensed midwife-led prenatal, birth, and postpartum care. "
                    "Includes certified nurse midwives (CNM) and licensed midwives.",
        keywords=[
            "midwife", "midwifery", "certified nurse midwife",
            "cnm", "licensed midwife", "birth center", "freestanding birth center",
        ],
        sdoh_domain=SDOHDomain.SOCIAL_SUPPORT,
        blueprint_goal=BlueprintGoal.GOAL_4_WORKFORCE,
        federal_program=False,
        examples=["Midwifery Program", "Birth Center", "CNM Services"],
    ),
    ProgramType(
        name="Community Health Workers",
        category="Community Health",
        description="Community health workers (promotores) providing outreach, education, "
                    "and care navigation for pregnant and postpartum individuals",
        keywords=[
            "community health worker", "promotora", "promotores",
            "health navigator", "care coordination", "patient navigator",
            "community outreach", "chw",
        ],
        sdoh_domain=SDOHDomain.SOCIAL_SUPPORT,
        blueprint_goal=BlueprintGoal.GOAL_4_WORKFORCE,
        federal_program=False,
        examples=["CHW Program", "Promotoras de Salud"],
    ),
    ProgramType(
        name="Lactation Support",
        category="Breastfeeding",
        description="Breastfeeding education and lactation consultant services to support "
                    "breastfeeding initiation and continuation",
        keywords=[
            "breastfeeding", "lactation", "lactation support",
            "lactation consultant", "breastfeeding education",
            "nursing mother", "breast pump", "milk bank", "ibclc",
            "breastfeeding peer counselor",
        ],
        sdoh_domain=SDOHDomain.SOCIAL_SUPPORT,
        blueprint_goal=BlueprintGoal.GOAL_4_WORKFORCE,
        federal_program=False,
        examples=["Breastfeeding Support Program", "Lactation Services"],
    ),
    
    # =========================================================================
    # GOAL 5: SOCIAL & ECONOMIC SUPPORTS
    # SDOH Domain: Nutrition, Economic Stability, Social Support
    # =========================================================================
    
    ProgramType(
        name="WIC Program",
        category="Nutrition",
        description="Women, Infants, and Children - supplemental nutrition program providing "
                    "food benefits, nutrition education, and breastfeeding support",
        keywords=[
            "wic", "women infants children", "women, infants, and children",
            "supplemental nutrition", "wic program", "wic clinic",
            "wic benefits", "wic foods", "wic eligibility",
        ],
        sdoh_domain=SDOHDomain.NUTRITION_FOOD,
        blueprint_goal=BlueprintGoal.GOAL_5_SOCIAL,
        federal_program=True,
        examples=["WIC Program", "WIC Nutrition Services", "WIC Clinic"],
    ),
    ProgramType(
        name="Teen Pregnancy & Parenting Programs",
        category="Adolescent Health",
        description="Comprehensive services for pregnant and parenting teens including "
                    "case management, education support, and healthcare access",
        keywords=[
            "adolescent family life", "aflp", "teen pregnancy",
            "pregnant teens", "parenting teens", "adolescent pregnancy",
            "teen parent", "young parent", "teenage pregnancy",
            "tapp", "teen parenting",
        ],
        sdoh_domain=SDOHDomain.SOCIAL_SUPPORT,
        blueprint_goal=BlueprintGoal.GOAL_5_SOCIAL,
        federal_program=False,
        examples=["AFLP", "Teen Pregnancy Program", "TAPP"],
    ),
    ProgramType(
        name="First 5 Programs",
        category="Early Childhood",
        description="California First 5 programs supporting children ages 0-5 and their families "
                    "with health, development, and school readiness services",
        keywords=[
            "first 5", "first five", "proposition 10", "prop 10",
            "children ages 0-5", "early childhood", "kindergarten readiness",
        ],
        sdoh_domain=SDOHDomain.SOCIAL_SUPPORT,
        blueprint_goal=BlueprintGoal.GOAL_5_SOCIAL,
        federal_program=False,
        examples=["First 5 California", "First 5 LA", "First 5 Commission"],
    ),
    ProgramType(
        name="Title V MCH Block Grant",
        category="Maternal Child Health",
        description="Federal Title V Maternal and Child Health Services Block Grant funding "
                    "state programs for mothers and children",
        keywords=[
            "title v", "title five", "mch block grant",
            "maternal child health block", "mch services",
            "mcah", "maternal child adolescent health",
            "mch program", "mcfhs",
        ],
        sdoh_domain=SDOHDomain.HEALTHCARE_ACCESS,
        blueprint_goal=BlueprintGoal.GOAL_1_ACCESS,
        federal_program=True,
        examples=["Title V Program", "MCH Services", "MCAH Program", "MCFHS"],
    ),
]


# =============================================================================
# NON-MATERNAL PROGRAMS (Exclusion List)
# Per advisor: keep maternal health focused, don't mix with general health
# =============================================================================

NON_MATERNAL_KEYWORDS = [
    # General health insurance (not maternal-specific)
    "medi-cal", "medicaid", "medicare", "calfresh", "food stamps", "snap",
    # Aging services
    "senior", "elderly", "aging", "older adults", "adult protective", "elder abuse",
    # Mental health (general, not perinatal)
    "behavioral health", "substance abuse", "addiction", "drug treatment",
    # Housing (general)
    "housing", "homeless", "shelter",
    # General social services
    "child protective", "foster care", "adoption", "calworks", "tanf",
    # Veterans (general)
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


def get_keywords_by_sdoh_domain(domain: SDOHDomain) -> List[str]:
    """Get keywords for a specific SDOH domain."""
    keywords = []
    for pt in MATERNAL_PROGRAM_TYPES:
        if pt.sdoh_domain == domain:
            keywords.extend(pt.keywords)
    return list(set(keywords))


def get_keywords_by_blueprint_goal(goal: BlueprintGoal) -> List[str]:
    """Get keywords for a specific Blueprint goal."""
    keywords = []
    for pt in MATERNAL_PROGRAM_TYPES:
        if pt.blueprint_goal == goal:
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
    
    return best_match if best_score > 0 else None


def is_maternal_health_program(text: str, url: str = "") -> bool:
    """
    Determine if a program is maternal health related.
    Uses the taxonomy to make this determination.
    """
    return classify_program(text, url) is not None


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


def get_program_categories() -> List[str]:
    """Get all unique program categories."""
    return list(set(pt.category for pt in MATERNAL_PROGRAM_TYPES))


def get_federal_programs() -> List[ProgramType]:
    """Get all federal/state-mandated programs."""
    return [pt for pt in MATERNAL_PROGRAM_TYPES if pt.federal_program]


def get_programs_by_sdoh_domain(domain: SDOHDomain) -> List[ProgramType]:
    """Get all programs for a specific SDOH domain."""
    return [pt for pt in MATERNAL_PROGRAM_TYPES if pt.sdoh_domain == domain]


def get_programs_by_blueprint_goal(goal: BlueprintGoal) -> List[ProgramType]:
    """Get all programs for a specific Blueprint goal."""
    return [pt for pt in MATERNAL_PROGRAM_TYPES if pt.blueprint_goal == goal]


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
    Organized by Blueprint goals for theoretical grounding.
    """
    examples = []
    
    # Select representative examples from each Blueprint goal
    goals_shown = set()
    for pt in MATERNAL_PROGRAM_TYPES:
        if pt.blueprint_goal in goals_shown:
            continue
        goals_shown.add(pt.blueprint_goal)
        
        examples.append(f"""
Program: {pt.name}
Category: {pt.category}
SDOH Domain: {pt.sdoh_domain.value}
Blueprint Goal: {pt.blueprint_goal.value}
Description: {pt.description}
Is Maternal Health Program: Yes
""".strip())
    
    return "\n\n".join(examples)


def get_framework_summary() -> str:
    """Get a summary of the theoretical framework for documentation."""
    return """
THEORETICAL FRAMEWORK FOR MATERNAL HEALTH PROGRAM CLASSIFICATION

This taxonomy is grounded in two complementary frameworks:

1. SOCIAL DETERMINANTS OF HEALTH (SDOH)
   Based on Solar & Irwin (2010) WHO Conceptual Framework
   
   Domains used in this taxonomy:
   - Healthcare Access & Coverage
   - Quality of Care & Patient Voice
   - Social Support & Community
   - Economic Stability
   - Nutrition & Food Security
   - Education & Health Literacy
   - Neighborhood & Physical Environment

2. WHITE HOUSE MATERNAL HEALTH BLUEPRINT (2022)
   Five-goal framework for addressing the maternal health crisis:
   
   Goal 1: Increase Access to and Coverage of Comprehensive 
           High-Quality Maternal Health Services
   Goal 2: Ensure Those Giving Birth are Heard and are 
           Decisionmakers in Accountable Systems of Care
   Goal 3: Advance Data Collection, Standardization, 
           Transparency, Research, and Analysis
   Goal 4: Expand and Diversify the Perinatal Workforce
   Goal 5: Strengthen Economic and Social Supports for People 
           Before, During, and After Pregnancy

KEY REFERENCES:
- Braveman et al. (2011, 2014) - Social determinants of health
- Marmot et al. (2012) - WHO European review of SDOH
- Solar & Irwin (2010) - WHO conceptual framework for SDOH
- White House Blueprint for Addressing the Maternal Health Crisis (2022)
"""


# =============================================================================
# PRINT TAXONOMY SUMMARY (for debugging/review)
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("MATERNAL HEALTH PROGRAM TAXONOMY")
    print("Grounded in SDOH Framework & White House Blueprint")
    print("=" * 70)
    print(f"\nTotal program types: {len(MATERNAL_PROGRAM_TYPES)}")
    print(f"Categories: {', '.join(sorted(get_program_categories()))}")
    print(f"Federal programs: {len(get_federal_programs())}")
    print(f"Total keywords: {len(get_all_keywords())}")
    
    print("\n" + "-" * 70)
    print("PROGRAMS BY BLUEPRINT GOAL")
    print("-" * 70)
    
    for goal in BlueprintGoal:
        programs = get_programs_by_blueprint_goal(goal)
        print(f"\n{goal.value}:")
        for pt in programs:
            federal = " [Federal]" if pt.federal_program else ""
            print(f"  - {pt.name} ({pt.category}){federal}")
    
    print("\n" + "-" * 70)
    print("PROGRAMS BY SDOH DOMAIN")
    print("-" * 70)
    
    for domain in SDOHDomain:
        programs = get_programs_by_sdoh_domain(domain)
        if programs:
            print(f"\n{domain.value}:")
            for pt in programs:
                print(f"  - {pt.name}")
    
    print("\n" + "-" * 70)
    print("EXAMPLE CLASSIFICATIONS")
    print("-" * 70)
    
    test_cases = [
        ("WIC Nutrition Program", "/wic/"),
        ("Medi-Cal Health Coverage", "/medi-cal/"),
        ("Black Infant Health Support", "/bih/"),
        ("Senior Services", "/aging/"),
        ("Prenatal Care Clinic", "/prenatal/"),
        ("CalFresh Food Assistance", "/calfresh/"),
        ("Nurse-Family Partnership", "/nfp/"),
        ("Doula Program", "/doula/"),
        ("Perinatal Equity Initiative", "/equity/"),
    ]
    
    for text, url in test_cases:
        is_maternal = is_maternal_health_program(text, url)
        is_excluded = is_non_maternal_program(text, url)
        classification = classify_program(text, url)
        cat = classification.category if classification else "N/A"
        sdoh = classification.sdoh_domain.value if classification else "N/A"
        
        status = "✓ KEEP" if is_maternal else ("✗ SKIP" if is_excluded else "? UNCLEAR")
        print(f"  {status}: '{text}'")
        print(f"         Category: {cat} | SDOH: {sdoh}")
