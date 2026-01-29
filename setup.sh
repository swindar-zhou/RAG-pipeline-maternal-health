#!/bin/bash
# Setup script for iTREDS project

set -e

echo "============================================================"
echo "🔧 iTREDS Project Setup"
echo "============================================================"

# Check if virtual environment exists
if [ -d ".venv" ]; then
    echo "✓ Virtual environment found"
    echo "Activating virtual environment..."
    source .venv/bin/activate
else
    echo "Creating virtual environment..."
    python3 -m venv .venv
    source .venv/bin/activate
fi

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt

# Verify installation
echo ""
echo "Verifying installation..."
python3 -c "import requests; import bs4; import openai; print('✓ All dependencies installed')" || {
    echo "✗ Some dependencies failed to install"
    exit 1
}

echo ""
echo "============================================================"
echo "✅ Setup Complete!"
echo "============================================================"
echo ""
echo "Next steps:"
echo "1. Activate virtual environment: source .venv/bin/activate"
echo "2. Configure .env: cp .env.example .env"
echo "3. Check data status: python collect_missing_counties.py"
echo "4. Run pipeline: python run_pipeline.py"
echo ""
