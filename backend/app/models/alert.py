"""
Alert model for storing security alerts and notifications.
"""
from datetime import datetime
from app.utils.database import db


class Alert(db.Model):
    """
    Alert entity representing security alerts.
    
    Attributes:
        id: Primary key
        camera_id: Associated camera ID
        alert_type: Type of alert (suspicious_activity, mask_violation, face_spoof, etc.)
        severity: Alert severity (low/medium/high/critical)
        message: Alert description
        status: Alert status (pending/resolved/acknowledged)
        meta_data: Additional alert data (JSON stored as text)
        created_at: Alert creation timestamp
        resolved_at: Resolution timestamp
    """
    __tablename__ = 'alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    camera_id = db.Column(db.Integer, db.ForeignKey('cameras.id'), nullable=False)
    alert_type = db.Column(db.String(50), nullable=False)  # suspicious_activity, mask_violation, face_spoof, etc.
    severity = db.Column(db.String(20), default='medium', nullable=False)  # low/medium/high/critical
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pending', nullable=False)  # pending/resolved/acknowledged
    meta_data = db.Column('metadata', db.Text, nullable=True)  # JSON string for additional data (db column: metadata)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    resolved_at = db.Column(db.DateTime, nullable=True)
    
    def to_dict(self):
        """Convert alert to dictionary."""
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
            'alert_type': self.alert_type,
            'severity': self.severity,
            'message': self.message,
            'status': self.status,
            'metadata': metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None
        }
    
    def __repr__(self):
        return f'<Alert {self.alert_type} - {self.severity}>'

