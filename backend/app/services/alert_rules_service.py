"""
Alert Rules Service for implementing comprehensive security detection rules.
Handles object-based detection, zone-based intrusion, and behavioral pattern analysis.
"""
import cv2
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import json


class AlertRulesService:
    """
    Service for implementing security alert rules based on detection patterns.
    Tracks state across frames for time-based and pattern-based detections.
    """
    
    def __init__(self):
        """Initialize alert rules service with state tracking."""
        # State tracking dictionaries (keyed by camera_id)
        self.person_tracking = defaultdict(dict)  # Track person positions over time
        self.zone_presence = defaultdict(dict)  # Track zone presence duration
        self.loitering_times = defaultdict(dict)  # Track loitering duration per person
        self.zone_violations = defaultdict(list)  # Track zone violation history
        self.multiple_zone_violations_alerted = defaultdict(dict)  # Track if multiple zone violations alert was sent (camera_id -> timestamp)
        self.movement_history = defaultdict(dict)  # Track movement patterns (nested: camera_id -> person_id -> list)
        self.object_tracking = defaultdict(dict)  # Track objects (bags, weapons, etc.) - nested: camera_id -> object_id -> dict
        
        # Detection thresholds
        self.WEAPON_CONFIDENCE_THRESHOLD = 0.70
        self.RESTRICTED_AREA_PERSON_LIMIT = 3
        self.LOITERING_TIME_THRESHOLD = 30  # seconds
        self.RUNNING_SPEED_THRESHOLD = 5.0  # m/s
        self.YELLOW_ZONE_TIME_THRESHOLD = 120  # 2 minutes
        self.DIRECTION_CHANGE_THRESHOLD = 120  # degrees
        self.RAPID_APPROACH_DISTANCE = 5.0  # meters
        
        # Camera calibration (can be set per camera)
        self.pixels_per_meter = 50  # Default placeholder - should be calibrated per camera
        
        # Zone definitions (can be configured per camera)
        self.red_zones = defaultdict(list)  # No-access areas
        self.yellow_zones = defaultdict(list)  # Warning zones
        self.perimeter_lines = defaultdict(list)  # Perimeter crossing lines
    
    def reset_camera_state(self, camera_id: int):
        """Reset all tracking state for a camera."""
        self.person_tracking[camera_id].clear()
        self.zone_presence[camera_id].clear()
        self.loitering_times[camera_id].clear()
        self.zone_violations[camera_id].clear()
        self.multiple_zone_violations_alerted[camera_id].clear()
        self.movement_history[camera_id].clear()
        self.object_tracking[camera_id].clear()
    
    def detect_weapons(self, frame: np.ndarray, detections: List[Dict]) -> List[Dict]:
        """
        Detect weapons in frame (gun, knife, bat).
        This is a placeholder - in production, use trained object detection models.
        
        Args:
            frame: Video frame
            detections: List of detected objects with bounding boxes
            
        Returns:
            List of weapon detections with confidence scores
        """
        weapons = []
        
        # Placeholder: In production, use YOLO, TensorFlow Object Detection, etc.
        # For now, we'll simulate detection based on object shape/features
        # This would be replaced with actual ML model inference
        
        # Example structure for weapon detection:
        # - Use object detection model to identify weapons
        # - Check confidence > 70%
        # - Return: [{'type': 'gun', 'confidence': 0.85, 'bbox': [x, y, w, h]}, ...]
        
        return weapons
    
    def detect_multiple_persons_in_restricted_area(
        self, 
        frame: np.ndarray, 
        person_detections: List[Dict],
        camera_id: int,
        is_restricted_zone: bool
    ) -> Optional[Dict]:
        """
        Detect if more than 3 persons are in a restricted area.
        
        Args:
            frame: Video frame
            person_detections: List of detected persons
            camera_id: Camera ID
            is_restricted_zone: Whether camera is in restricted zone
            
        Returns:
            Alert data if violation detected, None otherwise
        """
        if not is_restricted_zone:
            return None
        
        person_count = len(person_detections)
        
        if person_count > self.RESTRICTED_AREA_PERSON_LIMIT:
            return {
                'alert_type': 'multiple_persons_restricted_area',
                'severity': 'high',
                'message': f'{person_count} persons detected in restricted area (limit: {self.RESTRICTED_AREA_PERSON_LIMIT})',
                'metadata': {
                    'person_count': person_count,
                    'limit': self.RESTRICTED_AREA_PERSON_LIMIT,
                    'detections': [{'bbox': d.get('bbox'), 'confidence': d.get('confidence')} for d in person_detections]
                }
            }
        
        return None
    
    def detect_unknown_objects(self, frame: np.ndarray, detections: List[Dict], 
                              camera_id: int, timestamp: datetime) -> Optional[Dict]:
        """
        Detect unknown objects left behind (bags, backpacks).
        
        Args:
            frame: Video frame
            detections: List of detected objects
            camera_id: Camera ID
            timestamp: Current timestamp
            
        Returns:
            Alert data if abandoned object detected, None otherwise
        """
        # Track stationary objects
        stationary_objects = []
        
        for obj in detections:
            obj_id = obj.get('id', hash(str(obj.get('bbox'))))
            obj_type = obj.get('type', 'unknown')
            
            # Check if object is stationary (hasn't moved significantly)
            if obj_id in self.object_tracking[camera_id]:
                prev_obj = self.object_tracking[camera_id][obj_id]
                # Calculate movement
                prev_center = prev_obj['center']
                curr_center = self._get_bbox_center(obj.get('bbox', []))
                
                if curr_center and prev_center:
                    movement = np.sqrt(
                        (curr_center[0] - prev_center[0])**2 + 
                        (curr_center[1] - prev_center[1])**2
                    )
                    
                    # If object hasn't moved much and is bag-like
                    if movement < 10 and obj_type in ['bag', 'backpack', 'suitcase', 'unknown']:
                        # Check how long it's been stationary
                        if 'stationary_since' in prev_obj:
                            stationary_time = (timestamp - prev_obj['stationary_since']).total_seconds()
                            if stationary_time > 60:  # Stationary for more than 1 minute
                                stationary_objects.append({
                                    'id': obj_id,
                                    'type': obj_type,
                                    'bbox': obj.get('bbox'),
                                    'stationary_time': stationary_time
                                })
                        else:
                            # Mark as stationary
                            prev_obj['stationary_since'] = timestamp
                    else:
                        # Object moved, reset tracking
                        prev_obj.pop('stationary_since', None)
            
            # Update tracking
            self.object_tracking[camera_id][obj_id] = {
                'center': self._get_bbox_center(obj.get('bbox', [])),
                'type': obj_type,
                'timestamp': timestamp
            }
        
        if stationary_objects:
            return {
                'alert_type': 'unknown_object_left_behind',
                'severity': 'high',
                'message': f'{len(stationary_objects)} unknown object(s) left behind',
                'metadata': {
                    'objects': stationary_objects,
                    'count': len(stationary_objects)
                }
            }
        
        return None
    
    def detect_loitering(self, person_detections: List[Dict], camera_id: int, 
                        timestamp: datetime, fps: float = 30.0) -> List[Dict]:
        """
        Detect persons loitering (>30 seconds in one spot).
        
        Args:
            person_detections: List of detected persons
            camera_id: Camera ID
            timestamp: Current timestamp
            fps: Video frame rate
            
        Returns:
            List of loitering alerts
        """
        alerts = []
        frame_interval = 1.0 / fps if fps > 0 else 1.0
        
        for person in person_detections:
            person_id = person.get('id', hash(str(person.get('bbox'))))
            bbox = person.get('bbox', [])
            
            if not bbox:
                continue
            
            center = self._get_bbox_center(bbox)
            if not center:
                continue
            
            # Check if person is in same location
            if person_id in self.loitering_times[camera_id]:
                prev_data = self.loitering_times[camera_id][person_id]
                prev_center = prev_data['center']
                
                # Calculate distance moved
                distance = np.sqrt(
                    (center[0] - prev_center[0])**2 + 
                    (center[1] - prev_center[1])**2
                )
                
                # If person hasn't moved much (within 50 pixels)
                if distance < 50:
                    # Update loitering time
                    loitering_time = prev_data.get('loitering_time', 0) + frame_interval
                    prev_data['loitering_time'] = loitering_time
                    prev_data['center'] = center
                    
                    # Check threshold
                    if loitering_time >= self.LOITERING_TIME_THRESHOLD and not prev_data.get('alerted', False):
                        alerts.append({
                            'alert_type': 'person_loitering',
                            'severity': 'medium',
                            'message': f'Person loitering for {loitering_time:.1f} seconds',
                            'metadata': {
                                'person_id': person_id,
                                'loitering_time': loitering_time,
                                'location': center
                            }
                        })
                        prev_data['alerted'] = True
                else:
                    # Person moved, reset tracking
                    self.loitering_times[camera_id][person_id] = {
                        'center': center,
                        'loitering_time': 0,
                        'alerted': False
                    }
            else:
                # First detection of this person
                self.loitering_times[camera_id][person_id] = {
                    'center': center,
                    'loitering_time': 0,
                    'alerted': False
                }
        
        return alerts
    
    def detect_running(self, person_detections: List[Dict], camera_id: int, 
                     timestamp: datetime, fps: float = 30.0) -> List[Dict]:
        """
        Detect persons running (high speed > 5m/s).
        
        Args:
            person_detections: List of detected persons
            camera_id: Camera ID
            timestamp: Current timestamp
            fps: Video frame rate
            
        Returns:
            List of running alerts
        """
        alerts = []
        frame_interval = 1.0 / fps if fps > 0 else 1.0
        
        # Use calibrated pixels_per_meter if available, otherwise use default
        pixels_per_meter = self.pixels_per_meter
        
        for person in person_detections:
            person_id = person.get('id', hash(str(person.get('bbox'))))
            bbox = person.get('bbox', [])
            
            if not bbox:
                continue
            
            center = self._get_bbox_center(bbox)
            if not center:
                continue
            
            # Track movement
            if person_id in self.person_tracking[camera_id]:
                prev_data = self.person_tracking[camera_id][person_id]
                prev_center = prev_data.get('center')
                prev_time = prev_data.get('timestamp')
                
                if prev_center and prev_time:
                    # Calculate speed (pixels per second)
                    distance_pixels = np.sqrt(
                        (center[0] - prev_center[0])**2 + 
                        (center[1] - prev_center[1])**2
                    )
                    time_diff = (timestamp - prev_time).total_seconds()
                    
                    if time_diff > 0:
                        speed_pixels_per_sec = distance_pixels / time_diff
                        speed_m_per_sec = speed_pixels_per_sec / pixels_per_meter
                        
                        if speed_m_per_sec > self.RUNNING_SPEED_THRESHOLD:
                            alerts.append({
                                'alert_type': 'person_running',
                                'severity': 'medium',
                                'message': f'Person running at {speed_m_per_sec:.1f} m/s',
                                'metadata': {
                                    'person_id': person_id,
                                    'speed': speed_m_per_sec,
                                    'location': center
                                }
                            })
            
            # Update tracking
            self.person_tracking[camera_id][person_id] = {
                'center': center,
                'timestamp': timestamp
            }
        
        return alerts
    
    def detect_group_fighting(self, person_detections: List[Dict]) -> Optional[Dict]:
        """
        Detect group fighting (overlapping bounding boxes).
        
        Args:
            person_detections: List of detected persons
            
        Returns:
            Alert data if fighting detected, None otherwise
        """
        if len(person_detections) < 2:
            return None
        
        # Check for overlapping bounding boxes
        overlapping_pairs = []
        
        for i, person1 in enumerate(person_detections):
            bbox1 = person1.get('bbox', [])
            if not bbox1 or len(bbox1) < 4:
                continue
            
            for j, person2 in enumerate(person_detections[i+1:], start=i+1):
                bbox2 = person2.get('bbox', [])
                if not bbox2 or len(bbox2) < 4:
                    continue
                
                # Calculate IoU (Intersection over Union)
                iou = self._calculate_iou(bbox1, bbox2)
                
                # If significant overlap (>30%), consider it fighting
                if iou > 0.3:
                    overlapping_pairs.append((i, j, iou))
        
        if len(overlapping_pairs) >= 2:  # Multiple overlapping pairs suggests fighting
            return {
                'alert_type': 'group_fighting',
                'severity': 'medium',
                'message': f'Group fighting detected: {len(overlapping_pairs)} overlapping person pairs',
                'metadata': {
                    'overlapping_pairs': len(overlapping_pairs),
                    'total_persons': len(person_detections),
                    'pairs': overlapping_pairs
                }
            }
        
        return None
    
    def detect_zone_intrusion(self, person_detections: List[Dict], camera_id: int,
                             timestamp: datetime, is_restricted_zone: bool,
                             red_zones: List[Dict] = None, yellow_zones: List[Dict] = None) -> List[Dict]:
        """
        Detect zone-based intrusions (red/yellow zones).
        
        Args:
            person_detections: List of detected persons
            camera_id: Camera ID
            timestamp: Current timestamp
            is_restricted_zone: Whether camera is in restricted zone
            red_zones: List of red zone definitions
            yellow_zones: List of yellow zone definitions
            
        Returns:
            List of zone intrusion alerts
        """
        alerts = []
        
        # If camera is in restricted zone, all persons are violations
        if is_restricted_zone:
            for person in person_detections:
                person_id = person.get('id', hash(str(person.get('bbox'))))
                center = self._get_bbox_center(person.get('bbox', []))
                
                if center:
                    # Track zone presence
                    if person_id not in self.zone_presence[camera_id]:
                        self.zone_presence[camera_id][person_id] = {
                            'zone_type': 'red',
                            'entry_time': timestamp,
                            'location': center
                        }
                        
                        # Immediate alert for red zone entry
                        # Include bbox for better deduplication
                        bbox = person.get('bbox', [])
                        alerts.append({
                            'alert_type': 'red_zone_entry',
                            'severity': 'critical',
                            'message': f'Person entered restricted area (no-access zone)',
                            'metadata': {
                                'person_id': person_id,
                                'zone_type': 'red',
                                'location': center,
                                'bbox': bbox,  # Include bbox for spatial deduplication
                                'entry_time': timestamp.isoformat()
                            }
                        })
                    else:
                        # Update presence duration
                        entry_time = self.zone_presence[camera_id][person_id]['entry_time']
                        presence_duration = (timestamp - entry_time).total_seconds()
                        self.zone_presence[camera_id][person_id]['presence_duration'] = presence_duration
        
        # Check defined red zones
        if red_zones:
            for person in person_detections:
                center = self._get_bbox_center(person.get('bbox', []))
                if not center:
                    continue
                
                person_id = person.get('id', hash(str(person.get('bbox'))))
                bbox = person.get('bbox', [])
                
                for zone in red_zones:
                    if self._point_in_zone(center, zone):
                        # Track zone entries per person to prevent duplicates in same frame
                        zone_key = f"{person_id}_{zone.get('name', 'unknown')}"
                        
                        # Only create alert if this person hasn't already triggered an alert for this zone
                        if zone_key not in self.zone_presence[camera_id]:
                            self.zone_presence[camera_id][zone_key] = {
                                'zone_type': 'red',
                                'entry_time': timestamp,
                                'location': center,
                                'alerted': True
                            }
                            
                            alerts.append({
                                'alert_type': 'red_zone_entry',
                                'severity': 'critical',
                                'message': f'Person entered no-access area: {zone.get("name", "Unknown")}',
                                'metadata': {
                                    'person_id': person_id,
                                    'zone_name': zone.get('name'),
                                    'location': center,
                                    'bbox': bbox  # Include bbox for spatial deduplication
                                }
                            })
        
        # Check yellow zones (warning zones)
        if yellow_zones:
            for person in person_detections:
                center = self._get_bbox_center(person.get('bbox', []))
                if not center:
                    continue
                
                person_id = person.get('id', hash(str(person.get('bbox'))))
                
                for zone in yellow_zones:
                    if self._point_in_zone(center, zone):
                        zone_key = f"{person_id}_{zone.get('name', 'unknown')}"
                        
                        if zone_key not in self.zone_presence[camera_id]:
                            self.zone_presence[camera_id][zone_key] = {
                                'zone_type': 'yellow',
                                'entry_time': timestamp,
                                'location': center
                            }
                        else:
                            # Check prolonged presence
                            entry_time = self.zone_presence[camera_id][zone_key]['entry_time']
                            presence_duration = (timestamp - entry_time).total_seconds()
                            
                            if presence_duration >= self.YELLOW_ZONE_TIME_THRESHOLD:
                                if not self.zone_presence[camera_id][zone_key].get('alerted', False):
                                    alerts.append({
                                        'alert_type': 'yellow_zone_prolonged',
                                        'severity': 'medium',
                                        'message': f'Prolonged presence in warning zone: {zone.get("name", "Unknown")} ({presence_duration:.0f}s)',
                                        'metadata': {
                                            'person_id': person_id,
                                            'zone_name': zone.get('name'),
                                            'presence_duration': presence_duration,
                                            'location': center
                                        }
                                    })
                                    self.zone_presence[camera_id][zone_key]['alerted'] = True
        
        # Track multiple zone violations
        violation_count = len([p for p in person_detections if is_restricted_zone])
        if violation_count > 0:
            self.zone_violations[camera_id].append({
                'timestamp': timestamp,
                'count': violation_count
            })
            
            # Keep only recent violations (last 5 minutes)
            cutoff_time = timestamp - timedelta(minutes=5)
            self.zone_violations[camera_id] = [
                v for v in self.zone_violations[camera_id] 
                if v['timestamp'] > cutoff_time
            ]
            
            # Check for multiple violations
            # Only alert once per 5-minute window to prevent duplicates
            if len(self.zone_violations[camera_id]) >= 3:
                # Check if we've already alerted in this time window
                last_alert_time = self.multiple_zone_violations_alerted[camera_id].get('timestamp')
                alert_cooldown = timedelta(minutes=5)  # Don't alert more than once per 5 minutes
                
                if not last_alert_time or (timestamp - last_alert_time) >= alert_cooldown:
                    alerts.append({
                        'alert_type': 'multiple_zone_violations',
                        'severity': 'medium',
                        'message': 'Multiple zone violations detected',  # Simplified message without count
                        'metadata': {
                            'violation_count': len(self.zone_violations[camera_id]),
                            'time_window': '5 minutes'
                        }
                    })
                    # Track that we've sent this alert
                    self.multiple_zone_violations_alerted[camera_id]['timestamp'] = timestamp
        
        return alerts
    
    def detect_abnormal_movement(self, person_detections: List[Dict], camera_id: int,
                                 timestamp: datetime) -> List[Dict]:
        """
        Detect abnormal movement patterns.
        
        Args:
            person_detections: List of detected persons
            camera_id: Camera ID
            timestamp: Current timestamp
            
        Returns:
            List of abnormal movement alerts
        """
        alerts = []
        
        for person in person_detections:
            person_id = person.get('id', hash(str(person.get('bbox'))))
            bbox = person.get('bbox', [])
            
            if not bbox:
                continue
            
            center = self._get_bbox_center(bbox)
            if not center:
                continue
            
            # Track movement history
            if person_id not in self.movement_history[camera_id]:
                self.movement_history[camera_id][person_id] = []
            
            history = self.movement_history[camera_id][person_id]
            history.append({
                'center': center,
                'timestamp': timestamp,
                'bbox': bbox
            })
            
            # Keep only recent history (last 10 positions)
            if len(history) > 10:
                history.pop(0)
            
            # Detect sudden direction change (U-turn)
            if len(history) >= 3:
                # Calculate direction vectors
                directions = []
                for i in range(1, len(history)):
                    prev_center = history[i-1]['center']
                    curr_center = history[i]['center']
                    
                    dx = curr_center[0] - prev_center[0]
                    dy = curr_center[1] - prev_center[1]
                    
                    if dx != 0 or dy != 0:
                        angle = np.degrees(np.arctan2(dy, dx))
                        directions.append(angle)
                
                if len(directions) >= 2:
                    # Check for sudden direction change (>120 degrees)
                    angle_diff = abs(directions[-1] - directions[-2])
                    if angle_diff > 180:
                        angle_diff = 360 - angle_diff
                    
                    if angle_diff > self.DIRECTION_CHANGE_THRESHOLD:
                        alerts.append({
                            'alert_type': 'sudden_direction_change',
                            'severity': 'medium',
                            'message': f'Sudden direction change detected (U-turn)',
                            'metadata': {
                                'person_id': person_id,
                                'angle_change': angle_diff,
                                'location': center
                            }
                        })
            
            # Detect crawling/ducking (low posture - bbox height is small relative to width)
            try:
                if bbox and len(bbox) >= 4:
                    # Determine format: [x, y, w, h] or [x1, y1, x2, y2]
                    if bbox[2] > 1000 or bbox[3] > 1000:
                        # [x1, y1, x2, y2] format
                        width = abs(bbox[2] - bbox[0])
                        height = abs(bbox[3] - bbox[1])
                    else:
                        # [x, y, w, h] format
                        width = bbox[2]
                        height = bbox[3]
                    
                    if width > 0:
                        aspect_ratio = height / width
                        # Low aspect ratio suggests crawling/ducking
                        if aspect_ratio < 0.5:
                            alerts.append({
                                'alert_type': 'crawling_ducking',
                                'severity': 'medium',
                                'message': 'Person detected in low posture (crawling/ducking)',
                                'metadata': {
                                    'person_id': person_id,
                                    'aspect_ratio': aspect_ratio,
                                    'location': center
                                }
                            })
            except (IndexError, TypeError, ValueError, ZeroDivisionError):
                # Skip if bbox format is invalid
                pass
            
            # Detect covering face / hiding objects (would need face detection integration)
            # This is a placeholder - would need face detection to check if face is covered
        
        return alerts
    
    def detect_rapid_approach(self, person_detections: List[Dict], camera_id: int,
                               timestamp: datetime, sensitive_areas: List[Dict] = None) -> List[Dict]:
        """
        Detect rapid approach to sensitive areas.
        
        Args:
            person_detections: List of detected persons
            camera_id: Camera ID
            timestamp: Current timestamp
            sensitive_areas: List of sensitive area definitions
            
        Returns:
            List of rapid approach alerts
        """
        alerts = []
        
        if not sensitive_areas:
            return alerts
        
        for person in person_detections:
            person_id = person.get('id', hash(str(person.get('bbox'))))
            center = self._get_bbox_center(person.get('bbox', []))
            
            if not center:
                continue
            
            # Check approach to sensitive areas
            for area in sensitive_areas:
                area_center = area.get('center')
                if not area_center:
                    continue
                
                # Calculate distance
                distance = np.sqrt(
                    (center[0] - area_center[0])**2 + 
                    (center[1] - area_center[1])**2
                )
                
                # Check if rapidly approaching
                if person_id in self.movement_history[camera_id]:
                    history = self.movement_history[camera_id][person_id]
                    if len(history) >= 2:
                        prev_center = history[-2]['center']
                        prev_distance = np.sqrt(
                            (prev_center[0] - area_center[0])**2 + 
                            (prev_center[1] - area_center[1])**2
                        )
                        
                        # If distance decreased significantly, person is approaching
                        if prev_distance > distance and (prev_distance - distance) > 20:
                            alerts.append({
                                'alert_type': 'rapid_approach_sensitive_area',
                                'severity': 'medium',
                                'message': f'Rapid approach to sensitive area: {area.get("name", "Unknown")}',
                                'metadata': {
                                    'person_id': person_id,
                                    'area_name': area.get('name'),
                                    'distance': distance,
                                    'location': center
                                }
                            })
        
        return alerts
    
    def analyze_frame(self, frame: np.ndarray, person_detections: List[Dict],
                     camera_id: int, timestamp: datetime, camera_config: Dict,
                     fps: float = 30.0) -> Dict:
        """
        Comprehensive frame analysis using all alert rules.
        
        Args:
            frame: Video frame
            person_detections: List of detected persons with bboxes
            camera_id: Camera ID
            timestamp: Current timestamp
            camera_config: Camera configuration (is_restricted_zone, zones, etc.)
            fps: Video frame rate
            
        Returns:
            Dictionary with all detected alerts
        """
        alerts = []
        
        is_restricted_zone = camera_config.get('is_restricted_zone', False)
        red_zones = camera_config.get('red_zones', [])
        yellow_zones = camera_config.get('yellow_zones', [])
        sensitive_areas = camera_config.get('sensitive_areas', [])
        
        # Object-based detection
        # 1. Weapons detection (HIGH PRIORITY)
        # Note: Weapon detection is handled by ObjectDetectionService in video_processing_service
        # This placeholder method is kept for compatibility but returns empty list
        # Actual weapon detection happens before this analyze_frame call
        weapon_detections = self.detect_weapons(frame, person_detections)
        for weapon in weapon_detections:
            if weapon.get('confidence', 0) > self.WEAPON_CONFIDENCE_THRESHOLD:
                alerts.append({
                    'alert_type': 'weapon_detected',
                    'severity': 'high',
                    'message': f'Weapon detected: {weapon.get("type", "unknown")} (confidence: {weapon.get("confidence", 0):.1%})',
                    'metadata': weapon
                })
        
        # 2. Multiple persons in restricted area (HIGH PRIORITY)
        multiple_persons_alert = self.detect_multiple_persons_in_restricted_area(
            frame, person_detections, camera_id, is_restricted_zone
        )
        if multiple_persons_alert:
            alerts.append(multiple_persons_alert)
        
        # 3. Unknown objects left behind (HIGH PRIORITY)
        # Note: This requires object detection - placeholder for now
        # unknown_objects_alert = self.detect_unknown_objects(frame, object_detections, camera_id, timestamp)
        # if unknown_objects_alert:
        #     alerts.append(unknown_objects_alert)
        
        # 4. Mask violations (HIGH PRIORITY) - handled by mask detection service
        
        # Medium priority detections
        # 5. Loitering
        loitering_alerts = self.detect_loitering(person_detections, camera_id, timestamp, fps)
        alerts.extend(loitering_alerts)
        
        # 6. Running
        running_alerts = self.detect_running(person_detections, camera_id, timestamp, fps)
        alerts.extend(running_alerts)
        
        # 7. Group fighting
        fighting_alert = self.detect_group_fighting(person_detections)
        if fighting_alert:
            alerts.append(fighting_alert)
        
        # Zone-based intrusion
        zone_alerts = self.detect_zone_intrusion(
            person_detections, camera_id, timestamp, is_restricted_zone,
            red_zones, yellow_zones
        )
        alerts.extend(zone_alerts)
        
        # Behavioral patterns
        abnormal_movement_alerts = self.detect_abnormal_movement(person_detections, camera_id, timestamp)
        alerts.extend(abnormal_movement_alerts)
        
        rapid_approach_alerts = self.detect_rapid_approach(person_detections, camera_id, timestamp, sensitive_areas)
        alerts.extend(rapid_approach_alerts)
        
        return {
            'alerts': alerts,
            'timestamp': timestamp.isoformat(),
            'frame_analysis': {
                'persons_detected': len(person_detections),
                'alerts_count': len(alerts)
            }
        }
    
    # Helper methods
    def _get_bbox_center(self, bbox: List) -> Optional[Tuple[int, int]]:
        """Get center point of bounding box."""
        if not bbox:
            return None
        
        try:
            if len(bbox) < 4:
                return None
            
            # Format: [x, y, w, h] or [x1, y1, x2, y2]
            # Check if it's [x1, y1, x2, y2] format (x2 < x1 would be invalid, but check if w/h makes sense)
            # If width/height are reasonable (positive), assume [x, y, w, h]
            # Otherwise, assume [x1, y1, x2, y2]
            if len(bbox) == 4:
                # Try to determine format by checking if values make sense
                # If bbox[2] and bbox[3] are very large, they might be x2, y2
                # If they're small, they're likely width, height
                if bbox[2] > 1000 or bbox[3] > 1000:
                    # Likely [x1, y1, x2, y2] format
                    x = (bbox[0] + bbox[2]) / 2
                    y = (bbox[1] + bbox[3]) / 2
                else:
                    # Likely [x, y, w, h] format
                    x = bbox[0] + bbox[2] / 2
                    y = bbox[1] + bbox[3] / 2
            else:
                return None
            
            return (int(x), int(y))
        except (IndexError, TypeError, ValueError) as e:
            # Handle any errors gracefully
            return None
    
    def _calculate_iou(self, bbox1: List, bbox2: List) -> float:
        """Calculate Intersection over Union (IoU) of two bounding boxes."""
        try:
            if not bbox1 or not bbox2 or len(bbox1) < 4 or len(bbox2) < 4:
                return 0.0
            
            # Normalize to [x1, y1, x2, y2] format
            # Determine format by checking if values are reasonable
            if len(bbox1) == 4:
                if bbox1[2] > 1000 or bbox1[3] > 1000:
                    # [x1, y1, x2, y2] format
                    x1_1, y1_1, x2_1, y2_1 = bbox1[0], bbox1[1], bbox1[2], bbox1[3]
                else:
                    # [x, y, w, h] format
                    x1_1, y1_1 = bbox1[0], bbox1[1]
                    x2_1, y2_1 = bbox1[0] + bbox1[2], bbox1[1] + bbox1[3]
            else:
                return 0.0
            
            if len(bbox2) == 4:
                if bbox2[2] > 1000 or bbox2[3] > 1000:
                    # [x1, y1, x2, y2] format
                    x1_2, y1_2, x2_2, y2_2 = bbox2[0], bbox2[1], bbox2[2], bbox2[3]
                else:
                    # [x, y, w, h] format
                    x1_2, y1_2 = bbox2[0], bbox2[1]
                    x2_2, y2_2 = bbox2[0] + bbox2[2], bbox2[1] + bbox2[3]
            else:
                return 0.0
        except (IndexError, TypeError, ValueError):
            return 0.0
        
        # Calculate intersection
        x1_i = max(x1_1, x1_2)
        y1_i = max(y1_1, y1_2)
        x2_i = min(x2_1, x2_2)
        y2_i = min(y2_1, y2_2)
        
        if x2_i <= x1_i or y2_i <= y1_i:
            return 0.0
        
        intersection = (x2_i - x1_i) * (y2_i - y1_i)
        
        # Calculate union
        area1 = (x2_1 - x1_1) * (y2_1 - y1_1)
        area2 = (x2_2 - x1_2) * (y2_2 - y1_2)
        union = area1 + area2 - intersection
        
        if union == 0:
            return 0.0
        
        return intersection / union
    
    def _point_in_zone(self, point: Tuple[int, int], zone: Dict) -> bool:
        """Check if point is inside a zone."""
        zone_type = zone.get('type', 'rectangle')
        
        if zone_type == 'rectangle':
            x, y = point
            x1, y1 = zone.get('top_left', [0, 0])
            x2, y2 = zone.get('bottom_right', [0, 0])
            return x1 <= x <= x2 and y1 <= y <= y2
        elif zone_type == 'circle':
            x, y = point
            center = zone.get('center', [0, 0])
            radius = zone.get('radius', 0)
            distance = np.sqrt((x - center[0])**2 + (y - center[1])**2)
            return distance <= radius
        elif zone_type == 'polygon':
            # Point in polygon test
            x, y = point
            vertices = zone.get('vertices', [])
            if len(vertices) < 3:
                return False
            
            inside = False
            j = len(vertices) - 1
            for i in range(len(vertices)):
                xi, yi = vertices[i]
                xj, yj = vertices[j]
                
                if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
                    inside = not inside
                j = i
            
            return inside
        
        return False

