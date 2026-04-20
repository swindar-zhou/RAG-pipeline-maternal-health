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

# Manual HTML overrides — for Cloudflare-blocked counties the operator cannot
# bypass programmatically. To use: open the county page in Chrome, File → Save
# As → Webpage Complete, save as data/manual_html/<County Name>.html
# (spaces preserved, e.g. "Contra Costa.html").
MANUAL_HTML_DIR = os.path.join(PROJECT_ROOT, "data", "manual_html")

# Counties whose MCAH pages block automated requests (403 / bot-detection).
# For these counties the scraper uses a three-tier fetch chain:
#   1. curl-cffi  — Chrome TLS fingerprint impersonation (fastest, no browser)
#   2. Playwright — headless Chromium with stealth patches (JS-rendered pages)
#   3. aiohttp    — plain HTTP fallback (rarely succeeds for these counties)
# Updated 2026-04-17 based on Phase 1 zero-result run.
BOT_BLOCKED_COUNTIES: set = {
    "Alameda",        # HTTP 403 — Incapsula WAF
    "Amador",
    "Contra Costa",
    "El Dorado",
    "Fresno",
    "Glenn",
    "Kern",
    "Madera",
    "Mendocino",
    "Monterey",
    "Santa Barbara",  # JS-rendered CivicPlus site — aiohttp returns empty body
    "Santa Clara",    # HTTP 403 — Incapsula WAF
    "Shasta",
    "Tulare",         # HTTP 403 — Incapsula WAF
    "Tuolumne",
    "Ventura",        # HTTP 403 — Incapsula WAF
    "Yolo",
}

# Backward-compatible alias (phase2_enhanced.py imports this name)
PLAYWRIGHT_REQUIRED_COUNTIES = BOT_BLOCKED_COUNTIES

# Validated maternal health section URLs — human-checked, 2026-04-16
# Source: maternal_health_urls.json (46 verified, confidence="verified")
# All 46 entries below are direct MCAH/MCH program pages on official county health domains.
# 10 URLs were corrected vs. the prior config (domain moves, stale slugs — see notes inline).
MATERNAL_HEALTH_URLS = {
    # ── Bay Area ──────────────────────────────────────────────────────────────
    "Alameda":        "https://health.alamedacountyca.gov/department/public-health-department/",  # acphd.org/mpcah/ redirects here; new domain health.alamedacountyca.gov
    "Contra Costa":   "https://www.cchealth.org/services-and-programs/support-for-families/family-maternal-child-health-fmch",  # direct FMCH sub-page; 403 — blocks automated requests
    "Marin":          "https://www.marinhhs.org/maternal-child-adolescent-health",
    "Napa":           "https://www.napacounty.gov/3237/Home-Visiting-Programs",  # closest entry — see INFERRED note
    "San Francisco":  "https://www.sf.gov/departments--department-public-health--maternal-child-and-adolescent-health",
    "San Mateo":      "https://www.smchealth.org/mcah",
    "Santa Clara":    "https://publichealth.santaclaracounty.gov/health-information/child-health-pregnancy-and-parenting",  # updated path
    "Santa Cruz":     "https://www.santacruzhealth.org/PublicHealth/ChildrenFamilyHealth/MCAH.aspx",  # updated domain
    "Solano":         "https://www.solanocounty.gov/government/health-social-services-hss/solano-public-health/maternal-child-adolescent-health",
    "Sonoma":         "https://sonomacounty.gov/health-and-human-services/health-services/divisions/public-health/maternal-child-and-adolescent-health",
    # ── Central Valley ───────────────────────────────────────────────────────
    "Fresno":         "https://www.fresnocountyca.gov/Departments/Public-Health/Public-Health-Nursing/Maternal-Child-and-Adolescent-Health-MCAH",  # updated domain fresnocountyca.gov; 403 — blocks automated requests
    "Kern":           "https://www.kernpublichealth.com/healthy-community/women-s-health/maternal-child-adolescent-health",  # updated path; 403 — blocks automated requests
    "Kings":          "https://www.kcdph.com/nursing",
    "Madera":         "https://www.maderacounty.com/government/public-health/maternal-child-and-adolescent-health-program",  # 403 — blocks automated requests
    "Merced":         "https://www.countyofmerced.com/616/MCAH-Home-Visiting",  # co.merced.ca.us → countyofmerced.com (domain moved)
    "San Joaquin":    "https://cms.sjcphs.org/phs/programs-and-services/family-health-programs",  # no standalone MCAH page — see INFERRED note
    "Stanislaus":     "https://www.schsa.org/PublicHealth/programs/maternal-child-adolescent-health/",  # /mainpages/mcah/ → /programs/maternal-child-adolescent-health/ (redirect dest)
    "Tulare":         "https://tchhsa.org/eng/public-health/maternal-child-and-adolescent-health-mcah-program",
    # ── Greater Los Angeles ───────────────────────────────────────────────────
    "Los Angeles":    "http://publichealth.lacounty.gov/mch/",
    "Orange":         "https://www.ochealthinfo.com/services/community-and-nursing-services/maternal-child-and-adolescent-health-mcah",
    "Riverside":      "https://www.ruhealth.org/public-health/nursing-maternal-child-adolescent-health",  # updated domain ruhealth.org
    "San Bernardino": "https://dph.sbcounty.gov/programs/fhs/mcah/",
    "Ventura":        "https://hca.venturacounty.gov/public-health/health-care-for-all/",  # no dedicated MCAH page — see INFERRED note
    # ── Sacramento Region ────────────────────────────────────────────────────
    "El Dorado":      "https://www.eldoradocounty.ca.gov/Health-Well-Being/Public-Health/Pregnant-Women-Children-Teens-and-Families/Maternal-Child-Adolescent-Health-MCAH-and-California-Home-Visiting-Programs",  # updated domain; 403 — blocks automated requests
    "Placer":         "https://www.placer.ca.gov/2918/Women-Infants-Children-WIC",  # no dedicated MCAH page — see INFERRED note
    "Sacramento":     "https://dhs.saccounty.gov/PUB/Program/Pages/SP-Maternal-Child-and-Adolescent-Health-Program.aspx",
    "Sutter":         "https://www.sutter.gov/government/county-departments/health-and-human-services/public-health-branch/maternal-child-adolescent-health",  # suttercounty.org → sutter.gov (domain moved)
    "Yolo":           "https://www.yolocounty.gov/government/general-government-departments/health-human-services/boards-committees/mcah-advisory-board",  # advisory board only — see INFERRED note; 403 — blocks automated requests
    "Yuba":           "https://agendasuite.org/iip/yuba/file/getfile/30813",  # PDF seed — handled by pdf-seed detection; no dedicated MCAH page
    # ── San Diego & Imperial ──────────────────────────────────────────────────
    "Imperial":       "https://www.icphd.org/health-information-and-resources/maternal-child-adolescent-health",
    "San Diego":      "https://www.sandiegocounty.gov/content/sdc/hhsa/programs/phs/maternal_child_family_health_services.html",
    # ── Central Coast ────────────────────────────────────────────────────────
    "Monterey":       "https://www.countyofmonterey.gov/government/departments-a-h/health/public-health/maternal-child-adolescent-health-mcah",  # 403 — blocks automated requests
    "San Benito":     "https://hhsa.sanbenitocountyca.gov/maternal-child-adolescent-health/",
    "San Luis Obispo": "https://www.slocounty.ca.gov/departments/health-agency/public-health/all-public-health-services/maternal-child-health/maternal,-child-adolescent-health",
    "Santa Barbara":  "https://www.countyofsb.org/1680/Maternal-Child-Adolescent-Health",
    # ── North Coast ──────────────────────────────────────────────────────────
    "Del Norte":      "https://www.co.del-norte.ca.us/departments/PublicHealth/MCAH",
    "Humboldt":       "https://humboldtgov.org/1013/Maternal-Child-Adolescent-Health",
    "Lake":           "https://www.lakecountyca.gov/545/Maternal-Child-Adolescent-Health",
    "Mendocino":      "https://www.mendocinocounty.gov/departments/public-health/nursing/maternal-child-adolescent-health-programs",  # updated domain .gov; 403 — blocks automated requests
    # ── Sierra Nevada / Foothills ────────────────────────────────────────────
    "Amador":         "https://www.amadorcounty.gov/services/public-health/aaaaa",  # amadorgov.org → amadorcounty.gov (redirect dest); unusual slug; 403 — blocks automated requests
    "Butte":          "https://www.buttecounty.net/1145/Maternal-Child-Adolescent-Health-Program",
    "Calaveras":      "https://publichealth.calaverasgov.us/Programs/Maternal-Child-Adolescent-Health-MCAH",
    "Mariposa":       "http://www.mariposacounty.gov/1588/Maternal-Child-and-Adolescent-Health-MCA",  # mariposacounty.org → mariposacounty.gov (domain moved)
    "Nevada":         "https://www.nevadacountyca.gov/3546/Maternal-Child-Adolescent-Health",
    "Plumas":         "https://www.plumascounty.us/2542/Maternal-Child-Adolescent-Program-MCAH",
    "Sierra":         "https://www.sierracounty.ca.gov/282/Maternal-Child-Adolescent-Health-MCAH",
    "Tuolumne":       "https://www.tuolumnecounty.ca.gov/257/Maternal-Child-and-Adolescent-Health",  # updated slug /257/
    # ── Northeast / High Desert ──────────────────────────────────────────────
    "Alpine":         "https://www.alpinecountyca.gov/283/Perinatal-Outreach",  # no dedicated MCAH page — see INFERRED note
    "Colusa":         "https://www.countyofcolusaca.gov/285/Maternal-Child-Adolescent-Health-Program",
    "Glenn":          "https://www.countyofglenn.net/government/departments/health-human-services/public-health/services/maternal-child-adolescent-health-mcah",  # 403 — blocks automated requests
    "Inyo":           "https://www.inyocounty.us/public-health-clinic/maternal-child-adolescent-health-mcah",
    "Lassen":         "https://www.lassencounty.org/dept/public-health/public-health-programs-and-services/maternal-child-adolescent-health-mcah",
    "Modoc":          "https://publichealth.co.modoc.ca.us/children___families/index.php",  # no dedicated MCAH page — see INFERRED note
    "Mono":           "https://www.monohealth.com/hhs/page/women-maternal-health",
    "Shasta":         "https://www.shastacounty.gov/health-human-services/page/pregnancy-children-and-parenting",  # updated domain shastacounty.gov
    "Siskiyou":       "https://www.siskiyoucounty.gov/publichealth/page/maternal-child-and-adolescent-health-mcah",  # co.siskiyou.ca.us → siskiyoucounty.gov (domain moved)
    "Tehama":         "https://www.tehamacohealthservices.net/our-services/public-health/services/wic/",  # no dedicated MCAH page — see INFERRED note
    "Trinity":        "https://www.trinitycounty.org/441/Women-Infants-Children-WIC",  # no dedicated MCAH page — see INFERRED note
}

# Entries above flagged "see INFERRED note" are the 12 counties where no standalone MCAH page
# was found. The URLs are the closest available entry point (WIC page, advisory board, related
# program). Each needs a manual browser check before being relied on for scraping.
#
# Inferred counties (confidence="inferred"):
#   Alpine, Amador, Modoc, Napa, Placer, San Joaquin, Tehama, Trinity, Ventura, Yolo, Yuba, Mono
#
# For Yuba (agendasuite.org URL) — strongly recommend finding a replacement on yuba.gov or
# contracting agency (Youth for Change) before running Phase 2 on that county.

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

