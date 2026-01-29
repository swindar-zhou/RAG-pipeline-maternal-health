# County Healthcare Data Scraper

**iTREDS Project** - Extract healthcare program data from California county websites using LLMs.

> **Note**: This codebase has been restructured for better organization, type safety, and evaluation capabilities. See [ARCHITECTURE.md](ARCHITECTURE.md) for details.

## Quick Start (3-phase pipeline)

> **⚠️ Important**: If you get `ModuleNotFoundError` (e.g., `No module named 'requests'`), install dependencies first:
> ```bash
> # Option 1: Use setup script (recommended)
> ./setup.sh
> 
> # Option 2: Manual installation
> pip install -r requirements.txt
> 
> # Option 3: Use virtual environment (if permission errors)
> python3 -m venv .venv
> source .venv/bin/activate
> pip install -r requirements.txt
> ```
> See [SETUP.md](SETUP.md) or [QUICK_START.md](QUICK_START.md) for detailed setup instructions.

```bash
# 1) Install dependencies (if not already installed)
pip install -r requirements.txt

# 2) Configure your provider
cp .env.example .env
# Edit .env and set API provider and keys as needed
#   API_PROVIDER=openai        # or "anthropic" or "ollama"
# If OpenAI/Anthropic: add your API key
# If Ollama (local): install from https://ollama.com and pull a model:
#   ollama pull llama3.1:8b-instruct

# 3) Test the setup
python test_setup.py

# 4) Run the pilot pipeline (5 counties)
# Phase 1 - Discovery (collect candidate program links)
python scraper_discovery.py

# Phase 2 - Deep Extraction (fetch program pages, contacts, PDFs)
python scraper_extract.py

# Phase 3 - LLM Structuring (OpenAI gpt-4o-mini by default)
# Produces California_County_Healthcare_Data.csv
python scraper_structure.py
```

## How it works (explained with visuals)

This project runs in three simple phases. You don’t need prior context—think of it like a web “treasure hunt”:

```
PHASE 1: DISCOVERY            PHASE 2: DEEP EXTRACTION         PHASE 3: STRUCTURING
┌─────────────────────┐       ┌────────────────────────┐       ┌─────────────────────────┐
│ Start at County URL │  ──▶  │ Open each Program Page │  ──▶  │ Turn Text → Spreadsheet │
│  → Find Health Dept │       │  → Read the full text  │       │  → 1 row per program    │
│  → Find Maternal/MCH│       │  → Grab phones/emails  │       │  → CSV output           │
│  → Collect program  │       │  → Save page as JSON   │       │                         │
│    links (WIC, BIH) │       │    (raw content)       │       │                         │
└─────────────────────┘       └────────────────────────┘       └─────────────────────────┘
```

### Phase 1 — Discovery (what pages should we read?)
- Goal: Find the right pages on each county’s website that likely describe maternal health programs.
- Navigation recipe:
  - County homepage → Health Department → Maternal/Child Health section → Program pages (e.g., WIC, Healthy Start, BIH, Home Visiting).
  - We score links using keywords (department, section, and program levels).
- Output:
  - `data/discovery_results.json` with, per county:
    - `health_dept_url`, `maternal_section_url`
    - `programs[]` = list of candidate program links and how we got there.
- Why it matters: County sites are organized differently; a small, smart crawl gets you to the right pages quickly without breaking sites or budgets.

Mini visual
```
County Home
   │
   ├─▶ Health Department (Public Health / HHSA)
   │      │
   │      └─▶ Maternal/Child Health (MCH/MCAH/Women’s/Family)
   │              │
   │              └─▶ Program Pages (WIC, BIH, Home Visiting, NFP, etc.)
   │
   └─▶ (Ignore social/external links)
```

### Phase 2 — Deep Content Extraction (what’s on those pages?)
- Goal: For every program page found in Phase 1, fetch the content and capture helpful signals.
- What we do on each page:
  - Read HTML and strip layout (nav/header/footer).
  - Extract clean text (truncated to keep things fast).
  - Pull contact info via regex (phone numbers, emails).
  - Collect document links, especially “Eligibility”, “Apply”, “Application”, and “Brochure” PDFs.
- Output per page:
  - `data/raw/{county}/{program-slug}-{hash}.json` containing:
    - `page_url`, `link_text`, `nav_path`
    - `text` (main content), `contacts { phones[], emails[] }`
    - `pdf_links[]`

Mini visual
```
Program Page HTML
   │
   ├─▶ Strip layout → get main text
   ├─▶ Regex phones/emails
   └─▶ Collect likely PDFs (eligibility/apply/brochure)
        ↳ Save as raw JSON per page
```

### Phase 3 — LLM Structuring (turn the text into a consistent table)
- Goal: Convert unstructured text from Phase 2 into a clean, consistent dataset.
- How it works:
  - For each raw page JSON, we send up to ~10k characters to OpenAI `gpt-4o-mini`.
  - The model returns a small JSON object (program name, category, eligibility, application process, contact, link).
  - We aggregate all programs per county and write one CSV.
- Budget guardrails:
  - Input text truncated to 10k characters.
  - `max_tokens=1500`, `temperature=0.1`.
  - Short delay between calls.
- Output:
  - `California_County_Healthcare_Data.csv` (one row per program).

Mini visual
```
Raw Page JSON (text + contacts + PDFs)
   │
   └─▶ LLM (JSON-only prompt)
         │
         └─▶ Structured Program Object(s)
               │
               └─▶ Aggregated by County → CSV
```

Tip for visual learners
- There’s an interactive visualization of this workflow in `workflow-visuals.jsx` that you can drop into any React app to demo the process with panels and timelines.

## Configuration

Edit `.env` file:

```bash
API_PROVIDER=openai              # or "anthropic" or "ollama"
OPENAI_API_KEY=openai-key        # Your OpenAI key
ANTHROPIC_API_KEY=sk-ant-key     # Your Anthropic key (if used)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b-instruct
DATA_COLLECTOR_NAME=Swindar    # For attribution
```

### Using Ollama (free, local model)
- Install Ollama on macOS: see `https://ollama.com`
- Pull a small instruction-tuned model (recommended for structure extraction):
  - `ollama pull llama3.1:8b-instruct` (default in `.env`)
  - Alternatives: `qwen2.5:7b-instruct`, `mistral:7b-instruct`
- In `.env`, set `API_PROVIDER=ollama`
- Run `python test_setup.py` to confirm Ollama connectivity
- Run `python scraper.py`

## Output

Phase outputs:
- Phase 1: `data/discovery_results.json`
- Phase 2: `data/raw/{county}/*.json` (one per program page)
- Phase 3: Per‑county CSVs in `data/structured/`:
  - `data/structured/California_<County>_Healthcare_Data.csv`
  - Plus a combined file `California_County_Healthcare_Data.csv` for convenience

## Running the Pipeline

### Full Pipeline (Recommended)
```bash
# Run all 3 phases for 10 counties
python run_pipeline.py
```

The `run_pipeline.py` script targets 10 counties by default:
- Alameda, Fresno, Sacramento, Kern, Los Angeles, San Francisco, Orange, Riverside, Santa Clara, Contra Costa

### Individual Phases
```bash
# Phase 1 only: Discovery
python scraper_discovery.py

# Phase 2 only: Deep extraction (requires Phase 1 output)
python scraper_extract.py

# Phase 3 only: LLM structuring (requires Phase 2 output)
python scraper_structure.py
```

### Legacy All-in-One
```bash
# Old single-script approach (still supported)
python scraper.py
```

### Custom Counties
Edit the county list in `scraper_discovery.py` or `run_pipeline.py`:
```python
TARGET_COUNTIES = ["San Diego", "Los Angeles"]  # Your selection
```

### Check Data Status
```bash
# See which counties have data and which are missing
python collect_missing_counties.py
```

### Improve Discovery for Failed Counties
If some counties have empty programs arrays, use agentic discovery:
```bash
python improve_discovery.py
```

## Project Structure

### Entry Points (Scripts)
- `scraper_discovery.py` - Phase 1: Discovery (collect program links for counties)
- `scraper_extract.py` - Phase 2: Deep extraction (raw page JSON with contacts/PDFs)
- `scraper_structure.py` - Phase 3: LLM structuring → CSV (budget‑guarded)
- `run_pipeline.py` - Orchestrates all 3 phases for 10 preselected counties
- `scraper.py` - Legacy all-in-one scraper (OpenAI/Anthropic/Ollama)
- `test_setup.py` - Connectivity checks for API providers

### Core Modules (`src/`)
- `src/config.py` - Shared constants (county mappings, settings, keywords)
- `src/utils.py` - Shared utilities (CSV writer, common helpers)

### Type Safety (`schemas/`)
- `schemas/discovery.py` - Phase 1 Pydantic schemas
- `schemas/extraction.py` - Phase 2 Pydantic schemas
- `schemas/structured.py` - Phase 3 Pydantic schemas

### Agentic System (`agents/`)
- `agents/discovery_agent.py` - Agentic Phase 1 with tools and state management

### Evaluation Framework (`eval/`)
- `eval/gold_schema.py` - Gold dataset Pydantic schemas
- `eval/metrics.py` - Metric calculation functions (Recall@K, precision/recall, etc.)
- `eval/run_eval.py` - Main evaluation script
- `eval/README.md` - Evaluation framework documentation

### Configuration & Documentation
- `.env.example` - Template for environment configuration
- `.env` - Your local configuration (gitignored, create from `.env.example`)
- `requirements.txt` - Python dependencies
- `SETUP.md` - Detailed setup instructions
- `QUICK_START.md` - Quick guide for collecting more county data
- `setup.sh` - Automated setup script
- `README.md` - This file (main documentation)
- `EVALUATION_GUIDE.md` - Evaluation framework quick start guide
- `workflow-demo/` - Workflow visualization assets

## Folder Structure

```
iTREDS-gov-database-project-1/
├── src/                              # Core shared modules
│   ├── __init__.py                  # Package exports
│   ├── config.py                    # Constants, county mappings, settings
│   └── utils.py                     # Shared utilities (CSV writer, etc.)
├── schemas/                          # Pydantic schemas for type-safe data structures
│   ├── __init__.py
│   ├── discovery.py                 # Phase 1 schemas
│   ├── extraction.py                # Phase 2 schemas
│   └── structured.py                # Phase 3 schemas
├── agents/                           # Agentic system components
│   ├── __init__.py
│   └── discovery_agent.py           # Agentic Phase 1 with tools and state management
├── eval/                             # Evaluation framework
│   ├── gold_schema.py               # Gold dataset schemas
│   ├── metrics.py                   # Metric calculation functions
│   ├── run_eval.py                  # Main evaluation script
│   ├── gold.jsonl.example           # Example gold dataset
│   ├── gold.jsonl                   # Gold dataset (15 counties, 45 programs)
│   ├── README.md                    # Evaluation documentation
│   └── results/                     # Evaluation results (CSV/JSON)
├── tests/                            # Integration tests
│   ├── conftest.py                  # Shared fixtures
│   ├── test_phase1_discovery.py     # Phase 1 tests
│   ├── test_phase2_extraction.py    # Phase 2 tests
│   ├── test_phase3_structuring.py   # Phase 3 tests
│   ├── test_pipeline_integration.py # End-to-end tests
│   ├── test_schemas.py              # Schema validation tests
│   └── README.md                    # Test documentation
├── data/                             # Pipeline outputs
│   ├── discovery_results.json        # Phase 1 output: discovered program links per county
│   ├── raw/                          # Phase 2 output: raw page content per county
│   │   ├── {county-slug}/
│   │   │   └── program-{hash}.json   # One JSON file per program page
│   │   ├── los-angeles/              # Example: Los Angeles county raw data
│   │   └── san-diego/                # Example: San Diego county raw data
│   ├── structured/                   # Phase 3 output: structured CSV files
│   │   ├── California_{County}_Healthcare_Data.csv  # Per-county CSVs
│   │   ├── California_Los_Angeles_Healthcare_Data.csv
│   │   └── California_County_Healthcare_Data_San_Diego.csv
│   ├── reports/                      # Quality reports (future)
│   └── Raw_Data.csv                  # Legacy combined raw data (if generated)
├── workflow-demo/                    # Workflow visualization assets
│   ├── workflow-ref.md              # Workflow documentation
│   └── workflow-visuals.jsx         # React component for workflow visualization
├── scraper_discovery.py              # Phase 1: Discovery script (entry point)
├── scraper_extract.py                # Phase 2: Deep extraction script (entry point)
├── scraper_structure.py              # Phase 3: LLM structuring script (entry point)
├── scraper.py                        # Legacy all-in-one scraper
├── run_pipeline.py                   # Batch runner for 10 counties (orchestrates all 3 phases)
├── test_setup.py                     # Connectivity checks for API providers
├── requirements.txt                  # Python dependencies
├── .env.example                      # Environment configuration template
├── .env                              # Your local config (gitignored, create from .env.example)
├── .gitignore                        # Git ignore rules
├── README.md                         # This file
├── EVALUATION_GUIDE.md              # Evaluation framework guide
└── California_County_Healthcare_Data.csv  # Phase 3 combined CSV output (optional)
```

## Evaluation Framework

The project includes a rigorous evaluation framework with gold dataset and metrics tracking.

### Quick Start

1. **Gold dataset ready**: A gold dataset with 15 counties and 45 programs is available in `eval/gold.jsonl`
   - Includes San Diego, Los Angeles, Orange, Riverside, and 11 other major counties
   - Each county has 2-5 labeled programs (Medi-Cal, CalFresh, Behavioral Health, etc.)

2. **Run evaluation**:
   ```bash
   python eval/run_eval.py
   ```
   
   This will calculate metrics for all counties in the gold dataset.

3. **View results**: Metrics saved to `eval/results/metrics_{run_id}.csv` and `.json`

### Metrics Tracked

**Phase 1 (Discovery)**
- Recall@10, Recall@20: % of gold programs found in top K links
- Pages crawled per county

**Phase 2 (Extraction)**
- Contact precision/recall: Phone/email extraction accuracy
- PDF precision/recall: Application/eligibility PDF detection

**Phase 3 (Structuring)**
- Schema validity rate: % passing Pydantic validation
- Critical field missing rate: % missing eligibility/apply/contact
- Field exact match rate: % matching gold labels

See `eval/README.md` for detailed documentation.

## Agentic System

Phase 1 discovery can use an agentic system with tools and state management:

```python
from agents.discovery_agent import DiscoveryAgent

agent = DiscoveryAgent()
result = agent.run("San Diego", "https://www.sandiegocounty.gov/")
```

The agent implements a state machine with tools:
- **Search Tool**: Find health department links
- **Scoring Tool**: Score links by relevance
- **Classification Tool**: Classify pages as program pages
- **Verification Tool**: Verify pages have required signals

See `agents/discovery_agent.py` for implementation.

## Testing

The project includes comprehensive integration tests:

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_phase1_discovery.py

# Run with coverage
pytest tests/ --cov=. --cov-report=html
```

**Test Coverage:**
- Phase 1 (Discovery) - Schema validation, health dept finding, program collection
- Phase 2 (Extraction) - Contact extraction, PDF detection, page processing
- Phase 3 (Structuring) - LLM extraction (mocked), schema validation
- Full pipeline integration - End-to-end workflow tests
- Schema validation - Pydantic schema tests

See `tests/README.md` for detailed test documentation.

## Code Organization

The codebase is organized into clear modules:

- **`src/`** - Core shared modules (config, utilities) used by all scripts
- **`schemas/`** - Pydantic schemas for type-safe data validation
- **`agents/`** - Agentic system components with tools and state management
- **`eval/`** - Evaluation framework with metrics and gold dataset support
- **`tests/`** - Integration tests for all pipeline phases
- **Root scripts** - Entry points for each phase (import from `src/` and `schemas/`)

This structure:
- Eliminates code duplication (constants, utilities in `src/`)
- Provides type safety (Pydantic schemas)
- Enables evaluation (metrics tracking)
- Supports agentic workflows (tools + state management)
- Ensures reliability (comprehensive test suite)

## Budget Guardrails (OpenAI)
- `scraper_structure.py` truncates input text to 10k chars and caps `max_tokens` to 1500.
- Keep subpage recursion off for the pilot.
- Optional: set a monthly cap (e.g., $5) in OpenAI billing.
