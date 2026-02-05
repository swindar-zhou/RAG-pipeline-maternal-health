# Evaluation Framework

This directory contains the evaluation framework for the maternal health data extraction pipeline.

## Overview

Per advisor feedback, this project focuses specifically on **maternal health programs** rather than general health services. The evaluation framework is designed to:

1. **Track A**: Detect presence/absence of maternal health programs at county level
2. **Track B**: Evaluate detailed extraction of how counties offer maternal programs

## Files

| File | Description |
|------|-------------|
| `gold_maternal.jsonl` | Gold dataset focused on maternal health programs (4 validated counties) |
| `gold.jsonl` | Legacy gold dataset with general health programs (15 counties) |
| `gold_schema.py` | Pydantic schemas for gold dataset validation |
| `metrics.py` | Metric calculation functions |
| `run_eval.py` | Main evaluation script |
| `gold.jsonl.example` | Example gold dataset entry format |

## Gold Datasets

### Maternal Health Gold Dataset (`gold_maternal.jsonl`)

Created based on advisor's manual review and validated URLs. Contains **4 counties** with verified maternal health entry points:

| County | Maternal Health URL | Programs |
|--------|---------------------|----------|
| San Diego | `sandiegocounty.gov/.../maternal_child_family_health_services.html` | WIC, Black Infant Health, Nurse-Family Partnership |
| Los Angeles | `publichealth.lacounty.gov/mch/` | WIC, Black Infant Health, Nurse-Family Partnership |
| Sacramento | `dhs.saccounty.gov/.../MCAH-Program.aspx` | MCAH, WIC |
| San Francisco | `sf.gov/.../maternal-child-and-adolescent-health` | MCAH, WIC |

### Maternal Health Program Categories

Based on state-level reference pages (California CDPH, Florida DOH):

- **Nutrition**: WIC (Women, Infants, and Children)
- **Home Visiting**: Nurse-Family Partnership, MIECHV, Parents as Teachers, Black Infant Health
- **Perinatal Care**: Prenatal Care, Postpartum Support, CPSP
- **Health Equity**: Black Infant Health, Healthy Start, Perinatal Equity Initiative
- **Breastfeeding**: Lactation Support Programs
- **Adolescent Health**: Teen Pregnancy Programs, AFLP
- **Family Planning**: Reproductive Health Services
- **Birth Support**: Doula Programs, Midwifery Services
- **Early Childhood**: First 5 Programs

## Gold Dataset Format (Maternal Health)

Create entries in `gold_maternal.jsonl` with one JSON object per county:

```json
{
  "county_name": "San Diego",
  "county_url": "https://www.sandiegocounty.gov/",
  "maternal_health_url": "https://www.sandiegocounty.gov/.../maternal_child_family_health_services.html",
  "has_maternal_programs": true,
  "programs": [
    {
      "program_name": "WIC (Women, Infants, and Children)",
      "program_url": "https://...",
      "category": "WIC",
      "description": "Nutrition program for pregnant and breastfeeding women...",
      "target_population": "Pregnant women, breastfeeding mothers, infants...",
      "eligibility_requirements": "Income-based eligibility...",
      "services_provided": ["nutrition education", "breastfeeding support", "food vouchers"],
      "contact_phone": null,
      "contact_email": null
    }
  ]
}
```

## Running Evaluation

```bash
# Activate virtual environment
source .venv/bin/activate

# After running the pipeline (phases 1-3)
python eval/run_eval.py
```

This will:
1. Load gold dataset from `eval/gold_maternal.jsonl`
2. Load pipeline outputs from `data/structured/`
3. Calculate metrics for each county
4. Output aggregate metrics table
5. Save results to `eval/results/`

## Metrics

### Phase 1: Discovery

| Metric | Description |
|--------|-------------|
| **Recall@10** | % of gold maternal programs found in top 10 discovered links |
| **Recall@20** | % of gold maternal programs found in top 20 discovered links |
| **Maternal Program Detection** | Binary: Did we find the maternal health section? |
| **Pages Crawled** | Number of pages fetched per county (efficiency) |

### Phase 2: Extraction

| Metric | Description |
|--------|-------------|
| **Contact Precision** | Precision of phone/email extraction |
| **Contact Recall** | Recall of phone/email extraction |
| **Services Extraction** | % of services_provided fields populated |

### Phase 3: Structuring

| Metric | Description |
|--------|-------------|
| **Schema Validity Rate** | % of programs that pass Pydantic validation |
| **Critical Field Missing Rate** | % missing eligibility/services/contact |
| **Category Accuracy** | % of programs correctly categorized |
| **Maternal Health Precision** | % of extracted programs that are actually maternal health |

## Current Pipeline Results (Feb 2026)

### Discovery Results

| County | Programs Discovered | Categories Found |
|--------|--------------------:|------------------|
| San Diego | 3 | Perinatal Care, Health Equity |
| Los Angeles | 11 | Breastfeeding, Perinatal Care, Birth Support, Health Equity |
| Sacramento | 5 | Breastfeeding, Maternal Child Health, Perinatal Care |
| San Francisco | 8 | WIC, Home Visiting, Health Equity, Family Planning, Adolescent Health |
| **Total** | **27** | |

### Structured Programs

| County | Programs Extracted |
|--------|-------------------:|
| San Diego | 9 |
| Los Angeles | 20 |
| Sacramento | 5 |
| San Francisco | 12 |
| **Total** | **46** |

## Reference Sources

### State-Level Training Data

Per advisor recommendation, these state pages serve as reference for what constitutes a maternal health program:

- **California**: https://www.cdph.ca.gov/Programs/CFH/DMCAH/Pages/Domains/Maternal-Health.aspx
- **Florida (Pregnancy)**: https://www.floridahealth.gov/individual-family-health/womens-health/pregnancy/
- **Florida (WIC)**: https://www.floridahealth.gov/individual-family-health/womens-health/wic/

### Background Reading

- [NCBI: Maternal Health Research](https://www.ncbi.nlm.nih.gov/search/research-news/17328/)
- [CNN: Maternity Care Deserts Report](https://www.cnn.com/2022/10/11/health/maternity-care-deserts-march-of-dimes-report/index.html)
- Grimmer, Roberts & Stewart (2022). *Text as Data: A New Framework for Machine Learning and the Social Sciences*. Princeton University Press.

## Adding New Counties

1. **Manual Validation**: Find the maternal health section URL on the county website
2. **Add to Config**: Update `src/config.py` with the validated URL:
   ```python
   MATERNAL_HEALTH_URLS = {
       "County Name": "https://validated-maternal-health-url...",
       ...
   }
   ```
3. **Add Gold Entry**: Add a new line to `eval/gold_maternal.jsonl` with expected programs
4. **Run Pipeline**: Execute phases 1-3 for the new county
5. **Evaluate**: Run `python eval/run_eval.py` to measure performance

## Program Taxonomy

The `src/maternal_taxonomy.py` file contains a comprehensive taxonomy of maternal health programs with:

- **19 program types** across **10 categories**
- **118 keywords** for classification
- **7 federal programs** (WIC, NFP, MIECHV, etc.)
- Helper functions for classification and scoring

See `python src/maternal_taxonomy.py` for a full taxonomy summary.
