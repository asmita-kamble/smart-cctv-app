# Smart CCTV - Complete Project Structure

## Backend Structure

```
backend/
├── app/
│   ├── __init__.py                    # Flask app factory
│   ├── config.py                      # Configuration management
│   ├── routes.py                      # Route registration
│   │
│   ├── models/                        # Database Models (Entities)
│   │   ├── __init__.py
│   │   ├── user.py                    # User entity (Admin/User roles)
│   │   ├── camera.py                  # Camera entity
│   │   ├── alert.py                   # Alert entity
│   │   └── activity.py                # Activity entity
│   │
│   ├── repositories/                  # Data Access Layer
│   │   ├── __init__.py
│   │   ├── user_repository.py        # User data operations
│   │   ├── camera_repository.py      # Camera data operations
│   │   ├── alert_repository.py       # Alert data operations
│   │   └── activity_repository.py    # Activity data operations
│   │
│   ├── services/                      # Business Logic Layer
│   │   ├── __init__.py
│   │   ├── auth_service.py           # Authentication & authorization
│   │   ├── face_detection_service.py # Face detection & spoofing
│   │   ├── mask_detection_service.py # Mask compliance detection
│   │   ├── activity_detection_service.py # Suspicious activity detection
│   │   ├── alert_service.py          # Alert management
│   │   └── video_processing_service.py # Video processing pipeline
│   │
│   ├── controllers/                   # API Endpoints (Route Handlers)
│   │   ├── __init__.py
│   │   ├── auth_controller.py        # /api/auth/*
│   │   ├── camera_controller.py      # /api/cameras/*
│   │   ├── alert_controller.py       # /api/alerts/*
│   │   ├── activity_controller.py    # /api/activities/*
│   │   ├── dashboard_controller.py   # /api/dashboard/*
│   │   └── video_controller.py       # /api/videos/*
│   │
│   ├── middleware/                    # Custom Middleware
│   │   ├── __init__.py
│   │   └── auth_middleware.py        # JWT auth & RBAC decorators
│   │
│   └── utils/                         # Utility Functions
│       ├── __init__.py
│       ├── database.py                # PostgreSQL connection
│       ├── mongodb.py                # MongoDB connection
│       └── validators.py             # Input validation
│
├── tests/                             # Test Suite
│   └── __init__.py
│
├── requirements.txt                   # Python dependencies
├── .gitignore                        # Git ignore rules
├── run.py                            # Application entry point
├── SETUP.md                          # Setup instructions
└── MODULE_EXPLANATION.md             # Detailed module docs
```

## Frontend Structure (To be created)

```
frontend/
├── src/
│   ├── components/                   # React components
│   │   ├── common/                  # Reusable components
│   │   ├── auth/                    # Auth components
│   │   ├── camera/                  # Camera management
│   │   ├── dashboard/               # Dashboard components
│   │   └── alerts/                  # Alert components
│   │
│   ├── pages/                       # Page components
│   │   ├── Login.jsx
│   │   ├── Register.jsx
│   │   ├── Dashboard.jsx
│   │   ├── Cameras.jsx
│   │   └── Alerts.jsx
│   │
│   ├── services/                    # API services
│   │   ├── api.js                  # API client
│   │   ├── auth.js                 # Auth API
│   │   └── camera.js               # Camera API
│   │
│   ├── utils/                       # Utilities
│   │   ├── auth.js                 # Auth helpers
│   │   └── constants.js            # Constants
│   │
│   ├── App.jsx                      # Main app component
│   └── index.js                    # Entry point
│
├── package.json
├── tailwind.config.js
└── README.md
```

## Key Files Summary

### Backend Core Files

1. **`app/__init__.py`**: Flask application factory, initializes all extensions
2. **`app/config.py`**: Centralized configuration from environment variables
3. **`run.py`**: Application entry point, starts Flask server
4. **`app/routes.py`**: Registers all API blueprints

### Models (4 entities)
- **User**: Authentication, roles (admin/user)
- **Camera**: Surveillance camera configurations
- **Alert**: Security alerts and notifications
- **Activity**: Detected events and activities

### Repositories (4 repositories)
- Abstract database operations
- Provide clean interface for data access
- Handle CRUD and complex queries

### Services (6 services)
- **AuthService**: User registration, login, JWT tokens
- **FaceDetectionService**: Face detection and spoofing detection
- **MaskDetectionService**: Mask compliance tracking
- **ActivityDetectionService**: Suspicious activity detection
- **AlertService**: Alert creation and management
- **VideoProcessingService**: Video upload and processing pipeline

### Controllers (6 controllers)
- Handle HTTP requests
- Validate input
- Call services
- Return JSON responses
- Protected with authentication middleware

### Middleware
- **auth_middleware.py**: JWT validation and role-based access control

### Utils
- **database.py**: PostgreSQL connection
- **mongodb.py**: MongoDB connection
- **validators.py**: Input validation helpers

## API Endpoints Summary

### Authentication (`/api/auth`)
- `POST /register` - User registration
- `POST /login` - User login
- `GET /me` - Current user info

### Cameras (`/api/cameras`)
- `POST /` - Create camera
- `GET /` - List cameras
- `GET /<id>` - Get camera
- `PUT /<id>` - Update camera
- `DELETE /<id>` - Delete camera

### Alerts (`/api/alerts`)
- `GET /` - List alerts
- `GET /<id>` - Get alert
- `POST /<id>/resolve` - Resolve alert
- `GET /statistics` - Alert stats (admin)

### Activities (`/api/activities`)
- `GET /` - List activities
- `GET /<id>` - Get activity

### Videos (`/api/videos`)
- `POST /upload` - Upload and process video
- `POST /process/<camera_id>` - Process video

### Dashboard (`/api/dashboard`)
- `GET /overview` - Dashboard overview (admin)
- `GET /cameras` - All cameras (admin)

## Database Schema

### PostgreSQL Tables
- **users**: id, email, username, password_hash, role, is_active, timestamps
- **cameras**: id, name, location, ip_address, status, user_id, timestamps
- **alerts**: id, camera_id, alert_type, severity, message, status, metadata, timestamps
- **activities**: id, camera_id, activity_type, description, confidence_score, metadata, timestamps

### MongoDB Collections
- Video metadata
- Processing logs
- Large JSON documents

## Security Features

- ✅ Password hashing (Bcrypt)
- ✅ JWT authentication
- ✅ Role-based access control (Admin/User)
- ✅ Input validation
- ✅ CORS configuration
- ✅ Protected routes with middleware

## Next Steps

1. ✅ Backend structure complete
2. ⏳ Frontend React application
3. ⏳ Real-time WebSocket support
4. ⏳ Unit and integration tests
5. ⏳ Production deployment configuration

