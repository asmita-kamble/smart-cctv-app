"""
Alert service for managing security alerts and notifications.
Handles alert creation, escalation, and status management.
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from app.repositories.alert_repository import AlertRepository
from app.repositories.camera_repository import CameraRepository
from app.services.email_service import EmailService
import json
import hashlib
import re


class AlertService:
    """Service for alert management and notifications."""
    
    # Deduplication time window (seconds) - prevent duplicate alerts within this window
    DEDUP_TIME_WINDOW = 60  # 60 seconds default for video processing (longer to prevent duplicates)
    
    # Per-alert-type deduplication windows (seconds)
    # Longer windows to prevent duplicates during video processing
    # Only deduplicate truly identical alerts (same type, same location, same metadata)
    DEDUP_WINDOWS_BY_TYPE = {
        'weapon_detected': 60,  # 60 seconds - deduplicate same weapon type
        'suspicious_activity': 30,  # 30 seconds - allow different activities to be detected
        'mask_violation': 30,  # 30 seconds - mask violations can persist but allow updates
        'face_spoof': 60,  # 60 seconds - spoofing is serious
        'red_zone_entry': 60,  # 60 seconds - zone violations
        'unknown_object_left_behind': 60,  # 60 seconds - abandoned objects
        'multiple_zone_violations': 300,  # 5 minutes - already has its own cooldown
    }
    
    @staticmethod
    def _generate_alert_signature(camera_id: int, alert_type: str, message: str, metadata: Dict = None) -> str:
        """
        Generate a unique signature for an alert to detect duplicates.
        
        For video processing, we use a simplified signature that focuses on alert_type + message
        to aggressively deduplicate similar alerts across frames.
        
        Args:
            camera_id: Camera ID
            alert_type: Alert type
            message: Alert message
            metadata: Optional metadata
            
        Returns:
            Hash signature string
        """
        # Create a normalized signature from key fields
        # Normalize message: remove frame numbers, timestamps, and other transient info
        message_key = message.lower().strip() if message else ""
        
        # Remove frame numbers and other transient details from message
        # Remove patterns like "at frame 123" or "frame: 456"
        message_key = re.sub(r'\s*(at\s+)?frame\s*\d+', '', message_key, flags=re.IGNORECASE)
        # Remove confidence percentages that might vary slightly
        message_key = re.sub(r'\(confidence:\s*[\d.]+%?\)', '', message_key, flags=re.IGNORECASE)
        # Remove method info
        message_key = re.sub(r'\(method:\s*[^)]+\)', '', message_key, flags=re.IGNORECASE)
        # Take first 100 chars for comparison
        message_key = message_key[:100].strip()
        
        # For video processing, use a VERY simplified signature based on alert_type + message only
        # This aggressively deduplicates the same type of alert regardless of bbox/location/person_id
        # For video processing, we want to deduplicate ALL alerts of the same type with the same message
        if metadata and metadata.get('video_path'):
            # This is a video processing alert - use ultra-simplified signature
            # Base signature: camera_id + alert_type + normalized message
            # NO person_id, bbox, or other metadata - just deduplicate based on type and message
            signature_str = f"{camera_id}|{alert_type}|{message_key}"
            
            # Only add distinguishing info for weapon_type to allow different weapon types
            # But same weapon_type will be deduplicated regardless of bbox/person
            if alert_type == 'weapon_detected':
                weapon_type = metadata.get('weapon_type', 'unknown')
                signature_str += f"|weapon:{str(weapon_type).lower().strip()}"
            
            signature_hash = hashlib.md5(signature_str.encode()).hexdigest()
            return signature_hash
        
        # Include relevant metadata fields for better deduplication
        # Exclude transient fields like frame numbers, timestamps, confidence
        metadata_key = ""
        if metadata:
            # Extract key identifying fields from metadata (exclude frame, timestamps, confidence)
            # Use weapon_type, activity_type, object_type, class_name, detection_method for deduplication
            key_fields = ['weapon_type', 'activity_type', 'object_type', 'class_name', 'detection_method']
            metadata_parts = []
            for field in key_fields:
                if field in metadata:
                    # Normalize the value (lowercase, strip)
                    value = str(metadata[field]).lower().strip()
                    if value and value != 'none' and value != 'unknown':  # Only add non-empty, meaningful values
                        metadata_parts.append(f"{field}:{value}")
            
            # Add bbox position for spatial deduplication
            # Use exact bbox position to distinguish different detections
            # This ensures different objects or same object at different positions create different alerts
            if 'bbox' in metadata and metadata['bbox']:
                bbox = metadata['bbox']
                if isinstance(bbox, list) and len(bbox) >= 4:
                    # Use exact bbox values to create unique signatures for each detection
                    # Round to nearest 10 pixels to allow slight movement but distinguish locations
                    x = int(round(bbox[0] / 10) * 10)
                    y = int(round(bbox[1] / 10) * 10)
                    w = int(round(bbox[2] / 10) * 10) if len(bbox) > 2 else 0
                    h = int(round(bbox[3] / 10) * 10) if len(bbox) > 3 else 0
                    # Include bbox in signature to distinguish spatial locations
                    metadata_parts.append(f"bbox:{x},{y},{w},{h}")
            
            # DO NOT include frame number in signature - we want to deduplicate same detection across frames
            # Frame numbers are stored in metadata for reference but not used for deduplication
            
            # For weapon_detected alerts, include ALL distinguishing factors
            if alert_type == 'weapon_detected':
                # Always include class_name (even if empty) to distinguish detections
                class_name = str(metadata.get('class_name', '')).lower().strip()
                metadata_parts.append(f"class:{class_name if class_name else 'empty'}")
                
                # Include detection method
                method = str(metadata.get('detection_method', '')).lower().strip()
                metadata_parts.append(f"method:{method if method else 'unknown'}")
                
                # Include near_person flag to distinguish
                near_person = metadata.get('near_person', False)
                metadata_parts.append(f"near_person:{near_person}")
                
                # Include aspect_ratio (rounded) to distinguish different shaped objects
                aspect_ratio = metadata.get('aspect_ratio', 0)
                if aspect_ratio:
                    aspect_rounded = round(float(aspect_ratio), 2)
                    metadata_parts.append(f"aspect:{aspect_rounded}")
            
            # For suspicious_activity alerts, include activity_type
            if alert_type == 'suspicious_activity':
                activity_type = str(metadata.get('activity_type', '')).lower().strip()
                metadata_parts.append(f"activity:{activity_type if activity_type else 'unknown'}")
                
                # Include motion_percentage (rounded) to distinguish different motion levels
                motion_pct = metadata.get('motion_percentage', 0)
                if motion_pct:
                    motion_rounded = round(float(motion_pct), 1)
                    metadata_parts.append(f"motion:{motion_rounded}")
            
            # For red_zone_entry alerts, include person_id, bbox, and location to distinguish different persons
            if alert_type == 'red_zone_entry':
                person_id = metadata.get('person_id')
                if person_id is not None:
                    metadata_parts.append(f"person_id:{person_id}")
                
                # Include bbox for precise spatial distinction (more accurate than location center)
                if 'bbox' in metadata and metadata['bbox']:
                    bbox = metadata['bbox']
                    if isinstance(bbox, list) and len(bbox) >= 4:
                        # Use exact bbox values rounded to 5px for precise distinction
                        x = int(round(bbox[0] / 5) * 5)
                        y = int(round(bbox[1] / 5) * 5)
                        w = int(round(bbox[2] / 5) * 5) if len(bbox) > 2 else 0
                        h = int(round(bbox[3] / 5) * 5) if len(bbox) > 3 else 0
                        metadata_parts.append(f"bbox:{x},{y},{w},{h}")
                
                # Include location (center point) as fallback if bbox not available
                location = metadata.get('location')
                if location and isinstance(location, (list, tuple)) and len(location) >= 2:
                    # Round to nearest 10 pixels for precise distinction
                    x = int(round(location[0] / 10) * 10)
                    y = int(round(location[1] / 10) * 10)
                    metadata_parts.append(f"loc:{x},{y}")
                
                # Include zone_name if available
                zone_name = metadata.get('zone_name')
                if zone_name:
                    metadata_parts.append(f"zone:{str(zone_name).lower().strip()}")
            
            # Include location for any alert type that has it (for spatial distinction)
            if 'location' in metadata and metadata['location'] and alert_type != 'red_zone_entry':
                location = metadata['location']
                if isinstance(location, (list, tuple)) and len(location) >= 2:
                    x = int(round(location[0] / 20) * 20)
                    y = int(round(location[1] / 20) * 20)
                    metadata_parts.append(f"loc:{x},{y}")
            
            metadata_key = "|".join(sorted(metadata_parts))
        
        # Include camera_id, alert_type, normalized message, and metadata
        # This ensures different alert types, messages, and metadata create different signatures
        signature_str = f"{camera_id}|{alert_type}|{message_key}|{metadata_key}"
        signature_hash = hashlib.md5(signature_str.encode()).hexdigest()
        
        # Debug logging for signature generation
        if not metadata_key:
            print(f"Warning: Empty metadata_key for alert_type={alert_type}, message={message_key[:50]}")
        
        return signature_hash
    
    @staticmethod
    def _check_duplicate_alert(camera_id: int, alert_type: str, message: str, 
                               metadata: Dict = None, time_window: int = None) -> Optional[Dict]:
        """
        Check if a similar alert was created recently.
        
        Args:
            camera_id: Camera ID
            alert_type: Alert type
            message: Alert message
            metadata: Optional metadata
            time_window: Time window in seconds (default: DEDUP_TIME_WINDOW or type-specific)
            
        Returns:
            Existing alert dict if duplicate found, None otherwise
        """
        if time_window is None:
            # Use type-specific window if available, otherwise default
            time_window = AlertService.DEDUP_WINDOWS_BY_TYPE.get(
                alert_type, 
                AlertService.DEDUP_TIME_WINDOW
            )
        
        # Get recent alerts for this camera and alert type
        cutoff_time = datetime.utcnow() - timedelta(seconds=time_window)
        
        # Query recent alerts by camera and alert type (more efficient)
        candidate_alerts = AlertRepository.find_recent_by_camera_and_type(
            camera_id=camera_id,
            alert_type=alert_type,
            start_date=cutoff_time,
            limit=50
        )
        
        if not candidate_alerts:
            return None
        
        # Generate signature for new alert
        new_signature = AlertService._generate_alert_signature(camera_id, alert_type, message, metadata)
        
        # Check if any existing alert has the same signature
        for alert in candidate_alerts:
            # Parse metadata from existing alert
            existing_metadata = {}
            if alert.meta_data:
                try:
                    existing_metadata = json.loads(alert.meta_data)
                except:
                    pass
            
            existing_signature = AlertService._generate_alert_signature(
                alert.camera_id, alert.alert_type, alert.message, existing_metadata
            )
            
            if existing_signature == new_signature:
                time_diff = (datetime.utcnow() - alert.created_at).total_seconds()
                print(f"DUPLICATE DETECTED: Alert type={alert.alert_type}, existing_id={alert.id}, time_diff={time_diff:.1f}s")
                print(f"  New signature: {new_signature[:16]}...")
                print(f"  Existing signature: {existing_signature[:16]}...")
                print(f"  New metadata keys: {list(metadata.keys()) if metadata else 'none'}")
                print(f"  Existing metadata keys: {list(existing_metadata.keys()) if existing_metadata else 'none'}")
                return alert.to_dict()
            else:
                # Debug: show why signatures don't match
                if metadata and metadata.get('video_path'):
                    print(f"SIGNATURE MISMATCH: new={new_signature[:16]}... vs existing={existing_signature[:16]}...")
        
        return None
    
    @staticmethod
    def create_alert(camera_id: int, alert_type: str, message: str, 
                    severity: str = 'medium', metadata: Dict = None, 
                    deduplicate: bool = True, dedup_time_window: int = None) -> Dict:
        """
        Create a new security alert.
        
        Args:
            camera_id: Associated camera ID
            alert_type: Type of alert
            message: Alert message
            severity: Alert severity (low/medium/high/critical)
            metadata: Optional additional data
            deduplicate: Whether to check for duplicates (default: True)
            dedup_time_window: Time window in seconds for deduplication (default: DEDUP_TIME_WINDOW)
            
        Returns:
            Created alert data or existing alert if duplicate found
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
            
            # Check for duplicate alerts
            existing_alert = None
            if deduplicate:
                existing_alert = AlertService._check_duplicate_alert(
                    camera_id, alert_type, message, metadata, dedup_time_window
                )
                if existing_alert:
                    print(f"DUPLICATE PREVENTED: Alert type={alert_type}, camera_id={camera_id}, existing_alert_id={existing_alert.get('id')}, message={message[:50]}")
                elif metadata and metadata.get('video_path'):
                    # Debug: show why it's not a duplicate for video processing
                    signature = AlertService._generate_alert_signature(camera_id, alert_type, message, metadata)
                    print(f"NEW VIDEO ALERT: type={alert_type}, signature={signature[:16]}..., message={message[:50]}")
                if existing_alert:
                    print(f"DUPLICATE PREVENTED: Alert type={alert_type}, camera_id={camera_id}, existing_alert_id={existing_alert.get('id')}")
            
            if existing_alert:
                signature = AlertService._generate_alert_signature(camera_id, alert_type, message, metadata)
                # Debug: Show what fields are being used for signature
                metadata_debug = {}
                if metadata:
                    for field in ['weapon_type', 'activity_type', 'class_name', 'detection_method', 'bbox']:
                        if field in metadata:
                            metadata_debug[field] = metadata[field]
                print(f"Duplicate alert prevented (signature: {signature[:16]}...). "
                      f"Type: {alert_type}, Metadata: {metadata_debug}. "
                      f"Returning existing alert ID: {existing_alert.get('id')}")
                # Return existing alert but don't count it as a new creation
                return existing_alert, 200  # Return existing alert with 200 status
            
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
            
            signature = AlertService._generate_alert_signature(camera_id, alert_type, message, metadata)
            print(f"Alert created successfully: ID={alert.id}, type={alert.alert_type}, signature: {signature[:16]}...")
            
            # Send email notification for medium, high, or critical alerts
            if severity.lower() in ['medium', 'high', 'critical']:
                try:
                    email_result, email_status = EmailService.send_alert_notification(
                        alert_type=alert_type,
                        message=message,
                        severity=severity,
                        camera_name=camera.name
                    )
                    if email_status == 200:
                        print(f"Email notification sent successfully for alert {alert.id}")
                    else:
                        print(f"Failed to send email notification: {email_result.get('error', 'Unknown error')}")
                except Exception as e:
                    # Don't fail alert creation if email fails
                    print(f"Error sending email notification: {str(e)}")
            
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

