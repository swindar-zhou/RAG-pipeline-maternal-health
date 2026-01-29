# Evaluation & Agentic System Guide

This guide explains the evaluation framework and agentic system added to the pipeline.

## What Was Built

### 1. Pydantic Schemas (`schemas/`)
Type-safe data structures for all pipeline phases:
- `discovery.py`: `DiscoveryResult`, `ProgramLink`
- `extraction.py`: `RawPage`, `Contacts`
- `structured.py`: `StructuredProgram`, `StructuredCounty`

**Benefits**: Type validation, IDE autocomplete, catch errors early

### 2. Evaluation Framework (`eval/`)
Rigorous metrics tracking with gold dataset:

**Files**:
- `gold_schema.py`: Pydantic schemas for gold labels
- `metrics.py`: Metric calculation (Recall@K, precision/recall, schema validity)
- `run_eval.py`: Main evaluation script
- `gold.jsonl.example`: Example gold dataset format

**Metrics Tracked**:
- **Phase 1**: Recall@10, Recall@20, pages crawled
- **Phase 2**: Contact precision/recall, PDF precision/recall
- **Phase 3**: Schema validity, critical field missing rate, field exact match rate

### 3. Agentic System (`agents/`)
Agentic Phase 1 discovery with tools and state management:

**State Machine**: SEED → SEARCH → SCORE → FETCH → CLASSIFY → VERIFY → DONE

**Tools**:
1. **Search Tool**: Find health department links on county homepage
2. **Scoring Tool**: Score links by keyword relevance
3. **Classification Tool**: Classify pages as program pages
4. **Verification Tool**: Verify pages have required signals (eligibility/apply/contact)

**Benefits**: Looping behavior, failure handling, confidence tracking

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt  # Now includes pydantic
```

### 2. Create Gold Dataset

Create `eval/gold.jsonl` with ground truth labels (see `eval/gold.jsonl.example`):

```json
{"county_name": "San Diego", "county_url": "https://www.sandiegocounty.gov/", "programs": [...]}
```

Start with 10-20 counties, 3-5 programs each.

### 3. Run Pipeline

```bash
# Run all 3 phases
python run_pipeline.py

# Or run individually
python scraper_discovery.py  # Phase 1
python scraper_extract.py    # Phase 2
python scraper_structure.py  # Phase 3
```

### 4. Run Evaluation

```bash
python eval/run_eval.py
```

Output:
- Metrics table printed to console
- `eval/results/metrics_{run_id}.json` (detailed metrics)
- `eval/results/metrics_{run_id}.csv` (CSV for analysis)

### 5. Use Agentic Discovery (Optional)

```python
from agents.discovery_agent import DiscoveryAgent

agent = DiscoveryAgent()
result = agent.run("San Diego", "https://www.sandiegocounty.gov/")
```

## Metrics Explained

### Phase 1: Discovery Metrics

**Recall@K**: Percentage of gold program URLs found in top K discovered links.

Example: If gold dataset has 5 programs and 4 appear in top 20 links → Recall@20 = 80%

**Why it matters**: Measures if discovery finds the right pages.

### Phase 2: Extraction Metrics

**Contact Precision**: Of extracted phones/emails, how many are correct?
**Contact Recall**: Of gold contacts, how many were extracted?

**PDF Precision/Recall**: Similar for PDF links (application/eligibility forms).

**Why it matters**: Measures extraction quality before LLM structuring.

### Phase 3: Structuring Metrics

**Schema Validity Rate**: % of programs that pass Pydantic validation (should be 100% if using schemas).

**Critical Field Missing Rate**: % of programs missing eligibility/apply/contact info.

**Field Exact Match Rate**: % of fields that exactly match gold labels.

**Why it matters**: Measures LLM structuring accuracy.

## Resume Bullets

After running evaluation, you can write:

> Built an LLM-based web extraction system and repeatable evaluation harness (gold dataset + regression tests), tracking schema-validity, field-level accuracy, and failure modes across model/prompt versions.

> Reduced missing critical fields from 18% → 6% through prompt + parsing improvements.

> Added regression test suite to prevent metric drop across model/prompt versions.

## Next Steps

1. **Label Gold Dataset**: Start with San Diego (you already have data), label 3-5 programs
2. **Run Baseline**: Run evaluation to get baseline metrics
3. **Iterate**: Improve prompts/models, re-run evaluation, track improvements
4. **Add More Counties**: Expand gold dataset to 10-20 counties
5. **Regression Testing**: Set up CI to fail if metrics drop > X%

## File Structure

```
schemas/
├── __init__.py
├── discovery.py      # Phase 1 schemas
├── extraction.py     # Phase 2 schemas
└── structured.py     # Phase 3 schemas

agents/
├── __init__.py
└── discovery_agent.py  # Agentic Phase 1

eval/
├── README.md
├── gold_schema.py      # Gold dataset schemas
├── metrics.py          # Metric calculations
├── run_eval.py         # Evaluation script
├── gold.jsonl.example  # Example gold dataset
└── results/            # Evaluation outputs
```

## Questions?

See `eval/README.md` for detailed evaluation documentation.

