"""
Activity model for logging detected activities and events.
"""
from datetime import datetime
from app.utils.database import db


class Activity(db.Model):
    """
    Activity entity representing detected events and activities.
    
    Attributes:
        id: Primary key
        camera_id: Associated camera ID
        activity_type: Type of activity (face_detected, mask_detected, suspicious_behavior, etc.)
        description: Activity description
        confidence_score: Detection confidence (0.0 to 1.0)
        meta_data: Additional activity data (JSON stored as text)
        timestamp: When the activity occurred
        created_at: Record creation timestamp
    """
    __tablename__ = 'activities'
    
    id = db.Column(db.Integer, primary_key=True)
    camera_id = db.Column(db.Integer, db.ForeignKey('cameras.id'), nullable=False)
    activity_type = db.Column(db.String(50), nullable=False)  # face_detected, mask_detected, suspicious_behavior, etc.
    description = db.Column(db.Text, nullable=False)
    confidence_score = db.Column(db.Float, nullable=True)  # 0.0 to 1.0
    meta_data = db.Column('metadata', db.Text, nullable=True)  # JSON string for additional data (db column: metadata)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        """Convert activity to dictionary."""
        import json
        metadata = None
        if self.meta_data:
            try:
                metadata = json.loads(self.meta_data)
            except (json.JSONDecodeError, TypeError):
                metadata = self.meta_data
        
        return {
            'id': self.id,
            'camera_id': self.camera_id,
            'camera_name': self.camera.name if self.camera else None,
            'activity_type': self.activity_type,
            'description': self.description,
            'confidence_score': self.confidence_score,
            'metadata': metadata,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<Activity {self.activity_type} at {self.timestamp}>'

