"""
Camera model for managing surveillance cameras and locations.
"""
from datetime import datetime
from app.utils.database import db
import json


class Camera(db.Model):
    """
    Camera entity representing surveillance cameras.
    
    Attributes:
        id: Primary key
        name: Camera name/identifier
        location: Physical location description
        ip_address: Camera IP address (if network camera)
        rtsp_username: RTSP authentication username (optional)
        rtsp_password: RTSP authentication password (optional)
        rtsp_path: RTSP stream path (optional, defaults to /stream1)
        is_restricted_zone: Boolean flag indicating if this is a restricted zone (ON/OFF)
        status: Camera status (active/inactive/maintenance)
        user_id: Owner/creator user ID
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """
    __tablename__ = 'cameras'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(255), nullable=False)
    ip_address = db.Column(db.String(45), nullable=True)  # IPv6 compatible
    rtsp_username = db.Column(db.String(100), nullable=True)  # RTSP authentication username
    rtsp_password = db.Column(db.String(255), nullable=True)  # RTSP authentication password
    rtsp_path = db.Column(db.String(255), nullable=True)  # RTSP stream path (e.g., /stream1, /Streaming/Channels/1)
    is_restricted_zone = db.Column(db.Boolean, default=False, nullable=False)  # ON/OFF toggle for restricted zone
    status = db.Column(db.String(20), default='active', nullable=False)  # active/inactive/maintenance
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Camera Calibration Fields
    pixels_per_meter = db.Column(db.Float, nullable=True)  # Pixels per meter for distance/speed calculation
    camera_height = db.Column(db.Float, nullable=True)  # Camera height in meters
    camera_angle = db.Column(db.Float, nullable=True)  # Camera angle in degrees (0 = horizontal, 90 = vertical down)
    reference_object_height = db.Column(db.Float, nullable=True)  # Reference object height in meters (e.g., average person height)
    
    # Zone Configuration (stored as JSON)
    red_zones = db.Column(db.Text, nullable=True)  # JSON array of red zone definitions
    yellow_zones = db.Column(db.Text, nullable=True)  # JSON array of yellow zone definitions
    sensitive_areas = db.Column(db.Text, nullable=True)  # JSON array of sensitive area definitions
    perimeter_lines = db.Column(db.Text, nullable=True)  # JSON array of perimeter line definitions
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    alerts = db.relationship('Alert', backref='camera', lazy=True, cascade='all, delete-orphan')
    activities = db.relationship('Activity', backref='camera', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self, include_password=False):
        """
        Convert camera to dictionary.
        
        Args:
            include_password: If True, include RTSP password (default: False for security)
        """
        result = {
            'id': self.id,
            'name': self.name,
            'location': self.location,
            'ip_address': self.ip_address,
            'rtsp_username': self.rtsp_username,
            'rtsp_path': self.rtsp_path,
            'is_restricted_zone': self.is_restricted_zone,
            'status': self.status,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            # Calibration fields
            'pixels_per_meter': self.pixels_per_meter,
            'camera_height': self.camera_height,
            'camera_angle': self.camera_angle,
            'reference_object_height': self.reference_object_height,
            # Zone configurations (parse JSON)
            'red_zones': self._parse_json_field(self.red_zones),
            'yellow_zones': self._parse_json_field(self.yellow_zones),
            'sensitive_areas': self._parse_json_field(self.sensitive_areas),
            'perimeter_lines': self._parse_json_field(self.perimeter_lines)
        }
        # Only include password if explicitly requested (for internal use)
        if include_password:
            result['rtsp_password'] = self.rtsp_password
        return result
    
    def _parse_json_field(self, field_value):
        """Parse JSON field safely."""
        if not field_value:
            return []
        try:
            return json.loads(field_value)
        except (json.JSONDecodeError, TypeError):
            return []
    
    def __repr__(self):
        return f'<Camera {self.name} at {self.location}>'

