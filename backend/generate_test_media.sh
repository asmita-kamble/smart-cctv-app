#!/bin/bash

# Script to generate test media files for Smart CCTV testing

echo "Generating test media files..."
echo "================================"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Check if Python is available
if command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
elif command -v python &> /dev/null; then
    PYTHON_CMD=python
else
    echo "Error: Python not found. Please install Python 3."
    exit 1
fi

# Check if required packages are installed
echo "Checking dependencies..."
$PYTHON_CMD -c "import cv2, numpy" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Error: Required packages (opencv-python, numpy) not found."
    echo "Please install them: pip install opencv-python numpy"
    exit 1
fi

# Run the test media generator
echo "Creating test media files..."
$PYTHON_CMD create_test_media.py

if [ $? -eq 0 ]; then
    echo ""
    echo "================================"
    echo "Test media files created successfully!"
    echo "Location: backend/test_media/"
    echo ""
    echo "You can now:"
    echo "1. Start the backend server"
    echo "2. Login to the dashboard"
    echo "3. Add a camera"
    echo "4. Upload test media files to trigger alerts"
else
    echo "Error: Failed to create test media files"
    exit 1
fi

