# Local Setup and Validation Guide

This guide will help you set up and validate the Smart CCTV application on your local machine.

## Prerequisites

Before starting, ensure you have the following installed:

- **Python 3.9+** - Check with: `python3 --version`
- **PostgreSQL 12+** - Check with: `psql --version`
- **MongoDB 4.4+** - Check with: `mongosh --version` or `mongo --version`
- **Node.js 16+** (for frontend) - Check with: `node --version`
- **pip** (Python package manager)
- **Homebrew** (macOS) or appropriate package manager for your OS

## Step 1: Database Setup

### PostgreSQL Setup

1. **Start PostgreSQL service:**
   ```bash
   # macOS (with Homebrew):
   brew services start postgresql@14
   
   # Linux:
   sudo systemctl start postgresql
   
   # Windows:
   # Start PostgreSQL service from Services panel
   ```

2. **Create the database:**
   ```bash
   # Connect to PostgreSQL
   psql -U postgres
   
   # Create database
   CREATE DATABASE smart_cctv;
   
   # Exit psql
   \q
   ```

3. **Verify database exists:**
   ```bash
   psql -U postgres -l | grep smart_cctv
   ```

### MongoDB Setup

1. **Start MongoDB service:**
   ```bash
   # macOS (with Homebrew):
   brew services start mongodb-community
   
   # Linux:
   sudo systemctl start mongod
   
   # Windows:
   # Start MongoDB service from Services panel
   ```

2. **Verify MongoDB is running:**
   ```bash
   mongosh --eval "db.adminCommand('ping')"
   # Should return: { ok: 1 }
   ```

## Step 2: Backend Setup

### 2.1 Create Virtual Environment

```bash
cd backend
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### 2.2 Install Dependencies

```bash
# Make sure virtual environment is activated
# First, upgrade pip, setuptools, and wheel to fix common installation issues
pip install --upgrade pip setuptools wheel

# Check your Python version
python --version

# For Python 3.13, use the updated requirements file
# For Python 3.11 or 3.12, use the standard requirements.txt
if python --version | grep -q "3.13"; then
    # Python 3.13 - use updated numpy version
    pip install numpy>=1.26.0  # Install numpy first
    pip install -r requirements.txt
else
    # Python 3.11/3.12 - standard installation
    pip install -r requirements.txt
fi
```

**If you encounter "Cannot import 'setuptools.build_meta'" error:**
```bash
# Run the fix script
./fix_installation.sh

# Or manually:
pip install --force-reinstall setuptools
pip install -r requirements.txt
```

**If you encounter numpy build errors with Python 3.13:**
```bash
# Option 1: Install numpy first (recommended)
pip install --upgrade pip setuptools wheel
pip install "numpy>=1.26.0,<2.0.0"  # NumPy < 2.0 required for OpenCV compatibility
pip install -r requirements.txt

# Option 2: Use Python 3.11 or 3.12 instead (more stable)
python3.11 -m venv venv  # or python3.12
source venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

**If you encounter psycopg2-binary build errors with Python 3.13:**
```bash
# Python 3.13 requires psycopg (v3) instead of psycopg2-binary
pip install "psycopg[binary]>=3.1.0"
# Then install remaining packages
pip install -r requirements.txt --no-deps
pip install Flask==3.0.0 Flask-SQLAlchemy==3.1.1 Flask-CORS==4.0.0 Flask-JWT-Extended==4.6.0 Flask-Bcrypt==1.0.1
pip install pymongo==4.6.1 python-dotenv==1.0.0 marshmallow==3.20.1
pip install opencv-python==4.8.1.78 "numpy>=1.26.0" Pillow Werkzeug==3.0.1 python-dateutil==2.8.2
```

**If you encounter dlib build errors (CMake not found):**
```bash
# Install CMake first
# macOS:
brew install cmake

# Ubuntu/Debian:
sudo apt-get install cmake

# Then install dlib
pip install dlib
pip install face-recognition==1.3.0
```

**Note**: If you encounter issues installing `face_recognition`, install system dependencies first:

```bash
# macOS:
brew install cmake
pip install dlib
pip install face_recognition

# Ubuntu/Debian:
sudo apt-get install cmake libopenblas-dev liblapack-dev
pip install dlib
pip install face_recognition
```

### 2.3 Configure Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env file with your database credentials
# Use your preferred editor (nano, vim, code, etc.)
nano .env
```

Update the following in `.env`:
- `POSTGRES_USER` - Your PostgreSQL username (default: postgres)
- `POSTGRES_PASSWORD` - Your PostgreSQL password
- `SECRET_KEY` - Generate a random secret key
- `JWT_SECRET_KEY` - Generate a random JWT secret key

**Generate secret keys:**
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### 2.4 Create Upload Directory

```bash
mkdir -p uploads
```

### 2.5 Run the Backend

```bash
# Make sure virtual environment is activated
python run.py
```

You should see output like:
```
 * Running on http://0.0.0.0:5000
 * Debug mode: on
```

## Step 3: Validate Backend

### 3.1 Health Check

Open a new terminal and test the health endpoint:

```bash
curl http://localhost:5000/api/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "message": "Smart CCTV API is running"
}
```

### 3.2 Test Database Connections

The health check doesn't verify database connections. Let's test them:

**Test PostgreSQL:**
```bash
psql -U postgres -d smart_cctv -c "SELECT version();"
```

**Test MongoDB:**
```bash
mongosh --eval "db.adminCommand('ping')"
```

### 3.3 Create Test User

```bash
# Register a test user
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password": "Test123!"
  }'
```

**Expected response:**
```json
{
  "message": "User registered successfully",
  "user": {
    "id": 1,
    "email": "test@example.com",
    "username": "testuser",
    "role": "user"
  }
}
```

### 3.4 Test Authentication

```bash
# Login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test123!"
  }'
```

**Expected response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "email": "test@example.com",
    "username": "testuser",
    "role": "user"
  }
}
```

**Save the token** for subsequent requests:
```bash
export TOKEN="your-access-token-here"
```

### 3.5 Test Protected Endpoint

```bash
# Get current user (requires authentication)
curl -X GET http://localhost:5000/api/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

**Expected response:**
```json
{
  "id": 1,
  "email": "test@example.com",
  "username": "testuser",
  "role": "user"
}
```

### 3.6 Create Admin User

```bash
# Register admin user
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "username": "admin",
    "password": "Admin123!",
    "role": "admin"
  }'
```

### 3.7 Test Camera Creation

```bash
# Login as admin first
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "Admin123!"
  }'

# Save admin token
export ADMIN_TOKEN="admin-access-token-here"

# Create a camera
curl -X POST http://localhost:5000/api/cameras \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{
    "name": "Main Entrance",
    "location": "Building A - Front Door",
    "status": "active"
  }'
```

**Expected response:**
```json
{
  "id": 1,
  "name": "Main Entrance",
  "location": "Building A - Front Door",
  "status": "active",
  "created_at": "2024-01-01T12:00:00"
}
```

### 3.8 Test List Cameras

```bash
curl -X GET http://localhost:5000/api/cameras \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

## Step 4: Frontend Setup (Optional)

If the frontend is set up:

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

The frontend should be available at `http://localhost:3000`

## Step 5: Complete Validation Checklist

Use this checklist to ensure everything is working:

- [ ] PostgreSQL is running and database `smart_cctv` exists
- [ ] MongoDB is running and accessible
- [ ] Backend server starts without errors
- [ ] Health endpoint returns `{"status": "healthy"}`
- [ ] Can register a new user
- [ ] Can login and receive JWT token
- [ ] Can access protected endpoint with token
- [ ] Can create admin user
- [ ] Can create a camera (with auth)
- [ ] Can list cameras (with auth)
- [ ] Database tables are created (check PostgreSQL)
- [ ] Upload directory exists

## Step 6: Verify Database Tables

```bash
# Connect to PostgreSQL
psql -U postgres -d smart_cctv

# List all tables
\dt

# Check users table
SELECT id, email, username, role FROM users;

# Check cameras table
SELECT id, name, location, status FROM cameras;

# Exit
\q
```

## Troubleshooting

### Backend won't start

1. **Check virtual environment is activated:**
   ```bash
   which python  # Should show venv path
   ```

2. **Check database connections:**
   ```bash
   # PostgreSQL
   pg_isready
   
   # MongoDB
   mongosh --eval "db.adminCommand('ping')"
   ```

3. **Check environment variables:**
   ```bash
   # Make sure .env file exists and has correct values
   cat .env
   ```

4. **Check for missing dependencies:**
   ```bash
   pip list | grep -E "Flask|psycopg2|pymongo"
   ```

### Database connection errors

1. **PostgreSQL:**
   - Verify service is running: `brew services list | grep postgresql`
   - Check credentials in `.env`
   - Verify database exists: `psql -U postgres -l`

2. **MongoDB:**
   - Verify service is running: `brew services list | grep mongodb`
   - Check connection: `mongosh --eval "db.adminCommand('ping')"`

### Import errors

1. **Activate virtual environment:**
   ```bash
   source venv/bin/activate
   ```

2. **Fix setuptools issue:**
   ```bash
   pip install --upgrade pip setuptools wheel
   pip install --force-reinstall setuptools
   ```

3. **Reinstall dependencies:**
   ```bash
   pip install -r requirements.txt --force-reinstall
   ```

### "Cannot import 'setuptools.build_meta'" error

This error occurs when setuptools is missing or corrupted. Fix it with:

```bash
# Option 1: Use the fix script
./fix_installation.sh

# Option 2: Manual fix
source venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install --force-reinstall setuptools
pip install -r requirements.txt

# Option 3: Recreate virtual environment (if above doesn't work)
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

### NumPy build errors with Python 3.13

If you see "Failed to build 'numpy'" errors:

```bash
# Solution 1: Install numpy 1.26.0+ first (Python 3.13 compatible, but < 2.0 for OpenCV)
pip install --upgrade pip setuptools wheel
pip install "numpy>=1.26.0,<2.0.0"  # NumPy 2.x incompatible with OpenCV 4.8.1.78
pip install -r requirements.txt
```

### NumPy 2.x / OpenCV compatibility error

If you see "A module that was compiled using NumPy 1.x cannot be run in NumPy 2.x":

```bash
# Quick fix script
./fix_numpy.sh

# Or manually:
pip uninstall -y numpy
pip install "numpy>=1.26.0,<2.0.0"
python3 -c "import cv2; print('OpenCV: OK')"  # Verify

# Solution 2: Use Python 3.11 or 3.12 (more stable, recommended)
rm -rf venv
python3.11 -m venv venv  # or python3.12
source venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

**Note**: Python 3.13 is very new and some packages may not have pre-built wheels yet. Using Python 3.11 or 3.12 is recommended for better compatibility.

### Face recognition issues

1. **Install system dependencies:**
   ```bash
   # macOS
   brew install cmake
   
   # Ubuntu/Debian
   sudo apt-get install cmake libopenblas-dev liblapack-dev
   ```

2. **Reinstall face_recognition:**
   ```bash
   pip uninstall face_recognition dlib
   pip install dlib
   pip install face_recognition
   ```

## Quick Test Script

Save this as `test_api.sh` in the backend directory:

```bash
#!/bin/bash

BASE_URL="http://localhost:5000"

echo "1. Testing health endpoint..."
curl -s $BASE_URL/api/health | jq .

echo -e "\n2. Registering test user..."
REGISTER_RESPONSE=$(curl -s -X POST $BASE_URL/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password": "Test123!"
  }')
echo $REGISTER_RESPONSE | jq .

echo -e "\n3. Logging in..."
LOGIN_RESPONSE=$(curl -s -X POST $BASE_URL/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test123!"
  }')
TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.access_token')
echo "Token: ${TOKEN:0:50}..."

echo -e "\n4. Testing protected endpoint..."
curl -s -X GET $BASE_URL/api/auth/me \
  -H "Authorization: Bearer $TOKEN" | jq .

echo -e "\n✅ All tests passed!"
```

Make it executable and run:
```bash
chmod +x test_api.sh
./test_api.sh
```

## Next Steps

Once validated locally:

1. Set up frontend React application
2. Implement WebSocket for real-time updates
3. Add unit and integration tests
4. Set up CI/CD pipeline
5. Deploy to production environment

## Additional Resources

- Backend API documentation: See `backend/SETUP.md`
- Project structure: See `PROJECT_STRUCTURE.md`
- Module explanations: See `backend/MODULE_EXPLANATION.md`

