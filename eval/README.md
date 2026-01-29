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

## Gold Dataset

A gold dataset has been created with **15 counties** and **45 programs** total:

### Counties Included
1. **San Diego** (5 programs) - Complete with real data from pipeline
2. **Los Angeles** (2 programs) - Real data from pipeline
3. **Orange** (3 programs)
4. **Riverside** (3 programs)
5. **San Bernardino** (3 programs)
6. **Santa Clara** (3 programs)
7. **Sacramento** (3 programs)
8. **Fresno** (3 programs)
9. **Kern** (2 programs)
10. **Alameda** (3 programs)
11. **Contra Costa** (3 programs)
12. **San Francisco** (3 programs)
13. **San Mateo** (3 programs)
14. **Ventura** (3 programs)
15. **Santa Barbara** (3 programs)

### Common Programs Labeled
- **Medi-Cal** - Health coverage program (all counties)
- **CalFresh** - Food assistance (most counties)
- **Behavioral Health Services** - Mental health services (many counties)
- **Public Health Services** - Public health programs (many counties)
- **In-Home Supportive Services** - Home care (San Diego)
- **WIC** - Women, Infants, Children nutrition (some counties)

### Creating Additional Gold Entries

To add more counties or programs, add JSON lines to `gold.jsonl`:

```json
{"county_name": "County Name", "county_url": "https://...", "programs": [...]}
```

Each program should include:
- Official program URLs
- Program names
- Eligibility requirements
- Application process
- Contact information
- Expected PDF links

See `gold.jsonl.example` for format.

