"""Controller modules for API endpoints."""
from app.controllers.auth_controller import auth_bp
from app.controllers.camera_controller import camera_bp
from app.controllers.allowed_person_controller import allowed_person_bp
from app.controllers.alert_controller import alert_bp
from app.controllers.activity_controller import activity_bp
from app.controllers.dashboard_controller import dashboard_bp
from app.controllers.video_controller import video_bp

__all__ = ['auth_bp', 'camera_bp', 'allowed_person_bp', 'alert_bp', 'activity_bp', 'dashboard_bp', 'video_bp']

