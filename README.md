![alt text](women-feeding.png) 

# Closing the Maternal Health Information Gap: An Agentic RAG Pipeline for County-Level Program Discovery

## ([Paper Link](https://drive.google.com/file/d/12XLt5OXnlSFes3R4pPXsMXbYCfNT3a_1/view?usp=sharing))

## Background

### The Problem: Maternal Health Crisis in the United States

The United States faces a significant maternal health crisis. Key statistics:

- **Maternal mortality**: The U.S. has the highest maternal mortality rate among developed nations, with rates rising over the past two decades
- **Racial disparities**: Black women are 3-4 times more likely to die from pregnancy-related causes than white women
- **Maternity care deserts**: Over 2 million women of childbearing age live in counties with no obstetric hospitals or birth centers, and no obstetric providers ([March of Dimes, 2022](https://www.marchofdimes.org/maternity-care-deserts-report))
- **Declining birth rates**: Birth rates have become a global concern, making maternal health support increasingly critical

### Current Situation: Fragmented Information

Maternal health programs exist at federal, state, and county levels, but information about them is:

- **Scattered** across hundreds of county government websites
- **Inconsistently structured** - each county organizes information differently
- **Hard to discover** - programs are buried in complex website hierarchies
- **Not centralized** - no comprehensive database of county-level maternal health programs exists

This fragmentation makes it difficult for:
- Researchers to study program availability and coverage
- Policymakers to identify gaps in maternal health services
- Pregnant women and families to find available resources

### Project Scope: Building a Maternal Health Program Database

This project aims to create a **structured, searchable database** of county-level maternal health programs by:

1. **Automated discovery** - Using web scraping to find maternal health program pages on county websites
2. **Information extraction** - Using LLMs to extract program details (eligibility, services, contacts)
3. **Standardized output** - Producing structured data that can be analyzed and compared across counties
4. **Gap analysis** - Detecting programs missing from the registry using TF-IDF semantic matching

**Current scope**: California (all 58 counties)

**Target programs**: WIC, Black Infant Health, Nurse-Family Partnership, Perinatal Care Networks, Home Visiting Programs, Breastfeeding Support, Teen Pregnancy Programs, and other maternal/child health services

### Theoretical Framework

This project's program taxonomy is grounded in established public health frameworks:

#### Social Determinants of Health (SDOH)

Based on the WHO Conceptual Framework (Solar & Irwin, 2010), we recognize that maternal health outcomes are shaped by:
- **Healthcare Access** - availability of prenatal, delivery, and postpartum care
- **Quality of Care** - patient voice, equity, culturally appropriate care
- **Social Support** - community health workers, doulas, home visiting
- **Economic Stability** - nutrition programs, workplace protections
- **Neighborhood Environment** - environmental exposures, housing

#### White House Blueprint for Addressing the Maternal Health Crisis (2022)

The Biden-Harris Administration's five-goal framework provides structure for our program categories:
1. **Healthcare Access & Coverage** - comprehensive maternal health services
2. **Quality of Care & Patient Voice** - accountable, equitable care systems
3. **Data Collection & Research** - evidence-based practices
4. **Perinatal Workforce** - doulas, midwives, community health workers
5. **Social & Economic Supports** - WIC, housing, food security

### References

**SDOH Framework:**
- Braveman, P., Egerter, S., & Williams, D. R. (2011). The social determinants of health: coming of age. *Annual Review of Public Health*, 32(1), 381-398.
- Braveman, P., & Gottlieb, L. (2014). The social determinants of health: it's time to consider the causes of the causes. *Public Health Reports*, 129(1_suppl2), 19-31.
- Marmot, M., Allen, J., Bell, R., Bloomer, E., & Goldblatt, P. (2012). WHO European review of social determinants of health and the health divide. *The Lancet*, 380(9846), 1011-1029.
- Solar, O., & Irwin, A. (2010). A conceptual framework for action on the social determinants of health. WHO Document Production Services.

**Maternal Health Policy:**
- White House. (2022). *Blueprint for Addressing the Maternal Health Crisis*. [Link](https://bidenwhitehouse.archives.gov/wp-content/uploads/2022/06/Maternal-Health-Blueprint.pdf)
- March of Dimes. (2022). *Maternity Care Deserts Report*. [Link](https://www.marchofdimes.org/maternity-care-deserts-report)
- California Department of Public Health. *Maternal, Child and Adolescent Health Division*. [Link](https://www.cdph.ca.gov/Programs/CFH/DMCAH/Pages/Domains/Maternal-Health.aspx)

**Methods:**
- Grimmer, J., Roberts, M. E., & Stewart, B. M. (2022). *Text as Data: A New Framework for Machine Learning and the Social Sciences*. Princeton University Press.

---

## Overview

This pipeline discovers and extracts **maternal health programs** (WIC, Black Infant Health, Nurse-Family Partnership, etc.) from all 58 California county government websites. It uses a 3-phase approach — Discovery → Extraction → Structuring — followed by automated Gap Analysis.

## Quick Start

```bash
# 1. Setup
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-langchain.txt   # for RAG + Program Finder

# 2. Configure API key
cp .env.example .env
# Edit .env and add your OpenAI API key

# 3. Run the full pipeline (scrape → structure → index)
python run_pipeline.py

# 4. Launch the interactive Program Finder
python -m src.knowledge_graph
```

## How It Works

```
PHASE 1: DISCOVERY          PHASE 2: EXTRACTION           PHASE 3: STRUCTURING
┌──────────────────┐        ┌────────────────────┐        ┌─────────────────────┐
│ DuckDuckGo search│   ──▶  │ Fetch Program      │   ──▶  │ LLM → Structured    │
│ + validated URLs │        │ Page Content       │        │ CSV Output (vN)     │
│ + fallback crawl │        │ (text, contacts,   │        │ + registry match    │
│                  │        │  PDF links)        │        │ + gap candidates    │
└──────────────────┘        └────────────────────┘        └─────────────────────┘
         │                           │                              │
         │                           ▼                              ▼
         │                  ┌────────────────────┐        ┌─────────────────────┐
         │                  │ RAG INDEX          │        │ GAP ANALYSIS        │
         │                  │ ChromaDB per-county│        │ TF-IDF similarity   │
         │                  │ vectorstore        │        │ vs. 31-program      │
         │                  │ (text-embedding-   │        │ federal registry    │
         │                  │  3-small, 800-char │        └─────────────────────┘
         │                  │  chunks)           │
         │                  └─────────┬──────────┘
         │                            │
         ▼                            ▼
┌──────────────────────────────────────────────────────┐
│ PROGRAM FINDER  (src/knowledge_graph.py)             │
│ ZIP code → county (pgeocode, offline)                │
│   Path A: Structured CSV (fast, no LLM)              │
│   Path B: RAG + GPT-4o-mini (fallback for            │
│           counties without structured CSV)           │
└──────────────────────────────────────────────────────┘
```

### Phase 1 — Discovery (`scraper_discovery.py`)

3-tier strategy per county:
- **Tier 1**: Use advisor-validated MCH URLs directly (highest precision)
- **Tier 2**: DuckDuckGo search for county MCH page on the county's own domain
- **Tier 3**: Fall back to known health dept URL or county root

Link scoring uses a 2-layer taxonomy:
- **Layer 1**: Federal Program Registry aliases (31 known programs, +3.0 score) — high precision
- **Layer 2**: Maternal taxonomy keywords (`src/maternal_taxonomy.py`, +2.0) — broader recall

### Phase 2 — Extraction (`scraper_extract.py`)

- Fetches each discovered program page
- Extracts: full text content, phone/email contacts, PDF links, registry signals

### Phase 3 — Structuring (`scraper_structure.py`)

- Sends page content to GPT-4o-mini with registry-grounded prompt
- Async batch LLM calls (up to 5 concurrent) — ~3x faster than sequential
- Each extracted program is matched to a `program_id` from the Federal Program Registry
- Unmatched programs flagged as gap candidates
- Output saved to a new versioned directory (`data/structured/vN`) on every run

### RAG Index (`src/vector_store.py`)

Builds a per-county **ChromaDB vectorstore** from the raw Phase 2 JSON files, enabling semantic retrieval for counties that have not yet been structured into CSVs.

- Embedding model: `text-embedding-3-small` (OpenAI)
- Chunk size: 800 chars, 100-char overlap
- One Chroma collection per county, persisted to `data/vectorstore/{county}/`
- Idempotent — skips counties whose vectorstore already exists unless `--force` is passed

```bash
python -m src.vector_store                        # all 58 counties
python -m src.vector_store --counties "Fresno"    # specific county
python -m src.vector_store --force                # rebuild all
python -m src.vector_store --list                 # list built stores
```

### Program Finder (`src/knowledge_graph.py`)

A conversational LangGraph agent that answers "what maternal health programs are available near me?" from a ZIP code.

**Flow:**
1. User enters a 5-digit California ZIP code
2. ZIP resolved to county via `pgeocode` (fully offline, no API call)
3. User confirms county
4. Programs retrieved via **Path A → Path B** priority:
   - **Path A** — Structured CSV (fast, no LLM): reads `data/structured/vN/California_{County}_Healthcare_Data.csv`
   - **Path B** — RAG fallback: ChromaDB similarity search (k=10) → GPT-4o-mini extraction

```bash
# Interactive CLI
python -m src.knowledge_graph

# Programmatic (e.g. FastAPI / Streamlit)
from src.knowledge_graph import chat, initial_state
state = initial_state()
response, state = chat("94103", state)   # ZIP → confirms San Francisco
response, state = chat("yes", state)     # → lists programs
```

**Current coverage:** 58 counties vectorized; 9 counties with pre-structured CSVs (LA, SF, Sacramento, San Diego, Marin, Napa, Orange, Lake, Mono).

### Gap Analysis (`eval/gap_detector.py`)

- Reads Phase 3 output CSVs and Phase 2 raw JSON files
- TF-IDF cosine similarity compares unmatched extractions against registry
- 3 signal types: novel programs, alias misses, LLM/alias disagreement
- Output: `data/gap_analysis/gap_report.txt`

**Latest gap report summary (35 counties):**
- 577 total extractions, 423 matched to registry (73.3%)
- 40 gap candidates identified, including TAPP, LAMB, AAIMM, PEI
- 21 alias miss signals (e.g., FQHC, MEDICAID_PRENATAL)

## Configuration

Create `.env` from `.env.example`:

```bash
API_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here
DATA_COLLECTOR_NAME=Your Name
```

## Project Structure

```
├── run_pipeline.py              # Main entry point — runs all 3 phases + gap analysis
├── scraper_discovery.py         # Phase 1: Search-first discovery (DuckDuckGo + fallback)
├── scraper_extract.py           # Phase 2: Page content extraction
├── scraper_structure.py         # Phase 3: Async LLM structuring (registry-grounded)
│
├── src/
│   ├── config.py                # County URLs, API settings, budget guardrails
│   ├── federal_program_registry.py  # 31-program ground-truth registry (CA/IN/TX)
│   ├── maternal_taxonomy.py     # Keyword taxonomy (25 types, 14 categories)
│   ├── knowledge_graph.py       # LangGraph Program Finder agent (ZIP → programs)
│   ├── vector_store.py          # ChromaDB vectorstore builder + retriever factory
│   ├── phase2_enhanced.py       # Async BFS crawler with Playwright bot-bypass
│   ├── llm_program_classifier.py    # (legacy) LLM-based re-classification
│   └── utils.py                 # save_to_csv, get_next_structured_version_dir
│
├── eval/
│   ├── gap_detector.py          # TF-IDF gap analysis vs. federal registry
│   ├── run_eval.py              # Evaluation runner
│   ├── gold_maternal.jsonl      # Gold dataset (validated counties)
│   ├── gold_schema.py
│   └── metrics.py
│
├── data/
│   ├── discovery_results.json   # Phase 1 output (all 58 counties)
│   ├── raw/{county}/*.json      # Phase 2 output (889 files, 58 counties)
│   ├── structured/              # Phase 3 output (auto-versioned)
│   │   ├── v1/ … vN/            # Each run creates a new vN folder
│   │   └── vN/California_{County}_Healthcare_Data.csv
│   ├── vectorstore/{county}/    # RAG index (ChromaDB, one dir per county)
│   └── gap_analysis/
│       └── gap_report.txt       # Latest gap detection report
│
├── check_raw_data.py            # Diagnostic: county coverage + extraction quality
│
└── docs/
    ├── QUICK_START.md
    ├── ARCHITECTURE.md
    └── INSIGHTS_FATHERHOOD_MATERNAL_HEALTH.md
```

## Running the Pipeline

```bash
# Full pipeline — all 58 counties (recommended)
python run_pipeline.py

# Individual phases
python scraper_discovery.py                           # Phase 1: discovery only
python scraper_discovery.py --county "Alameda"        # specific counties
python scraper_extract.py                             # Phase 2: content extraction
python scraper_structure.py                           # Phase 3: LLM structuring

# RAG index — build vectorstores from data/raw/
python -m src.vector_store                            # all counties
python -m src.vector_store --counties "Fresno,Kern"   # subset
python -m src.vector_store --force                    # force rebuild

# Program Finder — interactive chatbot
python -m src.knowledge_graph

# Diagnostics — check data/raw coverage and extraction quality
python check_raw_data.py

# Gap analysis only (uses existing data/structured and data/raw)
python eval/gap_detector.py

# Evaluation
python eval/run_eval.py
```

## Output

| Path | Description |
|------|-------------|
| `data/discovery_results.json` | Discovered program links per county |
| `data/raw/{county}/*.json` | Raw page content (text, contacts, PDF links) — 889 files, 58 counties |
| `data/structured/vN/` | Structured CSVs — new versioned folder created every run |
| `data/vectorstore/{county}/` | Per-county ChromaDB RAG index |
| `data/gap_analysis/gap_report.txt` | Gap detection report |

## Federal Program Registry

`src/federal_program_registry.py` defines **31 known maternal health programs** used as ground truth for matching and gap detection:

| Tier | Description | Count |
|------|-------------|-------|
| Tier 1 | Universal — every county should list these (WIC, NFP, FQHC, …) | 11 |
| Tier 2 | State-wide — CA-funded, most counties receive funding | 3 |
| Tier 3 | Selective — CA-specific or evidence-based models (BIH, LAMB, PEI, …) | 17 |

Key programs: WIC, Black Infant Health (BIH), Nurse-Family Partnership (NFP), MCAH/Title V, Perinatal Care Network (PCN), Home Visiting, FQHC, Medi-Cal Prenatal, Doula programs.

## Maternal Health Focus

Per advisor feedback, the pipeline focuses exclusively on maternal health programs:

- **Included**: WIC, Black Infant Health, Nurse-Family Partnership, MCAH, Perinatal Care, Breastfeeding Support, Teen Pregnancy Programs, Doula Programs, Fatherhood & Partner Engagement Programs
- **Excluded**: Medi-Cal (general), CalFresh, Behavioral Health, Senior Services, and other non-maternal programs

### Program Taxonomy

The taxonomy in `src/maternal_taxonomy.py` defines **25 program types** across **14 categories**, aligned with the SDOH framework and White House Blueprint:

| Blueprint Goal | SDOH Domain | Categories |
|----------------|-------------|------------|
| Goal 1: Access | Healthcare Access | Perinatal Care, Behavioral Health, Reproductive Health |
| Goal 2: Quality | Quality of Care | Health Equity, Quality Improvement |
| Goal 4: Workforce | Social Support | Home Visiting, Birth Support, Community Health, Breastfeeding |
| Goal 5: Social | Nutrition, Social Support | Nutrition, Adolescent Health, Early Childhood, Partner & Family Engagement |

## Documentation

- [Quick Start Guide](docs/QUICK_START.md)
- [Architecture Overview](docs/ARCHITECTURE.md)
- [Evaluation Guide](eval/README.md)
- [Fatherhood & Maternal Health Insights](docs/INSIGHTS_FATHERHOOD_MATERNAL_HEALTH.md)
