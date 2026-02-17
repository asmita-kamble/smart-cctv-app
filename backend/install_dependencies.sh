#!/bin/bash

# Smart CCTV Backend Dependency Installation Script
# Handles Python 3.13 compatibility issues

cd "$(dirname "$0")"

echo "=========================================="
echo "Smart CCTV Backend Dependency Installation"
echo "=========================================="
echo ""

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

echo "Detected Python version: $PYTHON_VERSION"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip, setuptools, and wheel
echo ""
echo "Step 1: Upgrading pip, setuptools, and wheel..."
pip install --upgrade pip setuptools wheel

# Install CMake if needed (for dlib)
echo ""
echo "Step 2: Checking for CMake (required for dlib)..."
if ! command -v cmake &> /dev/null; then
    echo "CMake not found. Installing via Homebrew..."
    if command -v brew &> /dev/null; then
        brew install cmake
    else
        echo "ERROR: Homebrew not found. Please install CMake manually:"
        echo "  macOS: brew install cmake"
        echo "  Ubuntu/Debian: sudo apt-get install cmake"
        echo "  Then run this script again."
        exit 1
    fi
else
    CMAKE_VERSION=$(cmake --version | head -n1)
    echo "CMake found: $CMAKE_VERSION"
fi

# Handle Python 3.13 compatibility
if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 13 ]; then
    echo ""
    echo "Step 3: Python 3.13 detected - installing compatible packages..."
    
    # Install numpy first (Python 3.13 compatible, but < 2.0 for OpenCV compatibility)
    echo "  Installing numpy (Python 3.13 compatible, < 2.0 for OpenCV)..."
    pip install "numpy>=1.26.0,<2.0.0"
    
    # Install psycopg (v3) instead of psycopg2-binary for Python 3.13
    echo "  Installing psycopg (Python 3.13 compatible PostgreSQL driver)..."
    pip install "psycopg[binary]>=3.1.0"
    
    # Install other packages that don't need special handling
    echo "  Installing other dependencies..."
    pip install Flask==3.0.0 Flask-SQLAlchemy==3.1.1 Flask-CORS==4.0.0 Flask-JWT-Extended==4.6.0 Flask-Bcrypt==1.0.1
    pip install pymongo==4.6.1 python-dotenv==1.0.0 marshmallow==3.20.1
    pip install opencv-python==4.8.1.78 Pillow Werkzeug==3.0.1 python-dateutil==2.8.2
    
    # Install dlib and face-recognition (requires CMake)
    echo "  Installing dlib (this may take a while)..."
    pip install dlib
    echo "  Installing face-recognition..."
    pip install face-recognition==1.3.0
    
else
    echo ""
    echo "Step 3: Installing all dependencies from requirements.txt..."
    pip install -r requirements.txt
fi

echo ""
echo "=========================================="
echo "Installation complete!"
echo "=========================================="
echo ""
echo "If you encounter any issues:"
echo "  1. Make sure CMake is installed: cmake --version"
echo "  2. For Python 3.13, consider using Python 3.11 or 3.12 for better compatibility"
echo "  3. Check the LOCAL_SETUP.md for troubleshooting tips"
echo ""

