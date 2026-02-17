"""
Alert repository for data access operations.
Abstracts database queries for Alert model.
"""
from typing import Optional, List
from datetime import datetime
from app.models.alert import Alert
from app.utils.database import db


class AlertRepository:
    """Repository for Alert entity operations."""
    
    @staticmethod
    def create(camera_id: int, alert_type: str, message: str, severity: str = 'medium', 
               metadata: str = None) -> Alert:
        """
        Create a new alert.
        
        Args:
            camera_id: Associated camera ID
            alert_type: Type of alert
            message: Alert message
            severity: Alert severity
            metadata: Optional JSON metadata
            
        Returns:
            Created Alert object
        """
        alert = Alert(
            camera_id=camera_id,
            alert_type=alert_type,
            message=message,
            severity=severity,
            meta_data=metadata
        )
        db.session.add(alert)
        db.session.commit()
        return alert
    
    @staticmethod
    def find_by_id(alert_id: int) -> Optional[Alert]:
        """Find alert by ID."""
        return Alert.query.get(alert_id)
    
    @staticmethod
    def find_by_camera_id(camera_id: int, limit: int = None, offset: int = 0) -> List[Alert]:
        """Find alerts for a specific camera."""
        query = Alert.query.filter_by(camera_id=camera_id).order_by(Alert.created_at.desc())
        if limit:
            query = query.limit(limit).offset(offset)
        return query.all()
    
    @staticmethod
    def find_by_status(status: str, limit: int = None, offset: int = 0) -> List[Alert]:
        """Find alerts by status."""
        query = Alert.query.filter_by(status=status).order_by(Alert.created_at.desc())
        if limit:
            query = query.limit(limit).offset(offset)
        return query.all()
    
    @staticmethod
    def find_by_severity(severity: str, limit: int = None, offset: int = 0) -> List[Alert]:
        """Find alerts by severity."""
        query = Alert.query.filter_by(severity=severity).order_by(Alert.created_at.desc())
        if limit:
            query = query.limit(limit).offset(offset)
        return query.all()
    
    @staticmethod
    def find_recent(limit: int = 100, offset: int = 0) -> List[Alert]:
        """Find recent alerts."""
        query = Alert.query.order_by(Alert.created_at.desc())
        if limit:
            query = query.limit(limit).offset(offset)
        return query.all()
    
    @staticmethod
    def find_by_date_range(start_date: datetime, end_date: datetime, 
                          limit: int = None, offset: int = 0) -> List[Alert]:
        """Find alerts within a date range."""
        query = Alert.query.filter(
            Alert.created_at >= start_date,
            Alert.created_at <= end_date
        ).order_by(Alert.created_at.desc())
        if limit:
            query = query.limit(limit).offset(offset)
        return query.all()
    
    @staticmethod
    def update(alert: Alert) -> Alert:
        """Update alert in database."""
        db.session.commit()
        return alert
    
    @staticmethod
    def resolve(alert_id: int) -> Optional[Alert]:
        """Mark alert as resolved."""
        alert = AlertRepository.find_by_id(alert_id)
        if alert:
            alert.status = 'resolved'
            alert.resolved_at = datetime.utcnow()
            db.session.commit()
        return alert
    
    @staticmethod
    def delete(alert_id: int) -> bool:
        """Delete alert by ID."""
        alert = AlertRepository.find_by_id(alert_id)
        if alert:
            db.session.delete(alert)
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def count_pending() -> int:
        """Count pending alerts."""
        return Alert.query.filter_by(status='pending').count()

