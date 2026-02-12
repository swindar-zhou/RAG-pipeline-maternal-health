# Maternal Health Data Extraction Pipeline

**iTREDS Project** - Extract maternal health program data from California county websites using LLMs.

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

**Initial focus**: California (58 counties), with validated data from 4 major counties (San Diego, Los Angeles, Sacramento, San Francisco)

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

This pipeline discovers and extracts **maternal health programs** (WIC, Black Infant Health, Nurse-Family Partnership, etc.) from county government websites. It uses a 3-phase approach: Discovery → Extraction → Structuring.

## Quick Start

```bash
# 1. Setup
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Configure API key
cp .env.example .env
# Edit .env and add your OpenAI API key

# 3. Run the pipeline
python run_pipeline.py
```

## How It Works

```
PHASE 1: DISCOVERY          PHASE 2: EXTRACTION           PHASE 3: STRUCTURING
┌──────────────────┐        ┌────────────────────┐        ┌─────────────────────┐
│ Find Maternal    │   ──▶  │ Fetch Program      │   ──▶  │ LLM → Structured    │
│ Health Pages     │        │ Page Content       │        │ CSV Output          │
│ (WIC, BIH, NFP)  │        │ (text, contacts)   │        │                     │
└──────────────────┘        └────────────────────┘        └─────────────────────┘
```

### Phase 1 - Discovery
- Navigates: County → Health Dept → Maternal/Child Health → Programs
- Uses keyword scoring and taxonomy-based classification
- Filters to maternal health programs only (per advisor feedback)

### Phase 2 - Extraction  
- Fetches each discovered program page
- Extracts: text content, phone/email contacts, PDF links

### Phase 3 - Structuring
- Sends content to LLM (GPT-4o-mini)
- Returns structured JSON with program details
- Outputs CSV files per county

## Configuration

Create `.env` from `.env.example`:

```bash
API_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here
DATA_COLLECTOR_NAME=Your Name
```

## Project Structure

```
├── run_pipeline.py           # Main entry point (runs all 3 phases)
├── scraper_discovery.py      # Phase 1: Discovery
├── scraper_extract.py        # Phase 2: Extraction
├── scraper_structure.py      # Phase 3: LLM Structuring
│
├── src/                      # Core modules
│   ├── config.py             # County URLs, keywords, settings
│   ├── maternal_taxonomy.py  # Maternal health program taxonomy
│   └── utils.py              # Shared utilities
│
├── schemas/                  # Pydantic data schemas
│   ├── discovery.py
│   ├── extraction.py
│   └── structured.py
│
├── agents/                   # Agentic discovery system
│   └── discovery_agent.py
│
├── eval/                     # Evaluation framework
│   ├── gold_maternal.jsonl   # Gold dataset (4 validated counties)
│   ├── metrics.py            # Metric calculations
│   └── run_eval.py           # Evaluation script
│
├── tests/                    # Integration tests
├── data/                     # Pipeline outputs
│   ├── discovery_results.json
│   ├── raw/                  # Phase 2 JSON files
│   └── structured/           # Phase 3 CSV files
│
└── docs/                     # Documentation
    ├── QUICK_START.md
    ├── ARCHITECTURE.md
    └── ...
```

## Running the Pipeline

```bash
# Full pipeline (recommended)
python run_pipeline.py

# Individual phases
python scraper_discovery.py   # Phase 1
python scraper_extract.py     # Phase 2  
python scraper_structure.py   # Phase 3

# Run tests
pytest tests/

# Run evaluation
python eval/run_eval.py
```

## Output

- `data/discovery_results.json` - Discovered program links
- `data/raw/{county}/*.json` - Raw page content
- `data/structured/California_{County}_Healthcare_Data.csv` - Final structured data

## Validated Counties

These counties have manually validated maternal health URLs (from advisor):

| County | Programs Found |
|--------|:--------------:|
| San Diego | 9 |
| Los Angeles | 20 |
| Sacramento | 5 |
| San Francisco | 12 |

## Maternal Health Focus

Per advisor feedback, the pipeline focuses exclusively on maternal health programs:

- **Included**: WIC, Black Infant Health, Nurse-Family Partnership, MCAH, Perinatal Care, Breastfeeding Support, Teen Pregnancy Programs, Doula Programs, Fatherhood & Partner Engagement Programs
- **Excluded**: Medi-Cal, CalFresh, Behavioral Health, Senior Services, and other general health programs

### Program Taxonomy

The taxonomy in `src/maternal_taxonomy.py` defines **25 program types** across **14 categories**, aligned with the SDOH framework and White House Blueprint:

| Blueprint Goal | SDOH Domain | Categories |
|----------------|-------------|------------|
| Goal 1: Access | Healthcare Access | Perinatal Care, Behavioral Health, Reproductive Health |
| Goal 2: Quality | Quality of Care | Health Equity, Quality Improvement |
| Goal 4: Workforce | Social Support | Home Visiting, Birth Support, Community Health, Breastfeeding |
| Goal 5: Social | Nutrition, Social Support | Nutrition, Adolescent Health, Early Childhood, Partner & Family Engagement |

See `python src/maternal_taxonomy.py` for a full taxonomy summary.
See [docs/INSIGHTS_FATHERHOOD_MATERNAL_HEALTH.md](docs/INSIGHTS_FATHERHOOD_MATERNAL_HEALTH.md) for research insights on how fatherhood programs impact maternal health.

## Documentation

- [Quick Start Guide](docs/QUICK_START.md)
- [Architecture Overview](docs/ARCHITECTURE.md)
- [Evaluation Guide](eval/README.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
