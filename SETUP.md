# Setup Guide

## Quick Setup

### 1. Install Dependencies

```bash
# Install all required packages
pip install -r requirements.txt

# Or if using a virtual environment (recommended):
python3 -m venv .venv
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate  # On Windows
pip install -r requirements.txt
```

### 2. Verify Installation

```bash
# Test that key modules are installed
python3 -c "import requests; import bs4; import openai; print('✓ All dependencies installed')"
```

### 3. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env and add your API keys
# For OpenAI:
#   OPENAI_API_KEY=your-key-here
#   API_PROVIDER=openai
```

### 4. Test Setup

```bash
# Test API connectivity
python test_setup.py
```

## Common Issues

### Issue: `ModuleNotFoundError: No module named 'requests'`

**Solution:**
```bash
pip install -r requirements.txt
```

### Issue: `ModuleNotFoundError: No module named 'dotenv'`

**Solution:**
```bash
pip install python-dotenv
# Or install all dependencies:
pip install -r requirements.txt
```

**Note**: The code now handles missing dotenv gracefully, but you'll need it to load `.env` files.

### Issue: Permission errors during pip install

**Solution:**
```bash
# Use virtual environment (recommended)
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Or use --user flag
pip install --user -r requirements.txt
```

## Required Dependencies

From `requirements.txt`:
- **Web scraping**: `requests`, `beautifulsoup4`, `lxml`
- **LLM APIs**: `openai`, `anthropic`
- **Utilities**: `python-dotenv`, `httpx`, `pydantic`
- **Testing**: `pytest`, `pytest-mock`, `pytest-cov`

## After Setup

Once dependencies are installed:

1. **Check data status:**
   ```bash
   python collect_missing_counties.py
   ```

2. **Run pipeline for more counties:**
   ```bash
   python run_pipeline.py
   ```

3. **If discovery fails, use agentic system:**
   ```bash
   python improve_discovery.py
   ```
