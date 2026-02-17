# Backend Setup Guide

## Prerequisites

- Python 3.9 or higher
- PostgreSQL 12+ (for relational data)
- MongoDB 4.4+ (for metadata and logs)
- pip (Python package manager)

## Installation Steps

### 1. Create Virtual Environment

```bash
cd backend
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

**Note**: If you encounter issues installing `face_recognition`, you may need to install `dlib` first:
```bash
# On macOS (with Homebrew):
brew install cmake
pip install dlib
pip install face_recognition

# On Ubuntu/Debian:
sudo apt-get install cmake
pip install dlib
pip install face_recognition
```

### 3. Database Setup

#### PostgreSQL Setup

1. Create PostgreSQL database:
```sql
CREATE DATABASE smart_cctv;
```

2. Update `.env` file with your PostgreSQL credentials:
```env
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=smart_cctv
POSTGRES_USER=your_username
POSTGRES_PASSWORD=your_password
```

#### MongoDB Setup

1. Start MongoDB service:
```bash
# On macOS (with Homebrew):
brew services start mongodb-community

# On Linux:
sudo systemctl start mongod

# On Windows:
# Start MongoDB service from Services
```

2. MongoDB connection is configured via environment variables (defaults to localhost:27017)

### 4. Environment Configuration

1. Copy environment template:
```bash
cp .env.example .env
```

2. Edit `.env` file with your configuration:
```env
# Flask Configuration
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here

# PostgreSQL Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=smart_cctv
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# MongoDB Configuration
MONGODB_HOST=localhost
MONGODB_PORT=27017
MONGODB_DB=smart_cctv_metadata
```

### 5. Create Upload Directory

```bash
mkdir -p uploads
```

### 6. Run the Application

```bash
python run.py
```

The server will start on `http://localhost:5000` (or the port specified in your `.env` file)

### 7. Verify Installation

Test the health endpoint:
```bash
curl http://localhost:5001/api/health
```

**Note:** Adjust the port number if your backend is running on a different port.

Expected response:
```json
{
  "status": "healthy",
  "message": "Smart CCTV API is running"
}
```

## Creating Initial Admin User

You can create an admin user via the API:

```bash
curl -X POST http://localhost:5001/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "username": "admin",
    "password": "Admin123!",
    "role": "admin"
  }'
```

**Note:** Replace the port (5001) if your backend is running on a different port.

For more details and alternative methods, see [CREATE_ADMIN.md](../CREATE_ADMIN.md)

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login and get JWT token
- `GET /api/auth/me` - Get current user (requires auth)

### Cameras
- `POST /api/cameras` - Create camera (requires auth)
- `GET /api/cameras` - List cameras (requires auth)
- `GET /api/cameras/<id>` - Get camera details (requires auth)
- `PUT /api/cameras/<id>` - Update camera (requires auth)
- `DELETE /api/cameras/<id>` - Delete camera (requires auth)

### Alerts
- `GET /api/alerts` - List alerts (requires auth)
- `GET /api/alerts/<id>` - Get alert details (requires auth)
- `POST /api/alerts/<id>/resolve` - Resolve alert (requires auth)
- `GET /api/alerts/statistics` - Alert statistics (admin only)

### Activities
- `GET /api/activities` - List activities (requires auth)
- `GET /api/activities/<id>` - Get activity details (requires auth)

### Videos
- `POST /api/videos/upload` - Upload and process video (requires auth)
- `POST /api/videos/process/<camera_id>` - Process existing video (requires auth)

### Dashboard
- `GET /api/dashboard/overview` - Dashboard overview (admin only)
- `GET /api/dashboard/cameras` - All cameras (admin only)

## Testing with Postman/curl

### 1. Register User
```bash
curl -X POST http://localhost:5001/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "testuser",
    "password": "Test123!"
  }'
```

### 2. Login
```bash
curl -X POST http://localhost:5001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "Test123!"
  }'
```

Save the `access_token` from the response.

### 3. Create Camera (with token)
```bash
curl -X POST http://localhost:5001/api/cameras \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "name": "Main Entrance",
    "location": "Building A - Front Door",
    "status": "active"
  }'
```

### 4. Upload Video
```bash
curl -X POST http://localhost:5001/api/videos/upload \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "video=@/path/to/your/video.mp4" \
  -F "camera_id=1"
```

## Troubleshooting

### Database Connection Issues
- Verify PostgreSQL is running: `pg_isready`
- Check database credentials in `.env`
- Ensure database exists: `psql -l | grep smart_cctv`

### MongoDB Connection Issues
- Verify MongoDB is running: `mongosh --eval "db.adminCommand('ping')"`
- Check MongoDB connection string in `.env`

### Import Errors
- Ensure virtual environment is activated
- Reinstall dependencies: `pip install -r requirements.txt --force-reinstall`

### Face Recognition Issues
- Install system dependencies (cmake, dlib)
- On macOS: `brew install cmake`
- On Ubuntu: `sudo apt-get install cmake libopenblas-dev liblapack-dev`

## Development Tips

1. **Database Migrations**: The app auto-creates tables on first run. For production, use Flask-Migrate.

2. **Video Processing**: Large videos are processed synchronously. For production, implement async processing with Celery.

3. **Face Detection**: Current implementation uses basic heuristics. Integrate trained ML models for production.

4. **Logging**: Add logging configuration for production debugging.

5. **Error Handling**: Enhance error messages and validation for better UX.

## Next Steps

1. Set up frontend React application
2. Implement WebSocket for real-time updates
3. Add unit and integration tests
4. Set up CI/CD pipeline
5. Deploy to production environment

