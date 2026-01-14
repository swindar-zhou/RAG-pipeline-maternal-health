# Evaluation Framework

This directory contains the evaluation framework for the 3-phase pipeline.

## Files

- `gold_schema.py` - Pydantic schemas for gold dataset
- `metrics.py` - Metric calculation functions
- `run_eval.py` - Main evaluation script
- `gold.jsonl.example` - Example gold dataset entry

## Gold Dataset Format

Create `gold.jsonl` with one JSON object per county (one line per county):

```json
{
  "county_name": "San Diego",
  "county_url": "https://www.sandiegocounty.gov/",
  "programs": [
    {
      "program_name": "Medi-Cal",
      "program_url": "https://www.sandiegocounty.gov/content/sdc/hhsa/programs/ssp/medi-cal_program.html",
      "category": "Primary Care",
      "description": "California's Medicaid program",
      "eligibility_requirements": "Low-income individuals",
      "application_process": "Apply online or call",
      "contact_phone": "866-262-9881",
      "contact_email": null,
      "pdf_links": ["https://..."]
    }
  ]
}
```

## Running Evaluation

```bash
# After running the pipeline (phases 1-3)
python eval/run_eval.py
```

This will:
1. Load gold dataset from `eval/gold.jsonl`
2. Load pipeline outputs from `data/`
3. Calculate metrics for each county
4. Output aggregate metrics table
5. Save results to `eval/results/metrics_{run_id}.json` and `.csv`

## Metrics

### Phase 1 (Discovery)
- **Recall@10**: % of gold programs found in top 10 links
- **Recall@20**: % of gold programs found in top 20 links
- **Pages crawled**: Number of pages crawled per county

### Phase 2 (Extraction)
- **Contact Precision**: Precision of phone/email extraction
- **Contact Recall**: Recall of phone/email extraction
- **PDF Precision**: Precision of PDF detection
- **PDF Recall**: Recall of PDF detection

### Phase 3 (Structuring)
- **Schema Validity Rate**: % of programs that pass Pydantic validation
- **Critical Field Missing Rate**: % of programs missing eligibility/apply/contact
- **Field Exact Match Rate**: % of fields that exactly match gold labels

## Creating Gold Dataset

Start with 10-20 counties, 3-5 programs each. Label:
- Official program URLs
- Program names
- Eligibility requirements
- Application process
- Contact information
- Expected PDF links

See `gold.jsonl.example` for format.

