# Smart CCTV Backend - Module Explanations

This document explains the architecture and purpose of each module in the Smart CCTV backend application.

## Architecture Overview

The application follows a **layered architecture** pattern with clear separation of concerns:

```
Controllers (API Layer)
    ↓
Services (Business Logic Layer)
    ↓
Repositories (Data Access Layer)
    ↓
Models (Database Entities)
```

---

## 1. Models (Entities) - `/app/models/`

Models represent database entities using SQLAlchemy ORM. They define the structure of data stored in PostgreSQL.

### `user.py`
- **Purpose**: User authentication and authorization
- **Key Fields**: email, username, password_hash, role (admin/user), is_active
- **Relationships**: One-to-many with Camera (users can own multiple cameras)
- **Methods**: 
  - `set_password()`: Hashes and stores password
  - `check_password()`: Verifies password
  - `is_admin()`: Checks if user has admin role
  - `to_dict()`: Serializes user to dictionary

### `camera.py`
- **Purpose**: Manages surveillance camera configurations
- **Key Fields**: name, location, ip_address, status, user_id
- **Relationships**: 
  - Many-to-one with User (camera owner)
  - One-to-many with Alert and Activity
- **Status Values**: active, inactive, maintenance

### `alert.py`
- **Purpose**: Stores security alerts and notifications
- **Key Fields**: camera_id, alert_type, severity, message, status, metadata
- **Alert Types**: suspicious_activity, mask_violation, face_spoof, etc.
- **Severity Levels**: low, medium, high, critical
- **Status Values**: pending, resolved, acknowledged

### `activity.py`
- **Purpose**: Logs detected activities and events from video analysis
- **Key Fields**: camera_id, activity_type, description, confidence_score, metadata, timestamp
- **Activity Types**: face_detected, mask_detected, suspicious_behavior, etc.
- **Confidence Score**: 0.0 to 1.0 (detection confidence)

---

## 2. Repositories - `/app/repositories/`

Repositories abstract database operations and provide a clean interface for data access. They handle all CRUD operations and complex queries.

### `user_repository.py`
- **Purpose**: User data access operations
- **Key Methods**:
  - `create()`: Create new user
  - `find_by_id()`, `find_by_email()`, `find_by_username()`: Query users
  - `exists_by_email()`, `exists_by_username()`: Check user existence
  - `update()`, `delete()`: Modify users

### `camera_repository.py`
- **Purpose**: Camera data access operations
- **Key Methods**:
  - `create()`: Create new camera
  - `find_by_id()`, `find_by_user_id()`, `find_by_status()`: Query cameras
  - `count_by_user_id()`: Count user's cameras
  - `update()`, `delete()`: Modify cameras

### `alert_repository.py`
- **Purpose**: Alert data access operations
- **Key Methods**:
  - `create()`: Create new alert
  - `find_by_camera_id()`, `find_by_status()`, `find_by_severity()`: Filter alerts
  - `find_recent()`, `find_by_date_range()`: Time-based queries
  - `resolve()`: Mark alert as resolved
  - `count_pending()`: Count pending alerts

### `activity_repository.py`
- **Purpose**: Activity data access operations
- **Key Methods**:
  - `create()`: Log new activity
  - `find_by_camera_id()`, `find_by_type()`: Filter activities
  - `find_by_camera_and_type()`: Combined filters
  - `find_recent()`, `find_by_date_range()`: Time-based queries
  - `count_by_camera_id()`: Count activities per camera

---

## 3. Services - `/app/services/`

Services contain business logic and orchestrate operations across repositories. They handle complex operations like video processing, AI/ML detection, and alert generation.

### `auth_service.py`
- **Purpose**: Authentication and authorization logic
- **Key Methods**:
  - `register()`: Validate and create new user account
  - `login()`: Authenticate user and generate JWT token
  - `get_user_by_id()`, `verify_token()`: User verification

### `face_detection_service.py`
- **Purpose**: Detect faces and identify spoofed faces (photo/video attacks)
- **Key Methods**:
  - `detect_faces()`: Find faces in video frame using face_recognition library
  - `detect_spoofed_face()`: Analyze face texture to detect spoofing (simplified implementation)
  - `process_frame()`: Complete frame analysis for face detection
- **Note**: Uses OpenCV and face_recognition. For production, integrate advanced anti-spoofing ML models.

### `mask_detection_service.py`
- **Purpose**: Detect mask compliance in video feeds
- **Key Methods**:
  - `detect_mask()`: Analyze lower face region for mask presence
  - `process_frame()`: Analyze entire frame for mask compliance
- **Note**: Uses color analysis heuristics. For production, use trained mask detection models.

### `activity_detection_service.py`
- **Purpose**: Detect suspicious or unusual activities
- **Key Methods**:
  - `detect_motion()`: Background subtraction for motion detection
  - `detect_suspicious_activity()`: Analyze patterns for suspicious behavior
  - `analyze_frame()`: Comprehensive frame analysis
- **Detection Types**: rapid_movement, loitering, crowd_gathering, etc.

### `alert_service.py`
- **Purpose**: Manage security alerts and notifications
- **Key Methods**:
  - `create_alert()`: Generate new security alert
  - `get_alerts_by_camera()`, `get_pending_alerts()`: Query alerts
  - `resolve_alert()`: Mark alert as resolved
  - `get_alert_statistics()`: Dashboard statistics

### `video_processing_service.py`
- **Purpose**: Process uploaded video files for analysis
- **Key Methods**:
  - `save_video()`: Save uploaded video file
  - `extract_frames()`: Extract frames at intervals for processing
  - `process_video()`: Complete video analysis pipeline
- **Pipeline**: Extracts frames → Face detection → Mask detection → Activity detection → Generate alerts

---

## 4. Controllers - `/app/controllers/`

Controllers handle HTTP requests, validate input, call services, and return JSON responses. They define the API endpoints.

### `auth_controller.py`
- **Endpoints**:
  - `POST /api/auth/register`: User registration
  - `POST /api/auth/login`: User login
  - `GET /api/auth/me`: Get current user (protected)

### `camera_controller.py`
- **Endpoints**:
  - `POST /api/cameras`: Create camera (protected)
  - `GET /api/cameras`: List cameras (filtered by user role)
  - `GET /api/cameras/<id>`: Get camera details
  - `PUT /api/cameras/<id>`: Update camera
  - `DELETE /api/cameras/<id>`: Delete camera

### `alert_controller.py`
- **Endpoints**:
  - `GET /api/alerts`: List alerts (with filters)
  - `GET /api/alerts/<id>`: Get alert details
  - `POST /api/alerts/<id>/resolve`: Resolve alert
  - `GET /api/alerts/statistics`: Dashboard statistics (admin only)

### `activity_controller.py`
- **Endpoints**:
  - `GET /api/activities`: List activities (with filters)
  - `GET /api/activities/<id>`: Get activity details

### `dashboard_controller.py`
- **Endpoints**:
  - `GET /api/dashboard/overview`: Dashboard overview (admin only)
  - `GET /api/dashboard/cameras`: All cameras (admin only)

### `video_controller.py`
- **Endpoints**:
  - `POST /api/videos/upload`: Upload and process video
  - `POST /api/videos/process/<camera_id>`: Process existing video

---

## 5. Middleware - `/app/middleware/`

Middleware provides cross-cutting concerns like authentication and authorization.

### `auth_middleware.py`
- **Purpose**: JWT token validation and role-based access control
- **Decorators**:
  - `@require_auth`: Validates JWT token and injects current_user
  - `@require_admin`: Requires admin role (must be used with @require_auth)

---

## 6. Utils - `/app/utils/`

Utility modules provide shared functionality.

### `database.py`
- **Purpose**: SQLAlchemy database instance initialization
- **Exports**: `db` - SQLAlchemy instance

### `mongodb.py`
- **Purpose**: MongoDB connection management
- **Usage**: For storing video metadata, processing logs, and non-relational data
- **Exports**: `mongodb` - MongoDB connection manager

### `validators.py`
- **Purpose**: Input validation utilities
- **Functions**:
  - `validate_email()`: Email format validation
  - `validate_password()`: Password strength validation
  - `validate_video_file()`: Video file extension validation

---

## 7. Configuration - `/app/config.py`

- **Purpose**: Centralized configuration management
- **Features**:
  - Environment variable loading
  - Database connection strings
  - JWT settings
  - File upload settings
  - Video processing parameters
- **Config Classes**: DevelopmentConfig, ProductionConfig, TestingConfig

---

## 8. Application Initialization - `/app/__init__.py`

- **Purpose**: Flask application factory
- **Function**: `create_app(config_name)`
- **Responsibilities**:
  - Initialize Flask app
  - Configure extensions (SQLAlchemy, CORS, JWT)
  - Register routes
  - Create database tables

---

## 9. Entry Point - `/run.py`

- **Purpose**: Application entry point
- **Function**: Starts Flask development server
- **Configuration**: Reads FLASK_ENV from environment

---

## Data Flow Example: Video Processing

1. **Controller** (`video_controller.py`): Receives POST request with video file
2. **Service** (`video_processing_service.py`): 
   - Saves video file
   - Extracts frames
   - Calls detection services
3. **Detection Services**:
   - `face_detection_service.py`: Detects faces and spoofing
   - `mask_detection_service.py`: Checks mask compliance
   - `activity_detection_service.py`: Detects suspicious activities
4. **Alert Service** (`alert_service.py`): Creates alerts for violations
5. **Repository** (`alert_repository.py`): Saves alert to database
6. **Repository** (`activity_repository.py`): Logs activity to database
7. **Controller**: Returns processing results to client

---

## Security Features

- **Password Hashing**: Bcrypt for secure password storage
- **JWT Authentication**: Token-based authentication
- **Role-Based Access Control**: Admin/User role separation
- **Input Validation**: Email, password, and file validation
- **CORS Configuration**: Controlled cross-origin requests

---

## Database Strategy

- **PostgreSQL**: Relational data (Users, Cameras, Alerts, Activities)
- **MongoDB**: Non-relational data (Video metadata, processing logs, large JSON documents)

---

## Future Enhancements

1. **Real-time Processing**: WebSocket support for live CCTV feeds
2. **Advanced ML Models**: Integrate trained models for face spoofing and mask detection
3. **Async Processing**: Background task queue (Celery) for video processing
4. **Notification System**: Email/SMS alerts for critical events
5. **Video Storage**: Cloud storage integration (S3, etc.)
6. **Analytics**: Advanced reporting and analytics dashboard

