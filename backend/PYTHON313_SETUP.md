# Python 3.13 Setup Guide

Python 3.13 is very new and some packages don't have pre-built wheels yet. This guide helps you set up the project with Python 3.13.

## Quick Fix for Python 3.13

### Option 1: Use Automated Script (Recommended)

```bash
cd backend
./install_dependencies.sh
```

This script will:
- Detect Python 3.13
- Install CMake (required for dlib)
- Install Python 3.13-compatible package versions
- Handle all compatibility issues automatically

### Option 2: Manual Installation

```bash
cd backend
source venv/bin/activate

# 1. Install CMake (required for dlib)
brew install cmake  # macOS
# OR
sudo apt-get install cmake  # Linux

# 2. Upgrade pip and build tools
pip install --upgrade pip setuptools wheel

# 3. Install Python 3.13 compatible packages
pip install "numpy>=1.26.0"
pip install "psycopg[binary]>=3.1.0"  # Use psycopg v3 instead of psycopg2-binary

# 4. Install Flask and related packages
pip install Flask==3.0.0 Flask-SQLAlchemy==3.1.1 Flask-CORS==4.0.0
pip install Flask-JWT-Extended==4.6.0 Flask-Bcrypt==1.0.1

# 5. Install other dependencies
pip install pymongo==4.6.1 python-dotenv==1.0.0 marshmallow==3.20.1
pip install opencv-python==4.8.1.78 Pillow Werkzeug==3.0.1 python-dateutil==2.8.2

# 6. Install dlib and face-recognition (requires CMake)
pip install dlib
pip install face-recognition==1.3.0
```

## Important Notes

### psycopg vs psycopg2

- **Python 3.13**: Use `psycopg[binary]>=3.1.0` (psycopg v3)
- **Python 3.11/3.12**: Use `psycopg2-binary==2.9.9`

SQLAlchemy works with both, so no code changes are needed. The connection string `postgresql://` works with both drivers.

### CMake Requirement

`dlib` requires CMake to build. Make sure it's installed:
```bash
cmake --version  # Should show version 3.x or higher
```

### NumPy Version

Python 3.13 requires NumPy 1.26.0 or higher. Older versions won't build.

## Recommended: Use Python 3.11 or 3.12

For the most stable experience, we recommend using Python 3.11 or 3.12:

```bash
# Remove old venv
rm -rf venv

# Create new venv with Python 3.11
python3.11 -m venv venv  # or python3.12
source venv/bin/activate

# Standard installation works
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

## Troubleshooting

### "Failed to build psycopg2-binary"
- **Solution**: Use `psycopg[binary]>=3.1.0` for Python 3.13

### "CMake is not installed"
- **Solution**: Install CMake via Homebrew (macOS) or apt (Linux)

### "Failed to build numpy"
- **Solution**: Install `numpy>=1.26.0` first, then other packages

### "Failed to build dlib"
- **Solution**: Make sure CMake is installed and in your PATH

## Verification

After installation, verify everything works:

```bash
# Test imports
python3 -c "import numpy; print(f'NumPy: {numpy.__version__}')"
python3 -c "import psycopg; print('psycopg: OK')"  # Python 3.13
# OR
python3 -c "import psycopg2; print('psycopg2: OK')"  # Python 3.11/3.12
python3 -c "import dlib; print('dlib: OK')"
python3 -c "import face_recognition; print('face_recognition: OK')"

# Run the server
python run.py
```

