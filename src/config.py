"""
Configuration constants and county mappings.
"""

import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(PROJECT_ROOT, ".env")


def _load_env_fallback(path: str, override: bool = True) -> None:
    """Minimal .env loader used when python-dotenv is unavailable."""
    if not os.path.exists(path):
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
            for raw in f:
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip("'").strip('"')
                if not key:
                    continue
                if override or key not in os.environ:
                    os.environ[key] = value
    except Exception:
        # Non-fatal: app can still run with existing env vars.
        pass


# Try to load .env file, but don't fail if dotenv is not installed
try:
    from dotenv import load_dotenv
    # Explicit path is robust when running scripts from any directory.
    load_dotenv(dotenv_path=ENV_PATH, override=True)
except ImportError:
    _load_env_fallback(ENV_PATH, override=True)

# Project constants
STATE_NAME = "California"
DATA_COLLECTOR_NAME = os.getenv("DATA_COLLECTOR_NAME", "Your Name")

# All 58 California counties with official URLs
CALIFORNIA_COUNTIES = {
    "Alameda": "https://www.acgov.org/",
    "Alpine": "https://www.alpinecountyca.gov/",
    "Amador": "https://www.amadorgov.org/",
    "Butte": "https://www.buttecounty.net/",
    "Calaveras": "https://www.calaverasgov.us/",
    "Colusa": "https://www.countyofcolusa.org/",
    "Contra Costa": "https://www.contracosta.ca.gov/",
    "Del Norte": "https://www.dnco.org/",
    "El Dorado": "https://www.edcgov.us/",
    "Fresno": "https://www.co.fresno.ca.us/",
    "Glenn": "https://www.countyofglenn.net/",
    "Humboldt": "https://www.humboldtgov.org/",
    "Imperial": "https://www.co.imperial.ca.us/",
    "Inyo": "https://www.inyocounty.us/",
    "Kern": "https://www.kernpublichealth.com/",
    "Kings": "https://www.countyofkings.com/",
    "Lake": "https://www.lakecountyca.gov/",
    "Lassen": "https://www.lassencounty.org/",
    "Los Angeles": "https://www.lacounty.gov/",
    "Madera": "https://www.maderacounty.com/",
    "Marin": "https://www.marincounty.org/",
    "Mariposa": "https://www.mariposacounty.org/",
    "Mendocino": "https://www.mendocinocounty.org/",
    "Merced": "https://www.co.merced.ca.us/",
    "Modoc": "https://www.co.modoc.ca.us/",
    "Mono": "https://monocounty.ca.gov/",
    "Monterey": "https://www.co.monterey.ca.us/",
    "Napa": "https://www.countyofnapa.org/",
    "Nevada": "https://www.mynevadacounty.com/",
    "Orange": "https://www.ocgov.com/",
    "Placer": "https://www.placer.ca.gov/",
    "Plumas": "https://www.plumascounty.us/",
    "Riverside": "https://www.rivco.org/",
    "Sacramento": "https://www.saccounty.net/",
    "San Benito": "https://www.cosb.us/",
    "San Bernardino": "https://www.sbcounty.gov/",
    "San Diego": "https://www.sandiegocounty.gov/",
    "San Francisco": "https://sf.gov/",
    "San Joaquin": "https://www.sjgov.org/",
    "San Luis Obispo": "https://www.slocounty.ca.gov/",
    "San Mateo": "https://www.smcgov.org/",
    "Santa Barbara": "https://www.countyofsb.org/",
    "Santa Clara": "https://www.sccgov.org/",
    "Santa Cruz": "https://www.santacruzcounty.us/",
    "Shasta": "https://www.co.shasta.ca.us/",
    "Sierra": "https://www.sierracounty.ca.gov/",
    "Siskiyou": "https://www.co.siskiyou.ca.us/",
    "Solano": "https://www.solanocounty.com/",
    "Sonoma": "https://sonomacounty.ca.gov/",
    "Stanislaus": "https://www.stancounty.com/",
    "Sutter": "https://www.suttercounty.org/",
    "Tehama": "https://www.co.tehama.ca.us/",
    "Trinity": "https://www.trinitycounty.org/",
    "Tulare": "https://tularecounty.ca.gov/",
    "Tuolumne": "https://www.tuolumnecounty.ca.gov/",
    "Ventura": "https://www.ventura.org/",
    "Yolo": "https://www.yolocounty.org/",
    "Yuba": "https://www.yuba.org/"
}

# Discovery keywords
DEPT_KEYWORDS = [
    "health department", "health services", "public health",
    "health and human services", "hhs", "hhsa", "department of public health",
]

# Keywords for finding maternal health sections (high priority)
SECTION_KEYWORDS = [
    # Primary maternal health terms
    "maternal health", "maternal child health", "mch", "mcah",
    "maternal child family health", "maternal child adolescent health",
    "women's health", "family health", "perinatal", "reproductive health",
    "prenatal", "postpartum", "pregnancy", "pregnant",
    # Exclude these general terms that dilute focus (per advisor feedback)
    # Keeping focus on maternal-specific sections
]

# Keywords for identifying specific maternal health programs (per advisor feedback)
# Focus on well-defined maternal health programs, not general health services
PROGRAM_KEYWORDS = [
    # Federal/State maternal health programs
    "wic", "women infants children",
    "home visiting", "miechv", "maternal infant early childhood",
    "healthy start", "black infant health", "bih",
    "nurse-family partnership", "nfp", "parents as teachers",
    "first 5", "title v", "title five",
    # Maternal-specific services
    "prenatal care", "prenatal services", "prenatal program",
    "postpartum", "postpartum support", "postpartum care",
    "perinatal", "perinatal services", "perinatal equity",
    "breastfeeding", "lactation", "lactation support",
    "midwife", "midwifery", "doula",
    "childbirth", "birth", "labor and delivery",
    "family planning", "reproductive health",
    "infant mortality", "maternal mortality",
    # California-specific programs
    "comprehensive perinatal services program", "cpsp",
    "california home visiting program", "chvp",
    "adolescent family life program", "aflp",
    "perinatal outreach and education", "poem",
]

# Scraping settings
REQUEST_TIMEOUT = 20
DELAY_BETWEEN_REQUESTS = 2
MAX_CONTENT_LENGTH = 12000
MAX_TEXT_CHARS = 20000

# Validated maternal health section URLs (from advisor's manual review)
# These are the correct entry points for maternal health programs in each county
MATERNAL_HEALTH_URLS = {
    # Gold-standard validated (Phase 1 ground truth)
    "San Diego":      "https://www.sandiegocounty.gov/content/sdc/hhsa/programs/phs/maternal_child_family_health_services.html",
    "Los Angeles":    "http://publichealth.lacounty.gov/mch/",
    "Sacramento":     "https://dhs.saccounty.gov/PUB/Program/Pages/SP-Maternal-Child-and-Adolescent-Health-Program.aspx",
    "San Francisco":  "https://www.sf.gov/departments--department-public-health--maternal-child-and-adolescent-health",
    # Volatile counties — stabilize with validated seeds
    "Contra Costa":   "https://cchealth.org/services-and-programs/maternal-child-and-adolescent-health/",
    "Riverside":      "https://www.rivcoeh.org/Programs/Maternal-Child-and-Adolescent-Health",
    "Santa Cruz":     "https://www.santacruzcounty.us/Health-Human-Services/Public-Health/Programs-and-Services/Maternal-Child-Adolescent-Health",
    "Kern":           "https://www.kernpublichealth.com/programs/mcah/",
    # Persistently-zero counties — direct MCH entry points
    "El Dorado":      "https://www.edcgov.us/Government/PublicHealth/MCAH/Pages/MCAH.aspx",
    "Fresno":         "https://www.co.fresno.ca.us/departments/public-health-and-animal-services/public-health/programs-services/maternal-child-adolescent-health-mcah",
    "Mendocino":      "https://www.mendocinocounty.org/government/health-human-services/public-health/programs-services/maternal-child-adolescent-health",
    "Santa Clara":    "https://publichealth.santaclaracounty.gov/programs-services/maternal-child-and-adolescent-health-mcah",
    "Shasta":         "https://www.co.shasta.ca.us/departments/health-and-human-services/public-health/community-health/maternal-child-adolescent-health",
    "Tuolumne":       "https://www.tuolumnecounty.ca.gov/175/Public-Health",
}

# State-level reference pages (for training/learning what maternal health programs look like)
STATE_REFERENCE_URLS = {
    "California": "https://www.cdph.ca.gov/Programs/CFH/DMCAH/Pages/Domains/Maternal-Health.aspx",
    "Florida_pregnancy": "https://www.floridahealth.gov/individual-family-health/womens-health/pregnancy/",
    "Florida_wic": "https://www.floridahealth.gov/individual-family-health/womens-health/wic/",
}

# Known health department URLs (general entry points, fallback if no maternal URL)
HEALTH_DEPT_URLS = {
    "Alameda":        "https://www.acgov.org/services/",
    "Sacramento":     "https://dhs.saccounty.gov/PUB/Pages/PUB-Home.aspx",
    "Los Angeles":    "https://www.lacounty.gov/",
    "San Francisco":  "https://www.sf.gov/departments--department-public-health",
    "Orange":         "https://www.ochealthinfo.com/services-programs",
    "Santa Clara":    "https://publichealth.santaclaracounty.gov/services",
    "Contra Costa":   "https://www.cchealth.org/services-and-programs/",
    # Tier-3 fallback improvements for hard-to-discover counties
    "El Dorado":      "https://www.edcgov.us/Government/PublicHealth/Pages/Public-Health.aspx",
    "Fresno":         "https://www.co.fresno.ca.us/departments/public-health-and-animal-services/public-health",
    "Mendocino":      "https://www.mendocinocounty.org/government/health-human-services/public-health",
    "Shasta":         "https://www.co.shasta.ca.us/departments/health-and-human-services/public-health",
    "Tuolumne":       "https://www.tuolumnecounty.ca.gov/175/Public-Health",
    "Kern":           "https://www.kernpublichealth.com/",
    "Riverside":      "https://www.rivcoeh.org/",
    "Santa Cruz":     "https://www.santacruzcounty.us/Health-Human-Services/Public-Health",
    "Yolo":           "https://www.yolocounty.org/health-human-services/public-health",
    "San Joaquin":    "https://www.sjgov.org/department/phss",
    "Merced":         "https://www.co.merced.ca.us/116/Public-Health",
    "San Mateo":      "https://www.smchealth.org/programs-services",
    "Madera":         "https://maderacounty.com/government/public-health",
    "Yuba":           "https://www.yuba.org/departments/health-human-services/public-health/",
    "Glenn":          "https://www.countyofglenn.net/govt/departments/health-human-services/public-health/",
}

# LLM settings
MAX_INPUT_CHARS = 10000
OPENAI_MODEL = "gpt-4o-mini"
OPENAI_MAX_TOKENS = 1500
TEMPERATURE = 0.1
SLEEP_BETWEEN_CALLS = 0.5

