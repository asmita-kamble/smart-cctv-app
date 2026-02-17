#!/bin/bash

# Fix installation issues with setuptools and pip
# This script fixes the "Cannot import 'setuptools.build_meta'" error

cd "$(dirname "$0")"

echo "=========================================="
echo "Fixing Python Package Installation"
echo "=========================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating new one..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip, setuptools, and wheel first
echo ""
echo "Step 1: Upgrading pip, setuptools, and wheel..."
pip install --upgrade pip setuptools wheel

# Verify setuptools is installed
echo ""
echo "Step 2: Verifying setuptools installation..."
python3 -c "import setuptools; print(f'setuptools version: {setuptools.__version__}')" || {
    echo "ERROR: setuptools is still not working. Trying to reinstall..."
    pip install --force-reinstall setuptools
}

# Install requirements
echo ""
echo "Step 3: Installing project requirements..."
pip install -r requirements.txt

echo ""
echo "=========================================="
echo "Installation fix complete!"
echo "=========================================="
echo ""
echo "If you still encounter issues, try:"
echo "  1. Delete the venv directory: rm -rf venv"
echo "  2. Recreate it: python3 -m venv venv"
echo "  3. Run this script again: ./fix_installation.sh"
echo ""

