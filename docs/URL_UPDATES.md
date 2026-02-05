# Health Department URL Updates

## Summary
Updated scraping files to use the health department URLs from `discovery_results.json`.

## Changes Made

### 1. `src/config.py`
- **Updated Kern county URL**: `https://www.kerncounty.com/` → `https://www.kernpublichealth.com/`
- **Added `HEALTH_DEPT_URLS` mapping** with known health department URLs:
  - Alameda: `https://www.acgov.org/government/dotgov.htm`
  - Sacramento: `https://dhs.saccounty.gov/Pages/DHS-Home.aspx`
  - Los Angeles: `https://www.lacounty.gov/`
  - San Francisco: `https://www.sf.gov/departments--department-public-health`
  - Orange: `https://www.ochealthinfo.com/`
  - Santa Clara: `https://publichealth.santaclaracounty.gov/home`
  - Contra Costa: `https://www.cchealth.org/`

### 2. `scraper_discovery.py`
- **Imports `HEALTH_DEPT_URLS`** from `src.config`
- **Updated `run_discovery_for_county()`** to check for known health department URLs first before searching
- If a known URL exists, it uses it directly instead of searching

### 3. `agents/discovery_agent.py`
- **Imports `HEALTH_DEPT_URLS`** from `src.config`
- **Updated `run()` method** to check for known health department URLs in the SEARCH state
- Uses known URLs as a priority before performing search

### 4. `scraper.py`
- **Updated Kern county URL** to match `src/config.py`

### 5. `src/__init__.py`
- **Added `HEALTH_DEPT_URLS`** to exports

## How It Works

1. **Discovery Process**:
   - When running discovery for a county, the system first checks if there's a known health department URL in `HEALTH_DEPT_URLS`
   - If found, it uses that URL directly (faster and more reliable)
   - If not found, it falls back to the original search behavior

2. **Benefits**:
   - Faster discovery for counties with known URLs
   - More reliable results (no need to search and guess)
   - Can be easily updated as more health department URLs are discovered

## Notes

- **Riverside County**: The `discovery_results.json` shows `county_url` as a CDC NPIN page. The actual county website (`https://www.rivco.org/`) is maintained in `CALIFORNIA_COUNTIES` for new discoveries.
- **Kern County**: Updated to use the public health website directly, which may be more effective for discovery.

## Future Updates

To add more health department URLs:
1. Update `HEALTH_DEPT_URLS` in `src/config.py`
2. The discovery scripts will automatically use them
