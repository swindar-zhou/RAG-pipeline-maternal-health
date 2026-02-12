# Evaluation Framework

This directory contains the evaluation framework for the maternal health data extraction pipeline.

## Theoretical Framework

The program taxonomy and evaluation criteria are grounded in two complementary frameworks:

### 1. Social Determinants of Health (SDOH)

Based on Solar & Irwin (2010) WHO Conceptual Framework and related literature:

> "The conditions in which people are born, grow, live, work and age... are shaped by the distribution of money, power and resources at global, national and local levels."  
> — WHO Commission on Social Determinants of Health

**SDOH Domains Used in This Taxonomy:**
- Healthcare Access & Coverage
- Quality of Care & Patient Voice
- Social Support & Community
- Economic Stability
- Nutrition & Food Security
- Education & Health Literacy
- Neighborhood & Physical Environment

**Key References:**
- Braveman, P., Egerter, S., & Williams, D. R. (2011). The social determinants of health: coming of age. *Annual Review of Public Health*, 32(1), 381-398.
- Braveman, P., & Gottlieb, L. (2014). The social determinants of health: it's time to consider the causes of the causes. *Public Health Reports*, 129(1_suppl2), 19-31.
- Solar, O., & Irwin, A. (2010). A conceptual framework for action on the social determinants of health. WHO Document Production Services.

### 2. White House Blueprint for Addressing the Maternal Health Crisis (2022)

The Biden-Harris Administration's five-goal framework for addressing the maternal health crisis:

| Goal | Focus Area | Example Programs |
|------|------------|------------------|
| **Goal 1** | Healthcare Access & Coverage | Prenatal care, Postpartum support, Medicaid extension |
| **Goal 2** | Quality of Care & Patient Voice | Health equity initiatives, MMRCs, implicit bias training |
| **Goal 3** | Data Collection & Research | MMRC data, PRAMS, research initiatives |
| **Goal 4** | Perinatal Workforce | Doulas, midwives, CHWs, home visiting programs |
| **Goal 5** | Social & Economic Supports | WIC, housing, food security, workplace protections |

**Reference:** [White House Blueprint for Addressing the Maternal Health Crisis (June 2022)](https://bidenwhitehouse.archives.gov/wp-content/uploads/2022/06/Maternal-Health-Blueprint.pdf)

## Overview

Per advisor feedback, this project focuses specifically on **maternal health programs** rather than general health services. The evaluation framework is designed to:

1. **Track A**: Detect presence/absence of maternal health programs at county level
2. **Track B**: Evaluate detailed extraction of how counties offer maternal programs

## Files

| File | Description |
|------|-------------|
| `gold_maternal.jsonl` | Gold dataset focused on maternal health programs (4 validated counties) |
| `gold_schema.py` | Pydantic schemas for gold dataset validation |
| `metrics.py` | Metric calculation functions |
| `run_eval.py` | Main evaluation script |

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

Organized by White House Blueprint Goals with SDOH Domain alignment:

#### Goal 1: Healthcare Access & Coverage
*SDOH Domain: Healthcare Access*
- **Perinatal Care**: Prenatal Care, Postpartum Support, CPSP
- **Behavioral Health**: Maternal Mental Health, Substance Use Services
- **Reproductive Health**: Family Planning, Title X

#### Goal 2: Quality of Care & Patient Voice
*SDOH Domain: Quality of Care*
- **Health Equity**: Black Infant Health, Healthy Start, Perinatal Equity Initiative
- **Quality Improvement**: MMRCs, Perinatal Quality Collaboratives

#### Goal 4: Perinatal Workforce
*SDOH Domain: Social Support*
- **Home Visiting**: Nurse-Family Partnership, MIECHV, Parents as Teachers
- **Birth Support**: Doula Programs, Midwifery Services
- **Community Health**: Community Health Workers, Lactation Support

#### Goal 5: Social & Economic Supports
*SDOH Domains: Nutrition, Economic Stability*
- **Nutrition**: WIC (Women, Infants, and Children)
- **Adolescent Health**: Teen Pregnancy Programs, AFLP
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

The `src/maternal_taxonomy.py` file contains a comprehensive taxonomy of maternal health programs grounded in the SDOH framework and White House Blueprint:

### Taxonomy Statistics

| Metric | Count |
|--------|------:|
| Program types | 22 |
| Categories | 13 |
| Keywords | 189 |
| Federal programs | 7 |
| SDOH domains | 4 |
| Blueprint goals | 4 |

### Categories

Adolescent Health, Behavioral Health, Birth Support, Breastfeeding, Community Health, Early Childhood, Health Equity, Home Visiting, Maternal Child Health, Nutrition, Perinatal Care, Quality Improvement, Reproductive Health

### Federal Programs

| Program | Category | Blueprint Goal |
|---------|----------|----------------|
| WIC | Nutrition | Goal 5: Social & Economic Supports |
| Nurse-Family Partnership | Home Visiting | Goal 4: Perinatal Workforce |
| MIECHV | Home Visiting | Goal 4: Perinatal Workforce |
| Healthy Families America | Home Visiting | Goal 4: Perinatal Workforce |
| Parents as Teachers | Home Visiting | Goal 4: Perinatal Workforce |
| Healthy Start | Health Equity | Goal 2: Quality of Care |
| Title V MCH Block Grant | Maternal Child Health | Goal 1: Healthcare Access |

### Usage

```bash
# Print full taxonomy summary
python src/maternal_taxonomy.py

# Use in code
from src.maternal_taxonomy import (
    classify_program,
    is_maternal_health_program,
    SDOHDomain,
    BlueprintGoal,
    get_programs_by_blueprint_goal,
)
```
