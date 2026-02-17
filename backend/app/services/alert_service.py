"""
Alert service for managing security alerts and notifications.
Handles alert creation, escalation, and status management.
"""
from typing import Dict, List, Optional
from datetime import datetime
from app.repositories.alert_repository import AlertRepository
from app.repositories.camera_repository import CameraRepository
import json


class AlertService:
    """Service for alert management and notifications."""
    
    @staticmethod
    def create_alert(camera_id: int, alert_type: str, message: str, 
                    severity: str = 'medium', metadata: Dict = None) -> Dict:
        """
        Create a new security alert.
        
        Args:
            camera_id: Associated camera ID
            alert_type: Type of alert
            message: Alert message
            severity: Alert severity (low/medium/high/critical)
            metadata: Optional additional data
            
        Returns:
            Created alert data
        """
        try:
            print(f"AlertService.create_alert called: camera_id={camera_id}, type={alert_type}, severity={severity}")
            
            # Verify camera exists
            camera = CameraRepository.find_by_id(camera_id)
            if not camera:
                error_msg = f'Camera not found: {camera_id}'
                print(f"ERROR: {error_msg}")
                return {'error': error_msg}, 404
            
            print(f"Camera found: {camera.name} (ID: {camera.id})")
            
            # Convert metadata to JSON string
            metadata_str = json.dumps(metadata) if metadata else None
            
            # Create alert
            alert = AlertRepository.create(
                camera_id=camera_id,
                alert_type=alert_type,
                message=message,
                severity=severity,
                metadata=metadata_str
            )
            
            print(f"Alert created successfully: ID={alert.id}, type={alert.alert_type}")
            return alert.to_dict(), 201
            
        except Exception as e:
            error_msg = f'Failed to create alert: {str(e)}'
            print(f"ERROR creating alert: {error_msg}")
            import traceback
            traceback.print_exc()
            return {'error': error_msg}, 500
    
    @staticmethod
    def get_alert(alert_id: int) -> Dict:
        """Get alert by ID."""
        alert = AlertRepository.find_by_id(alert_id)
        if not alert:
            return {'error': 'Alert not found'}, 404
        return alert.to_dict(), 200
    
    @staticmethod
    def get_alerts_by_camera(camera_id: int, limit: int = 100, offset: int = 0) -> Dict:
        """Get alerts for a specific camera."""
        alerts = AlertRepository.find_by_camera_id(camera_id, limit, offset)
        return {
            'alerts': [alert.to_dict() for alert in alerts],
            'count': len(alerts)
        }, 200
    
    @staticmethod
    def get_pending_alerts(limit: int = 100, offset: int = 0) -> Dict:
        """Get all pending alerts."""
        alerts = AlertRepository.find_by_status('pending', limit, offset)
        return {
            'alerts': [alert.to_dict() for alert in alerts],
            'count': len(alerts)
        }, 200
    
    @staticmethod
    def get_alerts_by_severity(severity: str, limit: int = 100, offset: int = 0) -> Dict:
        """Get alerts by severity level."""
        alerts = AlertRepository.find_by_severity(severity, limit, offset)
        return {
            'alerts': [alert.to_dict() for alert in alerts],
            'count': len(alerts)
        }, 200
    
    @staticmethod
    def resolve_alert(alert_id: int) -> Dict:
        """Mark alert as resolved."""
        alert = AlertRepository.resolve(alert_id)
        if not alert:
            return {'error': 'Alert not found'}, 404
        return alert.to_dict(), 200
    
    @staticmethod
    def get_recent_alerts(limit: int = 100) -> Dict:
        """Get recent alerts."""
        alerts = AlertRepository.find_recent(limit)
        return {
            'alerts': [alert.to_dict() for alert in alerts],
            'count': len(alerts)
        }, 200
    
    @staticmethod
    def get_alert_statistics() -> Dict:
        """Get alert statistics for dashboard."""
        pending_count = AlertRepository.count_pending()
        recent_alerts = AlertRepository.find_recent(10)
        
        # Count by severity
        critical = len(AlertRepository.find_by_severity('critical', limit=1000))
        high = len(AlertRepository.find_by_severity('high', limit=1000))
        medium = len(AlertRepository.find_by_severity('medium', limit=1000))
        low = len(AlertRepository.find_by_severity('low', limit=1000))
        
        return {
            'pending_count': pending_count,
            'recent_alerts': [alert.to_dict() for alert in recent_alerts],
            'severity_counts': {
                'critical': critical,
                'high': high,
                'medium': medium,
                'low': low
            }
        }, 200

