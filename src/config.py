"""
Configuration constants and county mappings.
"""

import os
from dotenv import load_dotenv

load_dotenv()

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
    "Kern": "https://www.kerncounty.com/",
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

SECTION_KEYWORDS = [
    "maternal health", "maternal child health", "mch", "mcah",
    "women's health", "family health", "perinatal", "reproductive health",
    "prenatal", "postpartum",
]

PROGRAM_KEYWORDS = [
    "healthy start", "wic", "home visiting", "miechv",
    "black infant health", "first 5", "nurse-family partnership",
    "title v", "perinatal equity", "postpartum", "breastfeeding",
    "lactation", "family planning", "parents as teachers", "nfp"
]

# Scraping settings
REQUEST_TIMEOUT = 20
DELAY_BETWEEN_REQUESTS = 2
MAX_CONTENT_LENGTH = 12000
MAX_TEXT_CHARS = 20000

# LLM settings
MAX_INPUT_CHARS = 10000
OPENAI_MODEL = "gpt-4o-mini"
OPENAI_MAX_TOKENS = 1500
TEMPERATURE = 0.1
SLEEP_BETWEEN_CALLS = 0.5

