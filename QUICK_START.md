# Quick Start - Collect Data for More Counties

## Current Status

✅ **San Diego**: 21 programs  
✅ **Los Angeles**: 5 programs  
⚠️ **9 counties missing data**: Alameda, Fresno, Sacramento, Kern, San Francisco, Orange, Riverside, Santa Clara, Contra Costa

## Step-by-Step Guide

### Step 1: Install Dependencies

```bash
# Install all required packages
pip install -r requirements.txt

# If you get permission errors, use a virtual environment:
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Required packages:**
- `requests` - Web scraping
- `beautifulsoup4` - HTML parsing
- `openai` - LLM API (for Phase 3)
- `pydantic` - Type validation
- And more (see `requirements.txt`)

### Step 2: Configure API Key

```bash
# Copy example env file
cp .env.example .env

# Edit .env and add your OpenAI API key:
OPENAI_API_KEY=your-key-here
API_PROVIDER=openai
```

### Step 3: Check Current Data Status

```bash
python collect_missing_counties.py
```

This shows which counties have data and which need collection.

### Step 4: Run Pipeline for Missing Counties

```bash
# Run all 3 phases for 10 target counties
python run_pipeline.py
```

This will:
1. **Phase 1**: Discover program links for each county
2. **Phase 2**: Extract raw page content (text, contacts, PDFs)
3. **Phase 3**: Structure data using LLM → CSV files

### Step 5: If Discovery Fails

If some counties have empty `programs` arrays, use agentic discovery:

```bash
python improve_discovery.py
```

This uses the agentic system with better search capabilities.

## Expected Output

After running the pipeline, you should have:

```
data/
├── discovery_results.json          # Updated with new counties
├── raw/
│   ├── alameda/                    # New raw JSON files
│   ├── fresno/
│   └── ...
└── structured/
    ├── California_Alameda_Healthcare_Data.csv
    ├── California_Fresno_Healthcare_Data.csv
    └── ...
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'requests'"

**Fix:**
```bash
pip install -r requirements.txt
```

### "ModuleNotFoundError: No module named 'dotenv'"

**Fix:**
```bash
pip install python-dotenv
```

**Note**: The code now handles missing dotenv gracefully, but you need it for `.env` files.

### Counties have empty programs arrays

**Solution:**
```bash
# Use agentic discovery to retry
python improve_discovery.py
```

### Phase 3 fails (no CSV generated)

**Check:**
1. Do you have raw JSON files in `data/raw/{county}/`?
2. Is `OPENAI_API_KEY` set in `.env`?
3. Check Phase 3 output for error messages

## Next Steps After Collection

1. **Run evaluation:**
   ```bash
   python eval/run_eval.py
   ```

2. **Check results:**
   ```bash
   python collect_missing_counties.py
   ```

3. **View structured data:**
   ```bash
   ls -lh data/structured/*.csv
   ```
