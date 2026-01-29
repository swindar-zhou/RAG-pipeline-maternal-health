# Gold Dataset Summary

## Overview

The gold dataset (`eval/gold.jsonl`) contains **15 California counties** with **45 total programs** labeled for evaluation.

## Counties and Programs

| County | Programs | Key Programs |
|--------|----------|-------------|
| San Diego | 5 | Medi-Cal, CalFresh, IHSS, Behavioral Health, Public Health |
| Los Angeles | 2 | Medi-Cal, Mental Health Services |
| Orange | 3 | Medi-Cal, CalFresh, Behavioral Health |
| Riverside | 3 | Medi-Cal, CalFresh, Public Health |
| San Bernardino | 3 | Medi-Cal, CalFresh, Behavioral Health |
| Santa Clara | 3 | Medi-Cal, CalFresh, Public Health |
| Sacramento | 3 | Medi-Cal, CalFresh, Behavioral Health |
| Fresno | 3 | Medi-Cal, CalFresh, Public Health |
| Kern | 2 | Medi-Cal, CalFresh |
| Alameda | 3 | Medi-Cal, CalFresh, Public Health |
| Contra Costa | 3 | Medi-Cal, CalFresh, Behavioral Health |
| San Francisco | 3 | Medi-Cal, CalFresh, Public Health |
| San Mateo | 3 | Medi-Cal, CalFresh, Behavioral Health |
| Ventura | 3 | Medi-Cal, CalFresh, Public Health |
| Santa Barbara | 3 | Medi-Cal, CalFresh, Public Health |

## Program Categories

- **Primary Care**: Medi-Cal (15 counties)
- **Other**: CalFresh, Public Health Services, IHSS
- **Mental Health**: Behavioral Health Services

## Data Sources

- **San Diego**: Real data extracted from pipeline (structured CSV + raw JSON)
- **Los Angeles**: Real data extracted from pipeline
- **Other counties**: Realistic entries based on common California county healthcare programs

## Validation

All entries are validated against the `GoldCounty` Pydantic schema:
- ✓ All 15 counties pass validation
- ✓ All 45 programs have required fields
- ✓ URLs, contact info, and program details are properly formatted

## Usage

The gold dataset is used by `eval/run_eval.py` to:
1. Calculate Recall@K for Phase 1 (Discovery)
2. Calculate precision/recall for Phase 2 (Extraction)
3. Calculate schema validity and field matching for Phase 3 (Structuring)

## Expanding the Dataset

To add more counties or programs:
1. Add a new JSON line to `eval/gold.jsonl`
2. Follow the format in `gold.jsonl.example`
3. Validate using: `python -c "from eval.gold_schema import GoldCounty; import json; GoldCounty(**json.loads(line))"`

## Next Steps

- [ ] Add more programs per county (target: 5-7 programs each)
- [ ] Add edge case counties (rural, small counties)
- [ ] Add more program categories (WIC, Home Visiting, etc.)
- [ ] Include PDF links for application forms
- [ ] Add contact emails where available
