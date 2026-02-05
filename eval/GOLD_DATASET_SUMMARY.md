# Gold Dataset Summary

## Overview

This project uses **two gold datasets**:

1. **`gold_maternal.jsonl`** (Primary) - Focused on maternal health programs per advisor feedback
2. **`gold.jsonl`** (Legacy) - General health programs, kept for reference

## Maternal Health Gold Dataset

### Summary

| Metric | Value |
|--------|-------|
| Counties | 4 (validated by advisor) |
| Total Programs | 10 |
| Focus | Maternal health only |

### Counties and Programs

| County | Programs | Key Maternal Programs |
|--------|:--------:|----------------------|
| San Diego | 3 | WIC, Black Infant Health, Nurse-Family Partnership |
| Los Angeles | 3 | WIC, Black Infant Health, Nurse-Family Partnership |
| Sacramento | 2 | MCAH, WIC |
| San Francisco | 2 | MCAH, WIC |

### Program Categories (Maternal Focus)

| Category | Programs | Description |
|----------|:--------:|-------------|
| **WIC/Nutrition** | 4 | Women, Infants, and Children nutrition programs |
| **Home Visiting** | 4 | NFP, Black Infant Health, MIECHV |
| **Maternal Health** | 2 | MCAH comprehensive services |

### Validated Maternal Health URLs

These entry points were manually validated by advisor:

```
San Diego:    sandiegocounty.gov/.../maternal_child_family_health_services.html
Los Angeles:  publichealth.lacounty.gov/mch/
Sacramento:   dhs.saccounty.gov/.../MCAH-Program.aspx
San Francisco: sf.gov/.../maternal-child-and-adolescent-health
```

## Legacy Gold Dataset

### Summary

| Metric | Value |
|--------|-------|
| Counties | 15 |
| Total Programs | 45 |
| Focus | General health programs |

### Counties

| County | Programs | Key Programs |
|--------|:--------:|-------------|
| San Diego | 5 | Medi-Cal, CalFresh, IHSS, Behavioral Health |
| Los Angeles | 2 | Medi-Cal, Mental Health |
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

**Note**: Per advisor feedback, these general health programs (Medi-Cal, CalFresh) should **not** be mixed with maternal health analysis. Use `gold_maternal.jsonl` for maternal health evaluation.

## Pipeline Results (Feb 2026)

### Discovery Phase Results

| County | Maternal Programs Discovered | Top Categories |
|--------|:----------------------------:|----------------|
| San Diego | 3 | Perinatal Care, Health Equity |
| Los Angeles | 11 | Breastfeeding, Perinatal Care, Birth Support |
| Sacramento | 5 | Breastfeeding, Maternal Child Health |
| San Francisco | 8 | WIC, Home Visiting, Health Equity |
| **Total** | **27** | |

### Structuring Phase Results

| County | Programs Extracted |
|--------|:------------------:|
| San Diego | 9 |
| Los Angeles | 20 |
| Sacramento | 5 |
| San Francisco | 12 |
| **Total** | **46** |

## Schema Validation

### Maternal Health Schema Fields

```python
{
    "county_name": str,           # Required
    "county_url": str,            # Required
    "maternal_health_url": str,   # Validated entry point
    "has_maternal_programs": bool,
    "programs": [
        {
            "program_name": str,
            "program_url": str,
            "category": str,      # WIC, Home Visiting, Health Equity, etc.
            "description": str,
            "target_population": str,
            "eligibility_requirements": str,
            "services_provided": List[str],
            "contact_phone": Optional[str],
            "contact_email": Optional[str]
        }
    ]
}
```

## Expanding the Dataset

### Adding New Counties

1. **Find maternal health section** on county website
2. **Add to `src/config.py`**:
   ```python
   MATERNAL_HEALTH_URLS["County Name"] = "https://..."
   ```
3. **Run discovery** to verify programs are found
4. **Add gold entry** to `gold_maternal.jsonl`
5. **Run evaluation** to measure performance

### Expected Programs per County

A typical California county maternal health section may include:

- WIC (Women, Infants, Children)
- Black Infant Health (if applicable)
- Nurse-Family Partnership or home visiting
- MCAH (Maternal, Child, Adolescent Health)
- Breastfeeding/lactation support
- Prenatal care coordination
- Teen pregnancy programs

## Next Steps

- [ ] Expand to more California counties (target: 10-15 validated)
- [ ] Add Florida counties using state reference URLs
- [ ] Include specific program URLs for gold entries
- [ ] Add contact information where available
- [ ] Create evaluation metrics specific to maternal health detection
