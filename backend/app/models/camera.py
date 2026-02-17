"""
Camera model for managing surveillance cameras and locations.
"""
from datetime import datetime
from app.utils.database import db


class Camera(db.Model):
    """
    Camera entity representing surveillance cameras.
    
    Attributes:
        id: Primary key
        name: Camera name/identifier
        location: Physical location description
        ip_address: Camera IP address (if network camera)
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
    is_restricted_zone = db.Column(db.Boolean, default=False, nullable=False)  # ON/OFF toggle for restricted zone
    status = db.Column(db.String(20), default='active', nullable=False)  # active/inactive/maintenance
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    alerts = db.relationship('Alert', backref='camera', lazy=True, cascade='all, delete-orphan')
    activities = db.relationship('Activity', backref='camera', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        """Convert camera to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'location': self.location,
            'ip_address': self.ip_address,
            'is_restricted_zone': self.is_restricted_zone,
            'status': self.status,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Camera {self.name} at {self.location}>'

