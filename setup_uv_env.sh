#!/bin/bash
# Setup script for uv virtual environment

set -e

echo "Setting up uv virtual environment..."

# Create virtual environment with Python 3.9 (or specify another version)
uv venv --python 3.9

# Activate the virtual environment
source .venv/bin/activate

# Install the package in editable mode with test dependencies
uv pip install -e ".[test]"

# Clean up any old build artifacts
rm -rf .eggs
find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true

echo ""
echo "✅ Virtual environment created and dependencies installed!"
echo ""
echo "To activate the virtual environment, run:"
echo "  source .venv/bin/activate"
echo ""
echo "To run tests, use:"
echo "  pytest"
echo ""
echo "Note: Some tests require Docker or Singularity to be installed and running."
echo ""

