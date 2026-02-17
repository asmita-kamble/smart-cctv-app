"""
AllowedPerson model for storing images of allowed persons for cameras.
"""
from datetime import datetime
from app.utils.database import db


class AllowedPerson(db.Model):
    """
    AllowedPerson entity representing allowed person images for cameras.
    
    Attributes:
        id: Primary key
        camera_id: Associated camera ID
        image_path: Path to the stored image file
        name: Optional name/identifier for the person
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """
    __tablename__ = 'allowed_persons'
    
    id = db.Column(db.Integer, primary_key=True)
    camera_id = db.Column(db.Integer, db.ForeignKey('cameras.id'), nullable=False)
    image_path = db.Column(db.String(500), nullable=False)  # Path to stored image
    name = db.Column(db.String(100), nullable=True)  # Optional name/identifier
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    camera = db.relationship('Camera', backref='allowed_persons', lazy=True)
    
    def to_dict(self):
        """Convert allowed person to dictionary."""
        return {
            'id': self.id,
            'camera_id': self.camera_id,
            'image_path': self.image_path,
            'name': self.name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<AllowedPerson {self.name or "Unknown"} for Camera {self.camera_id}>'

