# Smart CCTV - Full Stack Application

A comprehensive smart surveillance system with real-time face detection, mask compliance tracking, and suspicious activity monitoring.

## Project Structure

```
smart-cctv/
├── backend/                 # Flask API Backend
│   ├── app/
│   │   ├── __init__.py     # Flask app initialization
│   │   ├── config.py       # Configuration management
│   │   ├── models/         # Database models (SQLAlchemy for PostgreSQL)
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── camera.py
│   │   │   ├── alert.py
│   │   │   └── activity.py
│   │   ├── repositories/   # Data access layer
│   │   │   ├── __init__.py
│   │   │   ├── user_repository.py
│   │   │   ├── camera_repository.py
│   │   │   ├── alert_repository.py
│   │   │   └── activity_repository.py
│   │   ├── services/       # Business logic layer
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py
│   │   │   ├── face_detection_service.py
│   │   │   ├── mask_detection_service.py
│   │   │   ├── activity_detection_service.py
│   │   │   ├── alert_service.py
│   │   │   └── video_processing_service.py
│   │   ├── controllers/    # API route handlers
│   │   │   ├── __init__.py
│   │   │   ├── auth_controller.py
│   │   │   ├── camera_controller.py
│   │   │   ├── alert_controller.py
│   │   │   ├── activity_controller.py
│   │   │   ├── dashboard_controller.py
│   │   │   └── video_controller.py
│   │   ├── middleware/     # Custom middleware
│   │   │   ├── __init__.py
│   │   │   └── auth_middleware.py
│   │   ├── utils/          # Utility functions
│   │   │   ├── __init__.py
│   │   │   ├── database.py
│   │   │   ├── mongodb.py
│   │   │   └── validators.py
│   │   └── routes.py       # Route registration
│   ├── tests/              # Unit and integration tests
│   ├── requirements.txt    # Python dependencies
│   ├── .env.example        # Environment variables template
│   └── run.py             # Application entry point
│
├── frontend/               # React + Tailwind Frontend
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   └── utils/
│   ├── package.json
│   └── tailwind.config.js
│
└── docs/                   # Documentation
```

## Technology Stack

- **Backend**: Python 3.9+, Flask, SQLAlchemy
- **Databases**: PostgreSQL (relational data), MongoDB (video metadata, logs)
- **Frontend**: React, Tailwind CSS
- **AI/ML**: OpenCV, face_recognition, TensorFlow/PyTorch (for face spoofing detection)

## Getting Started

### Quick Start with Docker (Recommended)

The easiest way to run the application is using Docker:

```bash
# Quick start script (automatically sets up environment)
./docker-start.sh

# Or manually:
cp env.docker.example .env
# Edit .env with your configuration
docker-compose up -d
```

Access the application:
- Frontend: http://localhost:3000
- Backend API: http://localhost:5001

For detailed Docker setup instructions, see [DOCKER_SETUP.md](DOCKER_SETUP.md)

### Manual Setup

### Backend Setup

1. Create virtual environment:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your database credentials
```

4. Run database migrations and start server:
```bash
python run.py
```

### Frontend Setup

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Start development server:
```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

For more details, see [frontend/README.md](frontend/README.md)

## Module Explanations

### Models (Entities)
- **User**: Stores user authentication data and roles (Admin/User)
- **Camera**: Manages camera locations and configurations
- **Alert**: Stores alert records for suspicious activities
- **Activity**: Logs detected activities and events

### Repositories
Data access layer that abstracts database operations. Each repository handles CRUD operations for its corresponding model.

### Services
Business logic layer containing:
- **Auth Service**: Handles authentication, authorization, JWT tokens
- **Face Detection Service**: Detects and verifies faces (real vs spoofed)
- **Mask Detection Service**: Identifies mask compliance
- **Activity Detection Service**: Analyzes suspicious activities
- **Alert Service**: Manages alert generation and notifications
- **Video Processing Service**: Processes video feeds for analysis

### Controllers
API endpoint handlers that receive HTTP requests, validate input, call services, and return responses.
- **Auth Controller**: User registration and login endpoints
- **Camera Controller**: Camera management (CRUD operations)
- **Alert Controller**: Alert retrieval and resolution
- **Activity Controller**: Activity log queries
- **Dashboard Controller**: Admin dashboard statistics
- **Video Controller**: Video upload and processing

### Middleware
- **Auth Middleware**: Validates JWT tokens and enforces role-based access control

## Detailed Documentation

For comprehensive module explanations, see [backend/MODULE_EXPLANATION.md](backend/MODULE_EXPLANATION.md)

