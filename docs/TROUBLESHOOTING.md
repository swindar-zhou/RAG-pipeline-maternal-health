# Troubleshooting Guide

## Common Installation Issues

### Issue: `pydantic-core` build fails on Python 3.13

**Error:**
```
TypeError: ForwardRef._evaluate() missing 1 required keyword-only argument: 'recursive_guard'
ERROR: Failed building wheel for pydantic-core
```

**Cause:** Older versions of pydantic (e.g., 2.5.0) try to build from source on Python 3.13 and fail due to API changes.

**Solution:**
```bash
# Upgrade pydantic to a version with pre-built wheels for Python 3.13
pip install --upgrade "pydantic>=2.9.0"

# Or reinstall from requirements.txt (now updated)
pip install -r requirements.txt
```

**Note:** `requirements.txt` now uses `pydantic>=2.9.0,<3.0.0` which has pre-built wheels for Python 3.13.

### Issue: `ModuleNotFoundError: No module named 'requests'`

**Solution:**
```bash
# Install dependencies
pip install -r requirements.txt

# Or use setup script
./setup.sh
```

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

### Issue: `ModuleNotFoundError: No module named 'dotenv'`

**Solution:**
```bash
pip install python-dotenv
```

**Note:** The code handles missing dotenv gracefully, but you need it to load `.env` files.

### Issue: Counties have empty programs arrays

**Cause:** Discovery phase couldn't find health department pages or program links.

**Solution:**
```bash
# Use agentic discovery to retry failed counties
python improve_discovery.py
```

### Issue: Phase 3 fails (no CSV generated)

**Check:**
1. Do you have raw JSON files in `data/raw/{county}/`?
2. Is `OPENAI_API_KEY` set in `.env`?
3. Check Phase 3 output for error messages

**Solution:**
```bash
# Verify API key is set
cat .env | grep OPENAI_API_KEY

# Test API connectivity
python test_setup.py

# Re-run Phase 3
python scraper_structure.py
```

## Python Version Compatibility

- **Python 3.8+**: Fully supported
- **Python 3.13**: Supported (requires pydantic>=2.9.0)

## System-Specific Issues

### macOS: SSL/Certificate errors

If you see SSL errors:
```bash
# Install certificates
pip install --upgrade certifi
/Applications/Python\ 3.13/Install\ Certificates.command
```

### Linux: Missing system dependencies

For `lxml`:
```bash
# Ubuntu/Debian
sudo apt-get install libxml2-dev libxslt1-dev

# Fedora/RHEL
sudo dnf install libxml2-devel libxslt-devel
```

## Getting Help

1. Check this troubleshooting guide
2. Review `SETUP.md` for setup instructions
3. Check `QUICK_START.md` for quick reference
4. Review error messages carefully - they often contain hints
