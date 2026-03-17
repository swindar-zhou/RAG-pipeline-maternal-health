"""
Federal Maternal Health Program Registry
=========================================
iTREDS Project - Ground-truth taxonomy built from verified federal sources.

USAGE LOGIC:
  Instead of keyword-scraping county websites open-endedly, match each county
  page against this registry. For each program, check whether the county lists
  it, and extract what details they provide. The output is a
  county x program presence matrix enabling cross-county gap analysis.

TIER DEFINITIONS:
  1 = Universal  - federally mandated, in every state AND every county health
                   dept. If a county doesn't list it -> genuine gap worth flagging.
  2 = State-wide - federally funded, every state participates, but county-level
                   presence depends on state distribution plan. Absence = possible gap.
  3 = Selective  - federally backed model; states/counties choose to adopt it.
                   Absence may reflect state choice, not a county-level gap.

STATE-SPECIFIC FIELD:
  state_specific = None       -> universal across all states
  state_specific = "CA"       -> California-specific implementation
  state_specific = "IN"       -> Indiana-specific implementation
  state_specific = "MULTI"    -> several states have this, not all

DATA SOURCES - verify each entry's federal_source_url before publication.
  Primary federal inventories used:
  - USDA FNS WIC:           https://www.fns.usda.gov/wic
  - HRSA Maternal Health:   https://www.hrsa.gov/maternal-health
  - MCHB Programs A-Z:      https://mchb.hrsa.gov/programs-impact/programs
  - CRS IF10595 (MIECHV):   https://www.congress.gov/crs-product/IF10595
  - CRS IF12685 (Title V):  https://www.congress.gov/crs-product/IF12685
  - CRS R44115 (WIC):       https://www.congress.gov/crs-product/R44115
  - Title X FP:             https://opa.hhs.gov/grant-programs/title-x-service-grants
  - CDPH DMCAH (CA):        https://www.cdph.ca.gov/Programs/CFH/DMCAH
  - Indiana DCS HFI:        https://secure.in.gov/dcs/prevention/healthy-families-indiana/
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class FederalProgram:
    program_id: str             # Unique stable identifier (use in your DB as FK)
    canonical_name: str         # Official federal or state program name
    acronym: str                # Common abbreviation as it appears on county sites
    federal_agency: str         # Administering federal agency
    authorizing_statute: str    # Legal basis / enabling legislation
    tier: int                   # 1=Universal, 2=State-wide, 3=Selective
    category: str               # Program category (aligned to White House Blueprint)
    blueprint_goal: int         # White House Blueprint goal (1-5); 0 = pre-dates blueprint
    target_population: str      # Who is served
    core_services: List[str]    # What the program provides
    county_aliases: List[str]   # Phrases county websites use - for fuzzy matching
    federal_source_url: str     # Primary federal source URL for verification
    state_specific: Optional[str] = None  # None=all states, "CA", "IN", "TX", etc.
    notes: str = ""             # Implementation nuances affecting county-level presence


# =============================================================================
# SECTION 1: UNIVERSAL FEDERAL PROGRAMS (Tier 1 & 2) - apply to ALL states
# =============================================================================

UNIVERSAL_PROGRAMS: List[FederalProgram] = [

    # -- TIER 1: Universal -----------------------------------------------------

    FederalProgram(
        program_id="WIC",
        canonical_name="Special Supplemental Nutrition Program for Women, Infants, and Children",
        acronym="WIC",
        federal_agency="USDA / Food and Nutrition Service (FNS)",
        authorizing_statute="Child Nutrition Act of 1966, 42 U.S.C. § 1786",
        tier=1,
        category="Nutrition & Food Security",
        blueprint_goal=5,
        target_population=(
            "Low-income pregnant, postpartum, and breastfeeding women; "
            "infants and children under 5 at nutritional risk (income <=185% FPL)"
        ),
        core_services=[
            "Supplemental food benefits (EBT/voucher)",
            "Nutrition education and counseling",
            "Breastfeeding support and peer counselors",
            "Referrals to health and social services",
        ],
        county_aliases=[
            "WIC", "Women, Infants and Children", "WIC program",
            "WIC clinic", "WIC office", "nutrition program",
            "supplemental nutrition", "WIC benefits",
        ],
        federal_source_url="https://www.fns.usda.gov/wic/about-wic",
        state_specific=None,
        notes=(
            "100% federally funded; no state match required. Operates in all 50 states, "
            "DC, 5 territories, 32 tribal orgs. Administered locally via county/city health "
            "depts or nonprofits. EVERY county health dept should list this. "
            "Source: CRS R44115, USDA FNS."
        ),
    ),

    FederalProgram(
        program_id="MEDICAID_PRENATAL",
        canonical_name="Medicaid Prenatal and Pregnancy Coverage",
        acronym="Medicaid (prenatal)",
        federal_agency="HHS / Centers for Medicare & Medicaid Services (CMS)",
        authorizing_statute="Title XIX of the Social Security Act, 42 U.S.C. § 1396 et seq.",
        tier=1,
        category="Healthcare Coverage",
        blueprint_goal=1,
        target_population=(
            "Pregnant individuals meeting income thresholds; varies by state expansion "
            "status. CA: Medi-Cal up to 213% FPL. IN: Medicaid up to 200% FPL."
        ),
        core_services=[
            "Prenatal care coverage",
            "Labor and delivery coverage",
            "Postpartum care (12 months in expansion states since 2022)",
            "Behavioral health coverage during pregnancy",
        ],
        county_aliases=[
            "Medicaid", "Medicaid for pregnant women", "pregnancy Medicaid",
            "prenatal coverage", "insurance for pregnant women",
            "healthcare coverage pregnancy", "Medi-Cal", "Medi-Cal for pregnancy",
            "Hoosier Healthwise", "HIP 2.0 pregnancy",
        ],
        federal_source_url="https://www.medicaid.gov/medicaid/benefits/pregnancy-related-services/index.html",
        state_specific=None,
        notes=(
            "In CA: called Medi-Cal. In IN: called Medicaid/Hoosier Healthwise. "
            "12-month postpartum extension became permanent under ARP Act 2021; states "
            "had until Jan 2023 to opt in. Both CA and IN opted in."
        ),
    ),

    # -- TIER 2: State-wide ----------------------------------------------------

    FederalProgram(
        program_id="TITLE_V_MCH",
        canonical_name="Title V Maternal and Child Health Services Block Grant",
        acronym="Title V / MCH Block Grant",
        federal_agency="HHS / HRSA / Maternal and Child Health Bureau (MCHB)",
        authorizing_statute="Title V of the Social Security Act, 42 U.S.C. § 701 et seq.",
        tier=2,
        category="Maternal & Child Health Systems",
        blueprint_goal=1,
        target_population="Pregnant women, mothers, infants, children including those with special health care needs",
        core_services=[
            "Gap-filling prenatal and postpartum services",
            "Perinatal care coordination",
            "Newborn screening follow-up",
            "CYSHCN (Children with Special Health Care Needs) services",
            "Public health infrastructure and workforce",
        ],
        county_aliases=[
            "Title V", "MCH", "MCAH", "maternal child health",
            "maternal child adolescent health", "MCAH program",
            "public health nurse prenatal", "perinatal case management",
            "MCH Block Grant",
        ],
        federal_source_url="https://mchb.hrsa.gov/programs-impact/title-v-maternal-child-health-mch-services-block-grant",
        state_specific=None,
        notes=(
            "States must match $3 for every $4 federal. CA: CDPH MCAH Division "
            "distributes to county LHDs - county MCAH programs are primary local recipient. "
            "IN: ISDH MCH Division administers; funds county health depts and nonprofits. "
            "Source: CRS IF12685, MCHB TVIS narratives (CA & IN)."
        ),
    ),

    FederalProgram(
        program_id="MIECHV",
        canonical_name="Maternal, Infant, and Early Childhood Home Visiting Program",
        acronym="MIECHV",
        federal_agency="HHS / HRSA + Administration for Children and Families (ACF)",
        authorizing_statute="Section 511 of the Social Security Act (ACA §2951), P.L. 111-148; reauth. P.L. 117-328",
        tier=2,
        category="Home Visiting",
        blueprint_goal=4,
        target_population="Pregnant women and parents with children 0-5 in at-risk communities; low-income, history of abuse/neglect, teen parents",
        core_services=[
            "Voluntary home visits by trained professionals",
            "Parenting education and support",
            "Maternal and child health screenings",
            "Referrals to community resources (WIC, Medicaid, housing)",
            "Developmental milestone monitoring",
        ],
        county_aliases=[
            "MIECHV", "home visiting", "home visits",
            "maternal home visiting", "infant home visiting",
            "home visitation program",
        ],
        federal_source_url="https://mchb.hrsa.gov/programs-impact/programs/home-visiting/maternal-infant-early-childhood-home-visiting-miechv-program",
        state_specific=None,
        notes=(
            "MIECHV is the federal umbrella; specific evidence-based models (NFP, HFA, PAT) "
            "are chosen by states. Funded through FY2027: $600M (FY25), $650M (FY26), $800M (FY27). "
            "CA: CDPH administers to counties. "
            "IN: ISDH + DCS co-lead; operates NFP and Healthy Families Indiana (HFI). "
            "Source: CRS IF10595, PMC6600820."
        ),
    ),

    FederalProgram(
        program_id="HEALTHY_START",
        canonical_name="Healthy Start Program",
        acronym="Healthy Start",
        federal_agency="HHS / HRSA / MCHB",
        authorizing_statute="42 U.S.C. § 254c-8",
        tier=2,
        category="Community-Based Perinatal Services",
        blueprint_goal=1,
        target_population="High-risk pregnant women, infants, and mothers in communities with high infant mortality; emphasis on Black and minority communities",
        core_services=[
            "Case management and care coordination",
            "Health education before, during, after pregnancy",
            "Interconception care",
            "Health systems navigation",
            "Community health workers / outreach",
        ],
        county_aliases=[
            "Healthy Start", "Healthy Start program",
            "infant mortality reduction", "perinatal health program",
            "community health worker pregnancy",
        ],
        federal_source_url="https://mchb.hrsa.gov/programs-impact/healthy-start",
        state_specific=None,
        notes=(
            "Competitive grants; not every county has a Healthy Start site. "
            "CA grantees include LA County, Fresno, etc. "
            "IN has had Healthy Start grantees in Indianapolis/Marion County. "
            "Addresses racial disparities in infant/maternal mortality. "
            "Source: HRSA Healthy Start locator, MCHB factsheet."
        ),
    ),

    FederalProgram(
        program_id="TITLE_X_FP",
        canonical_name="Title X Family Planning Program",
        acronym="Title X",
        federal_agency="HHS / Office of Population Affairs (OPA)",
        authorizing_statute="Title X of the Public Health Service Act, 42 U.S.C. § 300 et seq.",
        tier=2,
        category="Reproductive Health",
        blueprint_goal=1,
        target_population="Low-income individuals seeking family planning and reproductive health services; priority to those at or below 100% FPL",
        core_services=[
            "Contraceptive counseling and services",
            "STI/HIV testing and counseling",
            "Preconception counseling",
            "Pregnancy testing and referrals",
            "Cervical and breast cancer screening",
        ],
        county_aliases=[
            "Title X", "family planning", "reproductive health clinic",
            "birth control clinic", "contraception services",
            "women's health clinic", "preconception care",
        ],
        federal_source_url="https://opa.hhs.gov/grant-programs/title-x-service-grants",
        state_specific=None,
        notes=(
            "Funds flow to grantees (county health depts, Planned Parenthood, FQHCs). "
            "Not every county operates Title X directly - some contract to nonprofits. "
            "Distinct from Title V but often co-located."
        ),
    ),

    FederalProgram(
        program_id="FQHC",
        canonical_name="Federally Qualified Health Centers - Prenatal/Maternal Care",
        acronym="FQHC / Community Health Center",
        federal_agency="HHS / HRSA / Bureau of Primary Health Care (BPHC)",
        authorizing_statute="Section 330 of the Public Health Service Act, 42 U.S.C. § 254b",
        tier=2,
        category="Primary Care Access",
        blueprint_goal=1,
        target_population="Uninsured, underinsured, and low-income patients regardless of ability to pay; includes pregnant women",
        core_services=[
            "Prenatal care on sliding-fee scale",
            "Postpartum care",
            "WIC co-location in many sites",
            "Behavioral health integration",
            "Dental care during pregnancy",
        ],
        county_aliases=[
            "community health center", "federally qualified health center",
            "FQHC", "health center", "clinic prenatal",
            "sliding scale prenatal care", "low-cost prenatal",
        ],
        federal_source_url="https://findahealthcenter.hrsa.gov/",
        state_specific=None,
        notes=(
            "HRSA funds ~1,400 FQHC grantees operating 15,000+ sites nationwide. "
            "Relevant as county sites frequently reference FQHCs for prenatal care access."
        ),
    ),

    # -- TIER 3: Selective (Federal programs, not all counties) ----------------

    FederalProgram(
        program_id="NFP",
        canonical_name="Nurse-Family Partnership",
        acronym="NFP",
        federal_agency="HHS / HRSA (funded via MIECHV); private nonprofit model",
        authorizing_statute="Via MIECHV (Section 511 SSA); model developed by David Olds",
        tier=3,
        category="Home Visiting - Evidence-Based Model",
        blueprint_goal=4,
        target_population="First-time, low-income pregnant women enrolled by 28 weeks gestation",
        core_services=[
            "Registered nurse home visits from pregnancy through child's 2nd birthday",
            "Maternal health and prenatal care guidance",
            "Child development support",
            "Parenting skills",
            "Economic self-sufficiency coaching",
        ],
        county_aliases=[
            "Nurse-Family Partnership", "NFP", "nurse home visiting",
            "registered nurse home visits", "NFP program",
        ],
        federal_source_url="https://mchb.hrsa.gov/programs-impact/programs/home-visiting/maternal-infant-early-childhood-home-visiting-miechv-program",
        state_specific=None,
        notes=(
            "One of the 4 most commonly funded MIECHV models. "
            "CA: present in multiple counties via CDPH MIECHV funds. "
            "IN: funded by both MIECHV and state Title V funds; operates in several counties. "
            "Source: PMC6600820, Indiana ISDH TVIS narratives FY21."
        ),
    ),

    FederalProgram(
        program_id="HFA",
        canonical_name="Healthy Families America",
        acronym="HFA",
        federal_agency="HHS / HRSA (funded via MIECHV); model by Prevent Child Abuse America",
        authorizing_statute="Via MIECHV (Section 511 SSA)",
        tier=3,
        category="Home Visiting - Evidence-Based Model",
        blueprint_goal=4,
        target_population="Families with newborns up to 3 months; stress and risk-factor screening at birth",
        core_services=[
            "Home visits starting at or before birth",
            "Parent-child relationship building",
            "Child abuse/neglect prevention",
            "Developmental screening",
            "Community resource linkage",
        ],
        county_aliases=[
            "Healthy Families America", "HFA", "Healthy Families",
            "healthy families program", "family support home visiting",
            "Healthy Families Indiana",
        ],
        federal_source_url="https://mchb.hrsa.gov/programs-impact/programs/home-visiting/maternal-infant-early-childhood-home-visiting-miechv-program",
        state_specific=None,
        notes=(
            "In IN, HFA operates as 'Healthy Families Indiana (HFI)' administered by DCS. "
            "HFI is available in all 92 IN counties (31 agencies, 43 sites) - broader "
            "reach than most states' HFA implementations. "
            "Source: Indiana DCS HFI page, ISDH MIECHV page."
        ),
    ),

    FederalProgram(
        program_id="PAT",
        canonical_name="Parents as Teachers",
        acronym="PAT",
        federal_agency="HHS / HRSA (funded via MIECHV); model by PAT National Center",
        authorizing_statute="Via MIECHV (Section 511 SSA)",
        tier=3,
        category="Home Visiting - Evidence-Based Model",
        blueprint_goal=4,
        target_population="Expectant parents and families with children from birth through age 3 (or 5 in some implementations)",
        core_services=[
            "Personal home visits",
            "Group connections / parent meetings",
            "Child developmental screenings",
            "Family health and resource network",
        ],
        county_aliases=[
            "Parents as Teachers", "PAT", "parent educator home visits",
        ],
        federal_source_url="https://mchb.hrsa.gov/programs-impact/programs/home-visiting/maternal-infant-early-childhood-home-visiting-miechv-program",
        state_specific=None,
        notes="One of 4 most common MIECHV models. Source: MIHOPE study (MDRC).",
    ),

    FederalProgram(
        program_id="AIM",
        canonical_name="Alliance for Innovation on Maternal Health",
        acronym="AIM",
        federal_agency="HHS / HRSA / MCHB",
        authorizing_statute="SPRANS funding under Title V MCH Block Grant",
        tier=3,
        category="Quality Improvement - Hospital-Based",
        blueprint_goal=2,
        target_population="Birthing hospitals and obstetric providers; indirectly serves all pregnant women",
        core_services=[
            "Hospital safety bundles for obstetric hemorrhage",
            "Hypertension in pregnancy protocols",
            "Maternal early warning systems",
            "Racial equity quality improvement",
            "State-level AIM teams and learning networks",
        ],
        county_aliases=[
            "AIM", "Alliance for Innovation on Maternal Health",
            "maternal safety bundle", "obstetric quality improvement",
            "IPQIC",
        ],
        federal_source_url="https://mchb.hrsa.gov/programs-impact/programs/alliance-innovation-maternal-health",
        state_specific=None,
        notes=(
            "Hospital/clinical system level, not county health dept level. "
            "IN equivalent: Indiana Perinatal Quality Improvement Collaborative (IPQIC) "
            "implements AIM bundles. CA: CMQCC implements AIM bundles. "
            "Expect low county-website presence."
        ),
    ),

    FederalProgram(
        program_id="MATERNAL_MENTAL_HEALTH_HOTLINE",
        canonical_name="National Maternal Mental Health Hotline",
        acronym="NMMHH",
        federal_agency="HHS / HRSA / MCHB",
        authorizing_statute="Consolidated Appropriations Act, 2021",
        tier=3,
        category="Maternal Mental Health",
        blueprint_goal=1,
        target_population="Pregnant and postpartum individuals experiencing mental health challenges",
        core_services=[
            "24/7 free confidential phone/text counseling (1-833-TLC-MAMA)",
            "Referrals to local mental health services",
            "Support in multiple languages",
        ],
        county_aliases=[
            "maternal mental health hotline", "1-833-TLC-MAMA",
            "postpartum depression hotline", "perinatal mental health support",
            "pregnancy mental health line",
        ],
        federal_source_url="https://mchb.hrsa.gov/national-maternal-mental-health-hotline",
        state_specific=None,
        notes=(
            "National hotline, not a local program. "
            "Metric: does the county website reference/link this hotline? "
            "Note IN has its own state hotline (MOMS Helpline) that is more prominently listed."
        ),
    ),

    FederalProgram(
        program_id="PPW_SUD",
        canonical_name="Screening and Treatment for Maternal Mental Health and Substance Use Disorders",
        acronym="PPW-SUD",
        federal_agency="HHS / HRSA / MCHB",
        authorizing_statute="SUPPORT for Patients and Communities Act, P.L. 115-271 §7081",
        tier=3,
        category="Maternal Mental Health & Substance Use",
        blueprint_goal=1,
        target_population="Pregnant and postpartum women screened for depression, anxiety, and substance use disorders",
        core_services=[
            "Provider training on perinatal mental health screening",
            "Depression and anxiety assessment tools",
            "SUD treatment referrals",
            "Integration of behavioral health into prenatal care",
        ],
        county_aliases=[
            "perinatal mental health", "postpartum depression screening",
            "depression screening prenatal", "substance use pregnancy",
            "opioid pregnancy", "MAT pregnancy", "behavioral health prenatal",
            "NAS", "neonatal abstinence syndrome", "opioid use disorder pregnancy",
        ],
        federal_source_url="https://mchb.hrsa.gov/programs-impact/screening-treatment-maternal-depression-related-behavioral-disorders-program-mdrbd",
        state_specific=None,
        notes=(
            "Especially important for IN, which has documented high NAS rates "
            "(12.5 per 1,000 live births in 2019 vs ~5.8 national). "
            "Source: Indiana ISDH TVIS FY20 narrative, Indiana IPQIC."
        ),
    ),
]


# =============================================================================
# SECTION 2: CALIFORNIA-SPECIFIC STATE PROGRAMS
# (State programs receiving federal Title V match; CA only)
# =============================================================================

CALIFORNIA_PROGRAMS: List[FederalProgram] = [

    FederalProgram(
        program_id="BIH_CA",
        canonical_name="Black Infant Health Program",
        acronym="BIH",
        federal_agency="California CDPH (funded via Title V MCH Block Grant + state GF)",
        authorizing_statute="California Health and Safety Code §124174; Title V federal match",
        tier=3,
        category="Racial Health Equity - Maternal",
        blueprint_goal=2,
        target_population="Black/African American women of childbearing age; addresses 3-4x higher Black maternal mortality rate",
        core_services=[
            "Group-based life skills and stress coping (theory of weathering/John Henryism)",
            "Case management for high-risk Black mothers",
            "Community health worker support",
            "Interconception care",
        ],
        county_aliases=[
            "Black Infant Health", "BIH", "African American infant health",
            "Black maternal health program",
        ],
        federal_source_url="https://www.cdph.ca.gov/Programs/CFH/DMCAH/BIH/Pages/Program-Overview.aspx",
        state_specific="CA",
        notes=(
            "CA-specific. Operates in most CA counties. "
            "KEY program for racial equity research angle. "
            "No Indiana equivalent - IN does not have a comparable state-funded program "
            "specifically for Black maternal health. "
            "Source: CDPH DMCAH."
        ),
    ),

    FederalProgram(
        program_id="PCN_CA",
        canonical_name="Perinatal Care Network / Regional Perinatal Programs of California",
        acronym="PCN / RPPC",
        federal_agency="California CDPH (Title V + Medi-Cal managed care)",
        authorizing_statute="California Health and Safety Code §123625; Title V match",
        tier=3,
        category="Perinatal Clinical Care Coordination",
        blueprint_goal=1,
        target_population="High-risk pregnant women on Medi-Cal; preterm birth, NICU, high-risk OB cases",
        core_services=[
            "High-risk obstetric consultation",
            "Perinatal case management",
            "NICU follow-up programs",
            "Perinatal outreach educator programs",
            "Regional perinatal transport coordination",
        ],
        county_aliases=[
            "Perinatal Care Network", "PCN", "Regional Perinatal Program",
            "RPPC", "high-risk pregnancy", "perinatal services",
            "perinatal outreach", "perinatal coordinator",
        ],
        federal_source_url="https://www.cdph.ca.gov/Programs/CFH/DMCAH/Pages/Domains/Perinatal-Services.aspx",
        state_specific="CA",
        notes=(
            "CA-specific regional network funded by CDPH. "
            "IN analog: Indiana Perinatal Quality Improvement Collaborative (IPQIC) "
            "serves a similar clinical coordination function but is hospital-facing, "
            "not county-health-dept-facing. "
            "Source: CDPH DMCAH."
        ),
    ),

    FederalProgram(
        program_id="FIMR_CA",
        canonical_name="Fetal and Infant Mortality Review",
        acronym="FIMR",
        federal_agency="HHS / HRSA / MCHB (via Title V SPRANS + state CDPH)",
        authorizing_statute="Title V SPRANS; California Health and Safety Code",
        tier=3,
        category="Surveillance & Quality Improvement",
        blueprint_goal=3,
        target_population="Retrospective review of fetal and infant deaths; indirectly benefits all pregnant women",
        core_services=[
            "Community-level review of infant/fetal deaths",
            "Root cause analysis",
            "Community action team recommendations",
        ],
        county_aliases=[
            "FIMR", "infant mortality review", "fetal mortality review",
            "perinatal mortality review", "infant death review",
        ],
        federal_source_url="https://www.hrsa.gov/fimr",
        state_specific="CA",
        notes=(
            "IN equivalent: Indiana has a Fatality Review and Prevention Division "
            "within ISDH, and a Maternal Mortality Review Committee (MMRC). "
            "Both states conduct this surveillance function; county websites "
            "rarely reference it directly. "
            "Source: CDPH, Indiana ISDH TVIS FY22."
        ),
    ),
]


# =============================================================================
# SECTION 3: INDIANA-SPECIFIC STATE PROGRAMS
# (State programs funded by IN legislature / Title V match; IN only)
# =============================================================================

INDIANA_PROGRAMS: List[FederalProgram] = [

    FederalProgram(
        program_id="HFI_IN",
        canonical_name="Healthy Families Indiana",
        acronym="HFI",
        federal_agency="Indiana DCS (funded via TANF + MIECHV + state funds)",
        authorizing_statute="Indiana state budget appropriation; Title V match; MIECHV Section 511 SSA",
        tier=3,
        category="Home Visiting - Indiana State Implementation of HFA",
        blueprint_goal=4,
        target_population="Families with newborns up to 3 months; all 92 IN counties",
        core_services=[
            "Voluntary evidence-based home visitation (HFA model)",
            "Child development support and parent education",
            "Child abuse/neglect prevention",
            "Access to health care navigation",
            "Referrals to WIC, Medicaid, DCS services",
        ],
        county_aliases=[
            "Healthy Families Indiana", "HFI", "Healthy Families",
            "home visiting DCS", "family support program Indiana",
        ],
        federal_source_url="https://secure.in.gov/dcs/prevention/healthy-families-indiana/",
        state_specific="IN",
        notes=(
            "Indiana-specific implementation of the HFA model. "
            "Unusually broad: available in ALL 92 IN counties via 31 agencies, 43 sites. "
            "Administered by DCS (unusual - most states use health dept). "
            "Funded by TANF + MIECHV + state funds. "
            "CA equivalent: Healthy Families America sites operated through county programs. "
            "Source: Indiana DCS HFI page, ISDH MIECHV page."
        ),
    ),

    FederalProgram(
        program_id="OB_NAVIGATOR_IN",
        canonical_name="My Healthy Baby / OB Navigator Program",
        acronym="OB Navigator / MHB",
        federal_agency="Indiana ISDH + FSSA + DCS (state-funded; Title V supplement)",
        authorizing_statute="Indiana House Enrolled Act 1007 (2019); Indiana state budget $3.3M",
        tier=3,
        category="Perinatal Navigation & Care Coordination",
        blueprint_goal=1,
        target_population=(
            "Pregnant Medicaid enrollees in high-risk counties; women whose medical "
            "records indicate positive pregnancy test; all 92 counties via referral"
        ),
        core_services=[
            "Perinatal navigator home visits during pregnancy and 6-12 months postpartum",
            "Early prenatal care engagement",
            "Referrals to home visiting programs (NFP, HFI)",
            "Wraparound service navigation (Medicaid, WIC, housing)",
            "Centralized intake and stratification across ISDH/FSSA/DCS",
        ],
        county_aliases=[
            "OB Navigator", "OB Navigator program", "My Healthy Baby",
            "perinatal navigator", "Medicaid prenatal navigation",
            "ISDH home visitor", "wraparound prenatal services",
        ],
        federal_source_url="https://mchb.tvisdata.hrsa.gov/Narratives/StateTitleVProgramPurposeAndDesign/09057fbb-4441-4280-b093-5944129c2001",
        state_specific="IN",
        notes=(
            "Indiana-specific. Established by HEA 1007 (2019) with $3.3M state budget. "
            "Renamed 'My Healthy Baby (MHB)' in later documentation. "
            "Live and making referrals to ALL 92 IN counties as of 2024. "
            "CA equivalent: CA has no exact analog - closest is CDPH PCN case management. "
            "Source: Indiana ISDH Title V TVIS FY24 narrative."
        ),
    ),

    FederalProgram(
        program_id="MOMS_HELPLINE_IN",
        canonical_name="MCH MOMS Helpline",
        acronym="MOMS Helpline",
        federal_agency="Indiana ISDH MCH Division (Title V funded)",
        authorizing_statute="Indiana Title V MCH program; state-funded ISDH initiative",
        tier=3,
        category="Maternal Health Navigation & Referral",
        blueprint_goal=1,
        target_population="All pregnant and postpartum Indiana women; especially those needing care navigation",
        core_services=[
            "Phone referrals to local prenatal care providers",
            "Connection to WIC, home visiting, Medicaid enrollment",
            "Information on community resources by county",
            "Advocacy and education for pregnant women",
        ],
        county_aliases=[
            "MOMS Helpline", "MCH MOMS Helpline", "1-844-MCH-MOMS",
            "1-844-624-6667", "maternal helpline Indiana",
            "pregnancy helpline Indiana",
        ],
        federal_source_url="https://www.in.gov/isdh/21047.htm",
        state_specific="IN",
        notes=(
            "Indiana-specific state hotline (1-844-MCH-MOMS). "
            "Distinct from the federal National Maternal Mental Health Hotline - "
            "MOMS Helpline is a general referral/navigation line, not mental-health-specific. "
            "CA equivalent: CA has no direct analog; 211 serves similar navigation role. "
            "Source: ISDH MCH MOMS Helpline page; PMC5651965 (Adams 2017)."
        ),
    ),

    FederalProgram(
        program_id="EARLY_START_IN",
        canonical_name="Early Start Program",
        acronym="Early Start",
        federal_agency="Indiana ISDH MCH Division (Title V funded)",
        authorizing_statute="Indiana Title V MCH program",
        tier=3,
        category="Early Prenatal Care Outreach",
        blueprint_goal=1,
        target_population="Newly diagnosed pregnant women; emphasis on first-trimester care entry in high-risk areas",
        core_services=[
            "Community outreach to engage women in first-trimester prenatal care",
            "Fast-track referrals to OB providers for high-risk cases",
            "Care coordination and follow-up",
        ],
        county_aliases=[
            "Early Start", "Early Start program", "prenatal outreach Indiana",
            "first trimester outreach", "early prenatal care program",
        ],
        federal_source_url="https://mchb.tvisdata.hrsa.gov/Narratives/PlanForTheApplicationYear1/bff17ed9-29c2-40bd-ab09-d7ac0ab8c507",
        state_specific="IN",
        notes=(
            "7 sites funded across Indiana by ISDH as of FY21; most in county health depts. "
            "Focuses on increasing first-trimester prenatal care entry. "
            "CA equivalent: no direct analog; Title V MCAH case management serves similar role. "
            "Source: Indiana ISDH Title V TVIS FY21 state action plan."
        ),
    ),

    FederalProgram(
        program_id="IPQIC_IN",
        canonical_name="Indiana Perinatal Quality Improvement Collaborative",
        acronym="IPQIC",
        federal_agency="Indiana ISDH (Title V SPRANS; AIM federal funding through HRSA)",
        authorizing_statute="Title V SPRANS; AIM federal funding via HRSA MCHB",
        tier=3,
        category="Perinatal Quality Improvement - Hospital-Based",
        blueprint_goal=2,
        target_population="Birthing hospitals across Indiana; indirectly all pregnant Hoosiers",
        core_services=[
            "AIM maternal safety bundle implementation (hemorrhage, hypertension)",
            "Substance use in pregnancy protocols and collaborative",
            "NAS surveillance and clinical guidelines",
            "Breastfeeding policy support for hospitals",
            "Perinatal Levels of Care certification",
        ],
        county_aliases=[
            "IPQIC", "Indiana Perinatal Quality Improvement Collaborative",
            "perinatal quality collaborative", "maternal safety collaborative Indiana",
            "AIM Indiana", "perinatal levels of care",
        ],
        federal_source_url="https://mchb.tvisdata.hrsa.gov/Narratives/AnnualReport1/97f43bcc-598d-4c66-a060-2a050ba4ab1f",
        state_specific="IN",
        notes=(
            "IN-specific analog to California's CMQCC (California Maternal Quality Care Collaborative). "
            "Both implement AIM bundles at the state QI level. "
            "Neither likely to appear on county health dept websites. "
            "Source: Indiana ISDH Title V TVIS FY20-22 narratives."
        ),
    ),

    FederalProgram(
        program_id="INDIANA_BREASTFEEDING_IN",
        canonical_name="Indiana Breastfeeding Alliance / State Breastfeeding Plan",
        acronym="IBA",
        federal_agency="Indiana ISDH MCH Division (Title V funded)",
        authorizing_statute="Indiana Title V MCH program; Indiana Code §16-35-6 (breastfeeding rights)",
        tier=3,
        category="Breastfeeding Support",
        blueprint_goal=5,
        target_population="All pregnant and postpartum Indiana women; particular focus on minority communities in urban counties",
        core_services=[
            "Hospital Baby-Friendly initiative support",
            "Provider education on breastfeeding",
            "Workplace lactation support advocacy",
            "Breastfeeding education via WIC clinics",
            "Indiana Black Breastfeeding Coalition partnership",
        ],
        county_aliases=[
            "Indiana Breastfeeding Alliance", "IBA", "breastfeeding support Indiana",
            "lactation support", "Baby-Friendly hospital",
            "breastfeeding program", "lactation consultant",
        ],
        federal_source_url="https://pmc.ncbi.nlm.nih.gov/articles/PMC5651965/",
        state_specific="IN",
        notes=(
            "IN-specific coordinated breastfeeding initiative via ISDH. "
            "CA equivalent: CDPH has a Breastfeeding Program under MCAH that is similar. "
            "Both funded through Title V. "
            "Source: PMC5651965 (Adams/Box 2017 Breastfeed Med); ISDH breastfeeding page."
        ),
    ),

    FederalProgram(
        program_id="MMRC_IN",
        canonical_name="Indiana Maternal Mortality Review Committee",
        acronym="MMRC",
        federal_agency="Indiana ISDH Fatality Review and Prevention Division (Title V SPRANS)",
        authorizing_statute="Indiana Code §16-38-3; Title V SPRANS",
        tier=3,
        category="Surveillance & Quality Improvement",
        blueprint_goal=3,
        target_population="Retrospective review of pregnancy-associated deaths in Indiana; improves outcomes for all pregnant Hoosiers",
        core_services=[
            "Review of all pregnancy-associated deaths",
            "Root cause and contributing factor analysis",
            "Recommendations to state legislature and providers",
            "Racial disparity analysis in maternal deaths",
        ],
        county_aliases=[
            "MMRC", "maternal mortality review", "maternal mortality committee",
            "pregnancy-associated death review", "maternal death review Indiana",
        ],
        federal_source_url="https://mchb.tvisdata.hrsa.gov/Narratives/PlanForTheApplicationYear1/97f43bcc-598d-4c66-a060-2a050ba4ab1f",
        state_specific="IN",
        notes=(
            "CA equivalent: CDPH PAMR (Pregnancy-Associated Mortality Review). "
            "Both are state-level surveillance; extremely unlikely to appear on county websites. "
            "Relevant as research/policy context. "
            "Source: Indiana ISDH TVIS FY22 annual report."
        ),
    ),
]


# =============================================================================
# SECTION 4: TEXAS-SPECIFIC STATE PROGRAMS
# (State programs funded by TX legislature / Title V match / CHIP; TX only)
#
# KEY STRUCTURAL DIFFERENCE FROM CA AND IN:
#   Texas has NOT expanded Medicaid under the ACA (as of 2026).
#   This means the standard Medicaid prenatal pathway that CA and IN rely on
#   is replaced by a layered system:
#     1. Medicaid for Pregnant Women (citizens/qualified immigrants <=198% FPL)
#     2. CHIP Perinatal (unborn child coverage for ineligible/undocumented <=202% FPL)
#     3. Title V Fee-for-Service (last-resort gap-fill for those ineligible for both)
# =============================================================================

TEXAS_PROGRAMS: List[FederalProgram] = [

    FederalProgram(
        program_id="CHIP_PERINATAL_TX",
        canonical_name="CHIP Perinatal Program",
        acronym="CHIP Perinatal",
        federal_agency="Texas HHSC (funded via federal CHIP Title XXI + state match)",
        authorizing_statute="Title XXI of the Social Security Act; Texas Health and Safety Code",
        tier=2,
        category="Healthcare Coverage - TX Substitute for Full Medicaid Expansion",
        blueprint_goal=1,
        target_population=(
            "Unborn children of pregnant women who cannot get Medicaid - including "
            "undocumented immigrants, lawful permanent residents, and women with "
            "income between 199-202% FPL. Available up to 202% FPL."
        ),
        core_services=[
            "Prenatal visits (up to 20) and prenatal vitamins",
            "Labor and delivery coverage (for unborn child)",
            "Two postpartum visits within 60 days for the mother",
            "Newborn coverage for 12 months after birth",
            "No copays or deductibles",
        ],
        county_aliases=[
            "CHIP Perinatal", "CHIP Perinate", "CHIP-P",
            "perinatal CHIP", "prenatal CHIP coverage",
            "unborn child coverage", "CHIP perinatal program Texas",
        ],
        federal_source_url="https://www.hhs.texas.gov/services/health/medicaid-chip/medicaid-chip-programs-services/medicaid-pregnant-women-chip-perinatal",
        state_specific="TX",
        notes=(
            "TX-specific substitute for full Medicaid expansion. Critical for "
            "undocumented and immigrant populations - Texas has the highest "
            "uninsured rate in the US (~17%). Coverage is legally for the "
            "UNBORN CHILD, not the mother; mother receives only 2 postpartum visits. "
            "CA equivalent: Medi-Cal covers undocumented residents fully. "
            "IN equivalent: standard Medicaid (no CHIP Perinatal workaround needed)."
        ),
    ),

    FederalProgram(
        program_id="TITLE_V_FFS_TX",
        canonical_name="Title V Maternal and Child Health Fee-for-Service Program",
        acronym="Title V FFS / TVFFS",
        federal_agency="Texas HHSC / DSHS (Title V federal funds + state match)",
        authorizing_statute="Title V of the Social Security Act; Texas Health and Safety Code",
        tier=2,
        category="Last-Resort Prenatal Care - TX Gap-Fill",
        blueprint_goal=1,
        target_population=(
            "Low-income women who are NOT eligible for Medicaid, CHIP, or CHIP Perinatal. "
            "Income <=185% FPL. Texas residents. Covers prenatal care and 90 days postpartum."
        ),
        core_services=[
            "Prenatal and postpartum clinical visits (up to 90 days after birth)",
            "Prenatal dental care",
            "Laboratory and diagnostic testing",
            "Counseling, education, and referrals",
            "Two bridge visits during CHIP Perinatal/Medicaid enrollment process",
        ],
        county_aliases=[
            "Title V FFS", "TVFFS", "Title V fee for service",
            "Title V maternal health program Texas",
            "MCH fee for service", "prenatal care program Texas",
            "low income prenatal care Texas",
        ],
        federal_source_url="https://www.hhs.texas.gov/services/health/title-v-maternal-child-health-fee-service-program",
        state_specific="TX",
        notes=(
            "TX-specific last-resort safety net for women excluded from both Medicaid "
            "and CHIP Perinatal. More expansive than most states' Title V gap-fill because "
            "TX has more uninsured women due to non-expansion."
        ),
    ),

    FederalProgram(
        program_id="HEALTHY_TEXAS_WOMEN_TX",
        canonical_name="Healthy Texas Women Program",
        acronym="HTW",
        federal_agency="Texas HHSC (funded via federal Title V + Medicaid family planning waiver)",
        authorizing_statute="Texas family planning state waiver; Title V of the SSA",
        tier=3,
        category="Reproductive & Interconception Health",
        blueprint_goal=1,
        target_population=(
            "Women ages 15-44 with low income and no insurance; "
            "includes postpartum women and women between pregnancies"
        ),
        core_services=[
            "Well-woman exams",
            "Family planning and contraception",
            "Screening for chronic conditions (diabetes, hypertension)",
            "Mental health screenings",
            "Referrals to prenatal care and other services",
        ],
        county_aliases=[
            "Healthy Texas Women", "HTW", "Texas women's health program",
            "women's health Texas", "family planning Texas",
            "interconception care Texas",
        ],
        federal_source_url="https://www.hhs.texas.gov/services/health/women-health/healthy-texas-women",
        state_specific="TX",
        notes=(
            "TX created HTW after defunding Planned Parenthood from state family "
            "planning programs in 2011-2013. Covers interconception period. "
            "CA equivalent: Family PACT (state-funded family planning, broader eligibility). "
            "IN equivalent: standard Medicaid family planning + Title X."
        ),
    ),

    FederalProgram(
        program_id="TEXASAIM_TX",
        canonical_name="Texas Alliance for Innovation on Maternal Health",
        acronym="TexasAIM",
        federal_agency="Texas DSHS (funded via Title V SPRANS + AIM federal grants via HRSA)",
        authorizing_statute="Title V SPRANS; AIM federal grant via HRSA MCHB",
        tier=3,
        category="Quality Improvement - Hospital-Based",
        blueprint_goal=2,
        target_population="Birthing hospitals across Texas; indirectly all pregnant Texans",
        core_services=[
            "Severe Hypertension in Pregnancy patient safety bundle (201 hospitals enrolled, 93% of TX births)",
            "Opioid and Substance Use Disorders (OSUD) patient safety bundle",
            "Sepsis in Obstetric Care patient safety bundle",
            "Obstetric hemorrhage protocols",
            "Hospital quality improvement learning collaboratives",
        ],
        county_aliases=[
            "TexasAIM", "Texas AIM", "Texas Alliance for Innovation on Maternal Health",
            "maternal safety bundle Texas", "obstetric quality improvement Texas",
        ],
        federal_source_url="https://www.dshs.texas.gov/maternal-child-health/programs-activities-maternal-child-health/texasaim",
        state_specific="TX",
        notes=(
            "TX equivalent of CA's CMQCC and IN's IPQIC. TexasAIM is notable for "
            "its scale: as of Aug 2024, 92% of TX birthing hospitals enrolled. "
            "Unlikely to appear on county health dept websites."
        ),
    ),

    FederalProgram(
        program_id="THV_TX",
        canonical_name="Texas Home Visiting Program",
        acronym="THV",
        federal_agency="Texas DFPS / HHSC Family Support Services (MIECHV + state PEI funds)",
        authorizing_statute="Via MIECHV Section 511 SSA; Texas Family Code; Prevention and Early Intervention (PEI) state appropriation",
        tier=3,
        category="Home Visiting - Texas State Implementation of MIECHV",
        blueprint_goal=4,
        target_population="Expectant and new parents with children 0-5 in at-risk communities; 85.5% of TX MIECHV families at <=200% FPL",
        core_services=[
            "Evidence-based home visiting via NFP, HFA, PAT, and HIPPY models",
            "Home Instruction for Parents of Preschool Youngsters (HIPPY)",
            "Family Connects (universal newborn home visit pilot, Travis County)",
            "HOPES: Healthy Outcomes through Prevention and Early Support",
        ],
        county_aliases=[
            "Texas Home Visiting", "THV", "home visiting Texas",
            "HIPPY", "Home Instruction for Parents of Preschool Youngsters",
            "Family Connects Texas", "HOPES program Texas",
        ],
        federal_source_url="https://www.dfps.texas.gov/Prevention_and_Early_Intervention/About_Prevention_and_Early_Intervention/thv.asp",
        state_specific="TX",
        notes=(
            "TX MIECHV is administered by DFPS + HHSC, not DSHS - unusual split administration. "
            "Uses 4 MIECHV models: NFP, HFA, PAT, HIPPY. "
            "Critical gap: only 3% of eligible TX families receive home visiting services "
            "(TexProtects 2024), far below CA and IN penetration rates."
        ),
    ),

    FederalProgram(
        program_id="MMMRC_TX",
        canonical_name="Texas Maternal Mortality and Morbidity Review Committee",
        acronym="MMMRC",
        federal_agency="Texas DSHS (Title V SPRANS + CDC Preventing Maternal Deaths Act funds)",
        authorizing_statute="Texas Health and Safety Code §34.015; CDC Preventing Maternal Deaths Act P.L. 115-344",
        tier=3,
        category="Surveillance & Quality Improvement",
        blueprint_goal=3,
        target_population="Retrospective review of pregnancy-associated deaths in Texas",
        core_services=[
            "Review of pregnancy-related and pregnancy-associated deaths",
            "Root cause and contributing factor analysis",
            "Biennial report and legislative recommendations",
            "Racial disparity analysis",
        ],
        county_aliases=[
            "MMMRC", "maternal mortality review Texas", "Texas maternal mortality committee",
            "pregnancy-related death review Texas",
        ],
        federal_source_url="https://www.dshs.texas.gov/maternal-child-health/healthy-texas-mothers-babies/maternal-mortality-morbidity-review-committee",
        state_specific="TX",
        notes=(
            "TX MMMRC is one of the most active state MMRCs given TX's high maternal mortality. "
            "2024 biennial report found 63% increase in maternal mortality 2018-2020. "
            "CA equivalent: CDPH PAMR. IN equivalent: ISDH MMRC."
        ),
    ),

    FederalProgram(
        program_id="HEAR_HER_TX",
        canonical_name="Hear Her Texas Campaign",
        acronym="Hear Her Texas",
        federal_agency="Texas DSHS MCH Division (Title V funds; CDC Hear Her national campaign)",
        authorizing_statute="Title V MCH Block Grant; CDC Hear Her national initiative",
        tier=3,
        category="Maternal Health Awareness & Warning Signs",
        blueprint_goal=2,
        target_population="Pregnant and postpartum women; healthcare providers; employers and community members across Texas",
        core_services=[
            "Public outreach on urgent maternal warning signs",
            "Influencer and social media campaign",
            "Provider education materials",
            "Emergency department engagement on maternal health",
        ],
        county_aliases=[
            "Hear Her Texas", "Hear Her campaign", "maternal warning signs Texas",
            "urgent maternal warning signs", "pregnancy warning signs campaign",
        ],
        federal_source_url="https://www.dshs.texas.gov/maternal-child-health/healthy-texas-mothers-babies/hear-her-texas",
        state_specific="TX",
        notes=(
            "TX implementation of the CDC's national Hear Her campaign. "
            "More prominent in TX than most states due to high maternal mortality."
        ),
    ),
]


# =============================================================================
# MASTER REGISTRY - combine all sections
# =============================================================================

FEDERAL_PROGRAM_REGISTRY: List[FederalProgram] = (
    UNIVERSAL_PROGRAMS + CALIFORNIA_PROGRAMS + INDIANA_PROGRAMS + TEXAS_PROGRAMS
)


# =============================================================================
# COMPARISON TABLE: CA vs IN vs TX for universal programs
# =============================================================================

STATE_PROGRAM_MAPPING = {
    "WIC": {
        "CA": "WIC (CDPH-administered; 280+ local agencies)",
        "IN": "WIC (ISDH-administered; 140 clinics, all 92 counties)",
        "TX": "WIC (DSHS-administered; 70+ local agencies statewide)",
    },
    "MEDICAID_PRENATAL": {
        "CA": "Medi-Cal (covers undocumented; 12-mo postpartum)",
        "IN": "Medicaid / Hoosier Healthwise (expansion state; 12-mo postpartum)",
        "TX": (
            "3-TIER SYSTEM: Medicaid for Pregnant Women (citizens) + "
            "CHIP_PERINATAL_TX (undocumented/immigrants) + TITLE_V_FFS_TX (last resort). "
            "NO full Medicaid expansion. Postpartum extended to 12 mo in 2024."
        ),
    },
    "TITLE_V_MCH": {
        "CA": "CDPH MCAH Division -> county LHDs",
        "IN": "ISDH MCH Division -> county health depts + nonprofits",
        "TX": (
            "DSHS MCH Division -> county health depts; "
            "also operates unique TITLE_V_FFS_TX direct service program"
        ),
    },
    "MIECHV": {
        "CA": "CDPH MIECHV -> NFP + HFA county sites",
        "IN": "ISDH/DCS co-lead -> NFP + HFI (HFA model, all 92 counties)",
        "TX": (
            "DFPS/HHSC co-lead -> NFP + HFA + PAT + HIPPY. "
            "Only 3% of eligible families served (TexProtects 2024) - critical gap."
        ),
    },
    "BIH_CA": {
        "CA": "BIH_CA -> operates in most CA counties",
        "IN": "NO EQUIVALENT - structural gap",
        "TX": (
            "NO EQUIVALENT - MMMRC tracks Black disparity but no dedicated "
            "community-based program for Black maternal health"
        ),
    },
    "OB_NAVIGATOR_IN": {
        "CA": "NO EQUIVALENT - closest: CDPH PCN case management",
        "IN": "OB_NAVIGATOR_IN / My Healthy Baby (all 92 counties via Medicaid data pipeline)",
        "TX": (
            "PARTIAL EQUIVALENT - HRMCCS_TX pilot (Smith + Cherokee counties only); "
            "no statewide perinatal navigation system"
        ),
    },
    "CHIP_PERINATAL_TX": {
        "CA": "NO EQUIVALENT - Medi-Cal covers undocumented residents directly",
        "IN": "NO EQUIVALENT - Medicaid expansion covers this population",
        "TX": "CHIP_PERINATAL_TX - critical TX-specific coverage workaround",
    },
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_by_tier(tier: int) -> List[FederalProgram]:
    """Return all programs with the given tier level."""
    return [p for p in FEDERAL_PROGRAM_REGISTRY if p.tier == tier]


def get_by_state(state_code: Optional[str]) -> List[FederalProgram]:
    """Get programs for a given state section: None=universal, 'CA', 'IN', or 'TX'."""
    return [p for p in FEDERAL_PROGRAM_REGISTRY if p.state_specific == state_code]


def get_applicable_programs(state_code: str) -> List[FederalProgram]:
    """Get all programs that apply to a given state (universal + state-specific)."""
    return [p for p in FEDERAL_PROGRAM_REGISTRY if p.state_specific in (None, state_code)]


def get_aliases_flat(state_code: Optional[str] = None) -> dict:
    """
    Returns {alias_lower: program_id} for fuzzy matching against county pages.
    If state_code provided, includes only universal + that state's programs.
    """
    progs = get_applicable_programs(state_code) if state_code else FEDERAL_PROGRAM_REGISTRY
    mapping = {}
    for prog in progs:
        for alias in prog.county_aliases:
            mapping[alias.lower()] = prog.program_id
        mapping[prog.acronym.lower()] = prog.program_id
    return mapping


def print_summary():
    print(f"\n{'='*68}")
    print(f"Federal Maternal Health Program Registry - {len(FEDERAL_PROGRAM_REGISTRY)} programs total")
    print(f"{'='*68}")
    sections = [
        ("UNIVERSAL (all states)", None),
        ("CALIFORNIA-SPECIFIC",    "CA"),
        ("INDIANA-SPECIFIC",       "IN"),
        ("TEXAS-SPECIFIC",         "TX"),
    ]
    for label, state in sections:
        progs = get_by_state(state)
        print(f"\n  -- {label} ({len(progs)} programs) --")
        for tier in [1, 2, 3]:
            tier_progs = [p for p in progs if p.tier == tier]
            if tier_progs:
                tier_label = {1: "Tier 1 Universal", 2: "Tier 2 State-wide", 3: "Tier 3 Selective"}[tier]
                print(f"    [{tier_label}]")
                for p in tier_progs:
                    print(f"      {p.program_id:30s} | {p.acronym}")

    print(f"\n  -- CA / IN / TX COMPARISON --")
    for univ_id, mapping in STATE_PROGRAM_MAPPING.items():
        print(f"    {univ_id}")
        for state, desc in mapping.items():
            print(f"      {state}: {desc}")


if __name__ == "__main__":
    print_summary()
    print("\n  CA alias lookup (sample):")
    ca_aliases = get_aliases_flat("CA")
    for alias, pid in list(ca_aliases.items())[:8]:
        print(f"    '{alias}' -> {pid}")
    print("\n  IN alias lookup (sample):")
    in_aliases = get_aliases_flat("IN")
    for alias, pid in list(in_aliases.items())[:8]:
        print(f"    '{alias}' -> {pid}")
