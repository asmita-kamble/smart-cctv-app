#!/bin/bash

# Fix NumPy 2.x compatibility issue with OpenCV
# OpenCV 4.8.1.78 was compiled against NumPy 1.x and is incompatible with NumPy 2.x

cd "$(dirname "$0")"

echo "=========================================="
echo "Fixing NumPy/OpenCV Compatibility Issue"
echo "=========================================="
echo ""

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
else
    echo "ERROR: Virtual environment not found. Please create it first:"
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    exit 1
fi

echo ""
echo "Step 1: Uninstalling NumPy 2.x..."
pip uninstall -y numpy

echo ""
echo "Step 2: Installing NumPy 1.x (compatible with OpenCV)..."
pip install "numpy>=1.26.0,<2.0.0"

echo ""
echo "Step 3: Verifying installation..."
python3 -c "import numpy; print(f'NumPy version: {numpy.__version__}')" || {
    echo "ERROR: NumPy import failed"
    exit 1
}

python3 -c "import cv2; print('OpenCV import: OK')" || {
    echo "WARNING: OpenCV import failed. You may need to reinstall opencv-python:"
    echo "  pip install --force-reinstall opencv-python==4.8.1.78"
}

echo ""
echo "=========================================="
echo "Fix complete!"
echo "=========================================="
echo ""
echo "You can now run the application:"
echo "  python run.py"
echo ""

