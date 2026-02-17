# Quick Start Guide

## Prerequisites Check

```bash
# Check Python
python3 --version  # Should be 3.9+

# Check PostgreSQL
psql --version  # Should be 12+

# Check MongoDB
mongosh --version  # Should be 4.4+
```

## Quick Setup (5 minutes)

### 1. Start Databases

```bash
# PostgreSQL
brew services start postgresql@14  # macOS
# OR
sudo systemctl start postgresql   # Linux

# MongoDB
brew services start mongodb-community  # macOS
# OR
sudo systemctl start mongod            # Linux
```

### 2. Create PostgreSQL Database

```bash
psql -U postgres -c "CREATE DATABASE smart_cctv;"
```

### 3. Setup Backend

```bash
cd backend

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies (fix setuptools issue first)
pip install --upgrade pip setuptools wheel

# Install CMake (required for dlib)
brew install cmake  # macOS only, skip if already installed

# For Python 3.13, install compatible packages
if python --version | grep -q "3.13"; then
    # Python 3.13 - install compatible versions (NumPy < 2.0 for OpenCV compatibility)
    pip install "numpy>=1.26.0,<2.0.0"
    pip install "psycopg[binary]>=3.1.0"  # Use psycopg v3 for Python 3.13
    pip install Flask==3.0.0 Flask-SQLAlchemy==3.1.1 Flask-CORS==4.0.0 Flask-JWT-Extended==4.6.0 Flask-Bcrypt==1.0.1
    pip install pymongo==4.6.1 python-dotenv==1.0.0 marshmallow==3.20.1
    pip install opencv-python==4.8.1.78 Pillow Werkzeug==3.0.1 python-dateutil==2.8.2
    pip install dlib face-recognition==1.3.0
else
    # Python 3.11/3.12 - standard installation
    pip install -r requirements.txt
fi

# OR use the automated script:
# ./install_dependencies.sh

# Create .env file (copy from template below)
cat > .env << EOF
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
JWT_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=smart_cctv
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
MONGODB_HOST=localhost
MONGODB_PORT=27017
MONGODB_DB=smart_cctv_metadata
CORS_ORIGINS=http://localhost:3000
EOF

# Create uploads directory
mkdir -p uploads

# Run the server
python run.py
```

### 4. Validate Setup

In a new terminal:

```bash
cd backend
source venv/bin/activate  # If not already activated

# Run validation script
./validate_setup.sh
```

Or manually test:

```bash
# Health check
curl http://localhost:5000/api/health

# Register user
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","username":"testuser","password":"Test123!"}'

# Login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!"}'
```

## Environment Variables Template

Create `backend/.env` with:

```env
# Flask Configuration
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here
FLASK_ENV=development
PORT=5000

# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=smart_cctv
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# MongoDB
MONGODB_HOST=localhost
MONGODB_PORT=27017
MONGODB_DB=smart_cctv_metadata

# CORS
CORS_ORIGINS=http://localhost:3000
```

## Common Issues

### Backend won't start
- Check databases are running: `pg_isready` and `mongosh --eval "db.adminCommand('ping')"`
- Verify `.env` file exists in `backend/` directory
- Check virtual environment is activated

### Database connection errors
- Verify PostgreSQL credentials in `.env`
- Ensure database `smart_cctv` exists
- Check MongoDB is running

### Import errors
- Activate virtual environment: `source venv/bin/activate`
- Reinstall: `pip install -r requirements.txt --force-reinstall`

## Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will be available at `http://localhost:3000`

## Next Steps

- See `LOCAL_SETUP.md` for detailed setup instructions
- See `backend/SETUP.md` for API documentation
- See `frontend/README.md` for frontend documentation
- Run `./validate_setup.sh` to verify backend works

