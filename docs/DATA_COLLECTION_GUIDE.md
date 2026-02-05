# Data Collection Guide

## Bug Fixes ✅

### Fixed: `ModuleNotFoundError: No module named 'dotenv'`

**Problem**: Scripts failed if `python-dotenv` wasn't installed.

**Solution**: Made dotenv import optional in all files:
- `src/config.py`
- `scraper_structure.py`
- `test_setup.py`
- `scraper.py`

Now scripts work even if dotenv isn't installed (environment variables can still be set manually).

## Current Data Status

### Counties with Structured Data (CSV files)
- ✅ **San Diego** - 22 programs
- ✅ **Los Angeles** - 5 programs

### Counties Missing Data
- ⚠ Alameda, Fresno, Sacramento, Kern, San Francisco, Orange, Riverside, Santa Clara, Contra Costa

## Collecting Data for More Counties

### Option 1: Run Full Pipeline (Recommended)

```bash
# This will run all 3 phases for 10 target counties
python run_pipeline.py
```

**Target counties:**
- Alameda, Fresno, Sacramento, Kern, Los Angeles
- San Francisco, Orange, Riverside, Santa Clara, Contra Costa

### Option 2: Check Status First

```bash
# See which counties have data and which are missing
python collect_missing_counties.py
```

This shows:
- Which counties have structured CSVs
- How many programs each has
- Which counties need data collection

### Option 3: Improve Discovery for Failed Counties

If some counties have empty `programs` arrays after discovery, use the agentic system:

```bash
python improve_discovery.py
```

This will:
1. Find counties with empty programs
2. Use agentic discovery to retry them
3. Update `data/discovery_results.json` with improved results

### Option 4: Run Individual Phases

```bash
# Phase 1: Discovery (finds program links)
python scraper_discovery.py

# Phase 2: Extraction (fetches page content)
python scraper_extract.py

# Phase 3: Structuring (LLM extraction to CSV)
python scraper_structure.py
```

## Why Some Counties Have Empty Programs

The discovery phase may fail if:
1. **Health department not found** - County website structure doesn't match expected patterns
2. **Maternal section not found** - No clear maternal/child health section
3. **Program links not found** - Keywords don't match county's terminology

**Solutions:**
- Use `improve_discovery.py` (agentic system with better search)
- Manually check county websites and update discovery keywords
- Use agentic discovery agent directly

## Expected Output

After running the pipeline, you should have:

```
data/
├── discovery_results.json          # Phase 1: Program links per county
├── raw/
│   ├── alameda/                    # Phase 2: Raw page JSONs
│   ├── fresno/
│   └── ...
└── structured/
    ├── California_Alameda_Healthcare_Data.csv
    ├── California_Fresno_Healthcare_Data.csv
    └── ...
```

## Troubleshooting

### Issue: "No programs found" for a county

**Check:**
1. Does the county have a health department page?
   - Look in `data/discovery_results.json` for `health_dept_url`
2. Are there any raw JSON files?
   - Check `data/raw/{county-slug}/`
3. Try agentic discovery:
   ```bash
   python improve_discovery.py
   ```

### Issue: Phase 3 fails (no CSV generated)

**Check:**
1. Do you have raw JSON files in `data/raw/{county}/`?
2. Is `OPENAI_API_KEY` set in `.env`?
3. Check Phase 3 output for error messages

### Issue: Import errors

**Solution:**
```bash
# Install all dependencies
pip install -r requirements.txt
```

## Next Steps

1. **Run pipeline for missing counties:**
   ```bash
   python run_pipeline.py
   ```

2. **Check results:**
   ```bash
   python collect_missing_counties.py
   ```

3. **If discovery failed, retry with agentic:**
   ```bash
   python improve_discovery.py
   ```

4. **Run evaluation:**
   ```bash
   python eval/run_eval.py
   ```
