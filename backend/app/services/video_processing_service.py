"""
Video processing service for handling video uploads and frame extraction.
Processes video files for analysis instead of live CCTV feeds.
"""
import cv2
import os
import json
from typing import Dict, List, Optional, Generator
from datetime import datetime
from app.config import Config
from app.services.face_detection_service import FaceDetectionService
from app.services.mask_detection_service import MaskDetectionService
from app.services.activity_detection_service import ActivityDetectionService
from app.services.alert_rules_service import AlertRulesService
from app.services.object_detection_service import ObjectDetectionService
from app.services.camera_calibration_service import CameraCalibrationService
from app.repositories.camera_repository import CameraRepository
from app.repositories.allowed_person_repository import AllowedPersonRepository
from app.services.alert_service import AlertService
import numpy as np
import face_recognition

# Face match tolerance for allowed-person check (higher = more lenient).
# Use a slightly stricter value to avoid falsely matching unknown (e.g. hooded) persons to allowed encodings.
ALLOWED_FACE_MATCH_TOLERANCE = 0.55


class VideoProcessingService:
    """Service for video processing and analysis."""
    
    def __init__(self):
        """Initialize video processing service."""
        self.face_detection = FaceDetectionService()
        self.mask_detection = MaskDetectionService()
        self.activity_detection = ActivityDetectionService()
        self.alert_rules = AlertRulesService()
        self.object_detection = ObjectDetectionService()
        self.upload_folder = Config.UPLOAD_FOLDER
        
        # Create upload folder if it doesn't exist
        os.makedirs(self.upload_folder, exist_ok=True)
    
    def validate_video_file(self, filename: str) -> bool:
        """Validate video file extension."""
        from app.utils.validators import validate_video_file
        return validate_video_file(filename)
    
    def save_video(self, file, filename: str) -> str:
        """
        Save uploaded video file.
        
        Args:
            file: File object
            filename: Original filename
            
        Returns:
            Path to saved file
        """
        # Generate unique filename
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        safe_filename = f"{timestamp}_{filename}"
        filepath = os.path.join(self.upload_folder, safe_filename)
        
        file.save(filepath)
        return filepath
    
    def extract_frames(self, video_path: str, frame_interval: int = 30) -> Generator:
        """
        Extract frames from video at specified intervals.
        
        Args:
            video_path: Path to video file
            frame_interval: Extract every Nth frame
            
        Yields:
            Frame number and frame array
        """
        cap = cv2.VideoCapture(video_path)
        frame_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            if frame_count % frame_interval == 0:
                yield frame_count, frame
            
            frame_count += 1
        
        cap.release()
    
    @staticmethod
    def _bbox_overlaps(bbox1: List, bbox2: List) -> bool:
        """Check if two bboxes [x, y, w, h] overlap (intersect)."""
        if not bbox1 or not bbox2 or len(bbox1) < 4 or len(bbox2) < 4:
            return False
        x1, y1, w1, h1 = bbox1[0], bbox1[1], bbox1[2], bbox1[3]
        x2, y2, w2, h2 = bbox2[0], bbox2[1], bbox2[2], bbox2[3]
        return not (x1 + w1 <= x2 or x2 + w2 <= x1 or y1 + h1 <= y2 or y2 + h2 <= y1)

    @staticmethod
    def _person_matches_allowed_face(person_bbox: List, face_bbox: List) -> bool:
        """
        True if this person detection corresponds to this allowed face (person is allowed).
        Uses overlap OR face center inside person bbox.
        """
        if not person_bbox or not face_bbox or len(person_bbox) < 4 or len(face_bbox) < 4:
            return False
        if VideoProcessingService._bbox_overlaps(person_bbox, face_bbox):
            return True
        px, py, pw, ph = person_bbox[0], person_bbox[1], person_bbox[2], person_bbox[3]
        fx, fy, fw, fh = face_bbox[0], face_bbox[1], face_bbox[2], face_bbox[3]
        face_cx = fx + fw / 2
        face_cy = fy + fh / 2
        if px <= face_cx <= px + pw and py <= face_cy <= py + ph:
            return True
        return False

    # Face must be in upper part of person bbox (top 45% by height) to count as "person's face" (avoids hood/artifact)
    _FACE_IN_PERSON_TOP_RATIO = 0.45

    @staticmethod
    def _unauthorized_persons_1to1(person_detections: List[Dict], frame_matches: List[Dict]) -> List[Dict]:
        """
        Return person detections that are NOT authorized, using 1:1 matching: each allowed face
        can only authorize one person (the best match). Face must be in upper part of person bbox
        so hooded persons (face not visible / false detection in center) stay unauthorized.
        """
        if not frame_matches:
            return list(person_detections)
        authorized_indices = set()
        for face_match in frame_matches:
            face_bbox = face_match.get('bbox')
            if not face_bbox or len(face_bbox) < 4:
                continue
            fx, fy, fw, fh = face_bbox[0], face_bbox[1], face_bbox[2], face_bbox[3]
            fc_x, fc_y = fx + fw / 2, fy + fh / 2
            best_idx = None
            best_score = -1.0
            for i, person in enumerate(person_detections):
                if i in authorized_indices:
                    continue
                p_bbox = person.get('bbox', [])
                if not p_bbox or len(p_bbox) < 4:
                    continue
                px, py, pw, ph = p_bbox[0], p_bbox[1], p_bbox[2], p_bbox[3]
                # Face must be in upper part of person (real face on body; not hood/center artifact)
                face_in_upper = py <= fc_y <= py + ph * VideoProcessingService._FACE_IN_PERSON_TOP_RATIO
                if not face_in_upper:
                    continue
                score = 0.0
                if VideoProcessingService._bbox_overlaps(p_bbox, face_bbox):
                    score = 2.0
                elif px <= fc_x <= px + pw and py <= fc_y <= py + ph:
                    score = 1.0
                if score > best_score:
                    best_score = score
                    best_idx = i
            if best_idx is not None and best_score > 0:
                authorized_indices.add(best_idx)
        return [p for i, p in enumerate(person_detections) if i not in authorized_indices]
    
    def process_video(self, video_path: str, camera_id: int) -> Dict:
        """
        Process video file for analysis.
        
        Args:
            video_path: Path to video file
            camera_id: Associated camera ID
            
        Returns:
            Processing results summary
        """
        results = {
            'frames_processed': 0,
            'faces_detected': 0,
            'spoofed_faces': 0,
            'mask_violations': 0,
            'suspicious_activities': 0,
            'alerts_created': 0,
            'processing_time': 0
        }
        
        start_time = datetime.utcnow()
        previous_frame = None
        
        print(f"Starting video processing: {video_path}, camera_id={camera_id}")
        
        # Get camera configuration
        camera = CameraRepository.find_by_id(camera_id)
        if not camera:
            print(f"ERROR: Camera {camera_id} not found")
            return {'error': f'Camera {camera_id} not found'}, 404
        print(f"Processing video for camera: {camera.name} (ID: {camera.id})")
        calibration_config = CameraCalibrationService.get_calibration_config(camera) if camera else {}
        zone_config = CameraCalibrationService.get_zone_config(camera) if camera else {}
        
        camera_config = {
            'is_restricted_zone': zone_config.get('is_restricted_zone', False),
            'red_zones': zone_config.get('red_zones', []),
            'yellow_zones': zone_config.get('yellow_zones', []),
            'sensitive_areas': zone_config.get('sensitive_areas', []),
            'pixels_per_meter': calibration_config.get('pixels_per_meter')
        }
        
        # Reset alert rules state for this camera
        self.alert_rules.reset_camera_state(camera_id)
        
        try:
            # Get video FPS for accurate time calculations
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
            cap.release()

            # Build allowed-person encodings for restricted zone (for playback name overlay)
            allowed_encodings_with_names = []  # list of (name, encoding)
            is_restricted = camera_config.get('is_restricted_zone', False)
            if is_restricted:
                allowed_persons = AllowedPersonRepository.find_by_camera_id(camera_id)
                for ap in allowed_persons:
                    if not ap.name or not ap.image_path:
                        continue
                    enc = self.face_detection.get_encoding_from_image_path(ap.image_path)
                    if enc is not None:
                        allowed_encodings_with_names.append((ap.name, enc))

            allowed_matches_by_frame = {}  # frame_num -> [{"bbox": [x,y,w,h], "name": "..."}]

            for frame_num, frame in self.extract_frames(video_path, frame_interval=30):
                timestamp = datetime.utcnow()
                
                # Person detection using YOLO (more accurate than face-based)
                person_detections = self.object_detection.detect_persons(frame, confidence_threshold=0.25)
                
                # Add unique IDs to person detections
                for i, person in enumerate(person_detections):
                    person['id'] = hash(f"{camera_id}_{frame_num}_{i}_{person.get('bbox', [0])[0]}")
                
                # Face detection (for mask and spoofing detection)
                face_results = self.face_detection.process_frame(frame)

                # Match faces to allowed persons when restricted zone has allowed list (for playback overlay + names)
                frame_all_only_allowed = False
                frame_matches = []
                if allowed_encodings_with_names:
                    faces_with_encodings = self.face_detection.detect_faces(frame)
                    for face in faces_with_encodings:
                        enc_list = face.get('encoding')
                        if enc_list is None:
                            continue
                        face_enc = np.array(enc_list, dtype=np.float64)
                        loc = face['location']
                        # bbox as [x, y, w, h] (left, top, width, height)
                        bbox = [
                            int(loc['left']),
                            int(loc['top']),
                            int(loc['right'] - loc['left']),
                            int(loc['bottom'] - loc['top'])
                        ]
                        for name, allowed_enc in allowed_encodings_with_names:
                            if face_recognition.compare_faces([allowed_enc], face_enc, tolerance=ALLOWED_FACE_MATCH_TOLERANCE)[0]:
                                frame_matches.append({'bbox': bbox, 'name': name or 'Unknown'})
                                break
                    allowed_matches_by_frame[str(frame_num)] = frame_matches
                    # num_faces_in_frame used below for frame_all_only_allowed
                    num_faces_in_frame = len(faces_with_encodings)
                else:
                    num_faces_in_frame = 0
                results['faces_detected'] += face_results['faces_detected']
                
                # Unauthorized = persons not assigned to any allowed face (1:1 matching so 3rd person when 2 allowed gets red_zone_entry)
                unauthorized_person_detections = VideoProcessingService._unauthorized_persons_1to1(
                    person_detections, frame_matches
                )
                # In restricted zone with allowed list: never create weapon/mask/suspicious alerts (red_zone_entry still allowed)
                skip_weapon_mask_suspicious = is_restricted and bool(allowed_encodings_with_names)
                
                # Object detection for weapons and abandoned objects
                weapon_detections = self.object_detection.detect_weapons(frame, confidence_threshold=0.40)  # Lowered threshold
                abandoned_objects = self.object_detection.detect_abandoned_objects(frame, previous_frame)
                
                # Debug: Log weapon detection results
                if frame_num % 300 == 0:  # Log every 10 seconds
                    print(f"Frame {frame_num}: Weapon detection - found {len(weapon_detections)} weapons")
                
                # Create alerts for weapons detected (skip in restricted zone when camera has allowed persons)
                if not skip_weapon_mask_suspicious:
                    for weapon in weapon_detections:
                        try:
                            weapon_type = weapon.get('type', 'unknown')
                            confidence = weapon.get('confidence', 0.0)
                            detection_method = weapon.get('detection_method', 'unknown')
                            
                            alert_result, alert_status = AlertService.create_alert(
                                camera_id=camera_id,
                                alert_type='weapon_detected',
                                message=f'Weapon detected: {weapon_type}',
                                severity='high',
                                metadata={
                                    'video_path': video_path,
                                    'frame': frame_num,
                                    'weapon_type': weapon_type,
                                    'confidence': confidence,
                                    'bbox': weapon.get('bbox'),
                                    'class_name': weapon.get('class_name', ''),
                                    'detection_method': detection_method,
                                    'near_person': weapon.get('near_person', False),
                                    'aspect_ratio': weapon.get('aspect_ratio', 0)
                                },
                                deduplicate=True,
                                dedup_time_window=300
                            )
                            if alert_status == 201:
                                results['alerts_created'] += 1
                                print(f"Frame {frame_num}: Created weapon_detected alert - {weapon_type} (confidence: {confidence:.2f})")
                            else:
                                print(f"Frame {frame_num}: Failed to create weapon alert: {alert_result}")
                        except Exception as e:
                            print(f"Frame {frame_num}: Error creating weapon alert: {str(e)}")
                            import traceback
                            traceback.print_exc()
                
                # Create alerts for abandoned objects
                for obj in abandoned_objects:
                    alert_result, alert_status = AlertService.create_alert(
                        camera_id=camera_id,
                        alert_type='unknown_object_left_behind',
                        message=f'Abandoned object detected: {obj.get("type", "unknown")}',
                        severity='high',
                        metadata={
                            'video_path': video_path,
                            'frame': frame_num,
                            'object_type': obj.get('type'),
                            'confidence': obj.get('confidence'),
                            'bbox': obj.get('bbox')
                        },
                        deduplicate=True,
                        dedup_time_window=300  # 5 minute window for alert activity deduplication
                    )
                    if alert_status == 201:
                        results['alerts_created'] += 1
                
                # Check for spoofed faces
                for face in face_results['faces']:
                    if face['is_spoofed']:
                        results['spoofed_faces'] += 1
                        # Create alert for spoofed face
                        alert_result, alert_status = AlertService.create_alert(
                            camera_id=camera_id,
                            alert_type='face_spoof',
                            message='Spoofed face detected',
                            severity='high',
                            metadata={
                                'video_path': video_path,
                                'frame': frame_num,
                                'confidence': face['spoof_confidence']
                            },
                            deduplicate=True,
                            dedup_time_window=300  # 5 minute window for alert activity deduplication
                        )
                        if alert_status == 201:
                            results['alerts_created'] += 1
                
                # Mask detection (skip alert when restricted zone and only allowed persons in frame)
                mask_results = self.mask_detection.process_frame(frame)
                if mask_results['compliance_rate'] < 1.0:
                    mask_violations = sum(1 for m in mask_results['mask_compliance'] if not m['has_mask'])
                    results['mask_violations'] += mask_violations
                    
                    if mask_violations > 0 and not skip_weapon_mask_suspicious:
                        alert_result, alert_status = AlertService.create_alert(
                            camera_id=camera_id,
                            alert_type='mask_violation',
                            message=f'{mask_violations} mask violation(s) detected',
                            severity='high',
                            metadata={
                                'video_path': video_path,
                                'frame': frame_num,
                                'violations': mask_violations
                            },
                            deduplicate=True,
                            dedup_time_window=300
                        )
                        if alert_status == 201:
                            results['alerts_created'] += 1
                
                # Activity detection
                activity_results = self.activity_detection.analyze_frame(frame, previous_frame)
                motion_result = activity_results.get('motion', {})
                suspicious_result = activity_results.get('suspicious_activity', {})
                
                # Debug output
                if frame_num % 300 == 0:  # Log every 10 seconds (assuming 30 fps, every 300 frames)
                    print(f"Frame {frame_num}: Motion={motion_result.get('motion_percentage', 0):.1f}%, "
                          f"Suspicious={suspicious_result.get('is_suspicious', False)}, "
                          f"Type={suspicious_result.get('activity_type', 'none')}")
                
                # Lower threshold: Create alert if motion is significant (>5%) or suspicious activity detected
                motion_percentage = motion_result.get('motion_percentage', 0)
                is_suspicious = suspicious_result.get('is_suspicious', False)
                
                if is_suspicious or motion_percentage > 5.0:  # Lower threshold from 15% to 5%
                    results['suspicious_activities'] += 1
                    
                    # Create alert for suspicious activity (skip in restricted zone when camera has allowed persons)
                    if not skip_weapon_mask_suspicious:
                        try:
                            if is_suspicious:
                                activity_type = suspicious_result.get('activity_type', 'suspicious_activity')
                                confidence = suspicious_result.get('confidence', 0.5)
                            else:
                                activity_type = 'motion_detected'
                                confidence = min(motion_percentage / 20.0, 1.0)
                            simple_message = "Suspicious activity detected"
                            alert_result, alert_status = AlertService.create_alert(
                                camera_id=camera_id,
                                alert_type='suspicious_activity',
                                message=simple_message,
                                severity='high' if is_suspicious else 'medium',
                                metadata={
                                    'video_path': video_path,
                                    'frame': frame_num,
                                    'activity_type': activity_type,
                                    'confidence': confidence,
                                    'motion_percentage': motion_percentage,
                                    'motion_pixels': motion_result.get('motion_pixels', 0)
                                },
                                deduplicate=True,
                                dedup_time_window=300
                            )
                            if alert_status == 201:
                                results['alerts_created'] += 1
                                print(f"Frame {frame_num}: Created suspicious_activity alert - {activity_type} (motion: {motion_percentage:.1f}%)")
                            else:
                                print(f"Frame {frame_num}: Failed to create alert: {alert_result}")
                        except Exception as e:
                            print(f"Frame {frame_num}: Error creating suspicious activity alert: {str(e)}")
                            import traceback
                            traceback.print_exc()
                    # Activities are only for uploads (video/image); detection events are logged as Alerts only.
                
                # Apply alert rules (with error handling)
                # Update alert rules service to use calibrated pixels_per_meter
                if camera_config.get('pixels_per_meter'):
                    # Update the alert rules service with calibration
                    self.alert_rules.pixels_per_meter = camera_config['pixels_per_meter']
                
                try:
                    # Always pass unauthorized persons to alert_rules so red_zone_entry and other zone alerts still fire
                    alert_rules_result = self.alert_rules.analyze_frame(
                        frame=frame,
                        person_detections=unauthorized_person_detections,
                        camera_id=camera_id,
                        timestamp=timestamp,
                        camera_config=camera_config,
                        fps=fps
                    )
                    
                    # Create alerts from alert rules (skip multiple_zone_violations in restricted zone with allowed list)
                    for alert_data in alert_rules_result.get('alerts', []):
                        if skip_weapon_mask_suspicious and alert_data.get('alert_type') == 'multiple_zone_violations':
                            continue
                        try:
                            alert_result, alert_status = AlertService.create_alert(
                                camera_id=camera_id,
                                alert_type=alert_data.get('alert_type', 'rule_violation'),
                                message=alert_data.get('message', 'Alert rule violation detected'),
                                severity=alert_data.get('severity', 'medium'),
                                metadata={
                                    'video_path': video_path,
                                    'frame': frame_num,
                                    **alert_data.get('metadata', {})
                                },
                                deduplicate=True,
                                dedup_time_window=300
                            )
                            if alert_status == 201:
                                results['alerts_created'] += 1
                        except Exception as alert_error:
                            print(f"Error creating alert from rule: {str(alert_error)}")
                            # Continue processing other alerts
                except Exception as rules_error:
                    print(f"Error in alert rules analysis: {str(rules_error)}")
                    import traceback
                    traceback.print_exc()
                    # Continue processing video even if alert rules fail
                
                previous_frame = frame.copy()
                results['frames_processed'] += 1

            # Save allowed-person match data for playback overlay (path must match GET /videos/detections)
            if allowed_matches_by_frame:
                try:
                    # Same path as API: UPLOAD_FOLDER + basename(video) so client request with video_filename finds it
                    detections_path = os.path.join(Config.UPLOAD_FOLDER, os.path.basename(video_path)) + '.allowed_matches.json'
                    with open(detections_path, 'w') as f:
                        json.dump({'fps': fps, 'frames': allowed_matches_by_frame}, f)
                except Exception as save_err:
                    print(f"Warning: could not save allowed matches JSON: {save_err}")
        
        except Exception as e:
            return {'error': f'Video processing failed: {str(e)}'}, 500
        
        end_time = datetime.utcnow()
        results['processing_time'] = (end_time - start_time).total_seconds()
        
        print(f"Video processing complete:")
        print(f"  Frames processed: {results['frames_processed']}")
        print(f"  Faces detected: {results['faces_detected']}")
        print(f"  Suspicious activities: {results['suspicious_activities']}")
        print(f"  Alerts created: {results['alerts_created']}")
        print(f"  Processing time: {results['processing_time']:.2f}s")
        
        return results, 200
    
    def save_image(self, file, filename: str) -> str:
        """
        Save uploaded image file.
        
        Args:
            file: File object
            filename: Original filename
            
        Returns:
            Path to saved file
        """
        # Generate unique filename
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        safe_filename = f"{timestamp}_{filename}"
        filepath = os.path.join(self.upload_folder, safe_filename)
        
        file.save(filepath)
        return filepath
    
    def process_image(self, image_path: str, camera_id: int) -> Dict:
        """
        Process image file for analysis.
        
        Args:
            image_path: Path to image file
            camera_id: Associated camera ID
            
        Returns:
            Processing results summary
        """
        results = {
            'faces_detected': 0,
            'spoofed_faces': 0,
            'mask_violations': 0,
            'suspicious_activities': 0,
            'alerts_created': 0,
            'processing_time': 0,
            'warnings': []
        }
        
        start_time = datetime.utcnow()
        
        try:
            # Read image
            frame = cv2.imread(image_path)
            if frame is None:
                return {'error': 'Failed to read image file'}, 400
            
            print(f"Processing image: {image_path}")
            print(f"Image shape: {frame.shape}")
            
            # Get camera config early for restricted-zone / allowed-person logic
            camera = CameraRepository.find_by_id(camera_id)
            calibration_config = CameraCalibrationService.get_calibration_config(camera) if camera else {}
            zone_config = CameraCalibrationService.get_zone_config(camera) if camera else {}
            camera_config = {
                'is_restricted_zone': zone_config.get('is_restricted_zone', False),
                'red_zones': zone_config.get('red_zones', []),
                'yellow_zones': zone_config.get('yellow_zones', []),
                'sensitive_areas': zone_config.get('sensitive_areas', []),
                'pixels_per_meter': calibration_config.get('pixels_per_meter')
            }
            is_restricted = camera_config.get('is_restricted_zone', False)
            allowed_encodings_with_names = []
            if is_restricted:
                allowed_persons = AllowedPersonRepository.find_by_camera_id(camera_id)
                for ap in allowed_persons:
                    if not ap.name or not ap.image_path:
                        continue
                    enc = self.face_detection.get_encoding_from_image_path(ap.image_path)
                    if enc is not None:
                        allowed_encodings_with_names.append((ap.name, enc))
            frame_matches = []
            
            # Face detection
            try:
                face_results = self.face_detection.process_frame(frame)
                results['faces_detected'] = face_results['faces_detected']
                print(f"Faces detected: {results['faces_detected']}")
            except Exception as e:
                print(f"Face detection error: {str(e)}")
                import traceback
                traceback.print_exc()
                results['warnings'].append(f'Face detection error: {str(e)}')
                face_results = {'faces_detected': 0, 'faces': []}
            
            # Check for spoofed faces
            for face in face_results.get('faces', []):
                if face.get('is_spoofed', False):
                    results['spoofed_faces'] += 1
                    # Create alert for spoofed face
                    try:
                        AlertService.create_alert(
                            camera_id=camera_id,
                            alert_type='face_spoof',
                            message='Spoofed face detected',
                            severity='high',
                            metadata={
                                'image_path': image_path,
                                'confidence': face.get('spoof_confidence', 0.0)
                            }
                        )
                        results['alerts_created'] += 1
                        print(f"Created face_spoof alert")
                    except Exception as e:
                        print(f"Error creating face_spoof alert: {str(e)}")
                        results['warnings'].append(f'Alert creation error: {str(e)}')
            
            # Person detection and face matching for overlay + unauthorized list for zone alerts
            person_detections_for_allowed = self.object_detection.detect_persons(frame, confidence_threshold=0.25)
            for i, person in enumerate(person_detections_for_allowed):
                person['id'] = hash(f"{camera_id}_{i}_{person.get('bbox', [0])[0]}")
            if allowed_encodings_with_names:
                faces_with_encodings = self.face_detection.detect_faces(frame)
                frame_matches = []
                for face in faces_with_encodings:
                    enc_list = face.get('encoding')
                    if enc_list is None:
                        continue
                    face_enc = np.array(enc_list, dtype=np.float64)
                    loc = face['location']
                    bbox = [
                        int(loc['left']), int(loc['top']),
                        int(loc['right'] - loc['left']), int(loc['bottom'] - loc['top'])
                    ]
                    for name, allowed_enc in allowed_encodings_with_names:
                        if face_recognition.compare_faces([allowed_enc], face_enc, tolerance=ALLOWED_FACE_MATCH_TOLERANCE)[0]:
                            frame_matches.append({'bbox': bbox, 'name': name or 'Unknown'})
                            break
                num_faces_in_image = len(faces_with_encodings)
            else:
                frame_matches = []
            # In restricted zone with allowed list: never create weapon/mask/suspicious (red_zone_entry still allowed)
            skip_weapon_mask_suspicious_image = is_restricted and bool(allowed_encodings_with_names)
            
            # Mask detection
            try:
                mask_results = self.mask_detection.process_frame(frame)
                print(f"Mask detection - faces: {mask_results.get('faces_detected', 0)}, compliance: {mask_results.get('compliance_rate', 1.0)}")
                
                if mask_results.get('compliance_rate', 1.0) < 1.0:
                    mask_violations = sum(1 for m in mask_results.get('mask_compliance', []) if not m.get('has_mask', True))
                    results['mask_violations'] += mask_violations
                    
                    if mask_violations > 0 and not skip_weapon_mask_suspicious_image:
                        try:
                            AlertService.create_alert(
                                camera_id=camera_id,
                                alert_type='mask_violation',
                                message=f'{mask_violations} mask violation(s) detected',
                                severity='high',
                                metadata={
                                    'image_path': image_path,
                                    'violations': mask_violations,
                                    'faces_detected': mask_results.get('faces_detected', 0)
                                }
                            )
                            results['alerts_created'] += 1
                            print(f"Created mask_violation alert")
                        except Exception as e:
                            print(f"Error creating mask_violation alert: {str(e)}")
                            results['warnings'].append(f'Alert creation error: {str(e)}')
                elif mask_results.get('faces_detected', 0) > 0:
                    # Faces detected but all have masks - create info alert for testing
                    print(f"All {mask_results.get('faces_detected', 0)} faces have masks - compliance OK")
            except Exception as e:
                print(f"Mask detection error: {str(e)}")
                import traceback
                traceback.print_exc()
                results['warnings'].append(f'Mask detection error: {str(e)}')
            
            # Only create image_processed alert if no other alerts were created AND no violations detected
            # This prevents image_processed from masking important alerts like mask_violation
            if results['alerts_created'] == 0 and results['mask_violations'] == 0 and results['spoofed_faces'] == 0:
                print("No alerts created and no violations - creating info alert")
                try:
                    alert_result, status_code = AlertService.create_alert(
                        camera_id=camera_id,
                        alert_type='image_processed',
                        message=f'Image processed: {results["faces_detected"]} faces detected. File: {os.path.basename(image_path)}',
                        severity='low' if results['faces_detected'] == 0 else 'medium',
                        metadata={
                            'image_path': image_path,
                            'faces_detected': results['faces_detected'],
                            'mask_violations': results['mask_violations'],
                            'processing_time': results.get('processing_time', 0)
                        }
                    )
                    if status_code == 201:
                        results['alerts_created'] += 1
                        print(f"Created info alert: {alert_result.get('id')}")
                    else:
                        print(f"Failed to create alert: {alert_result}")
                        results['warnings'].append(f'Alert creation returned status {status_code}')
                except Exception as e:
                    print(f"Exception creating info alert: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    results['warnings'].append(f'Info alert creation error: {str(e)}')
            elif results['mask_violations'] > 0 and results['alerts_created'] == 0 and not skip_weapon_mask_suspicious_image:
                print(f"Mask violations detected ({results['mask_violations']}) but no alert created - creating mask_violation alert")
                try:
                    AlertService.create_alert(
                        camera_id=camera_id,
                        alert_type='mask_violation',
                        message=f'{results["mask_violations"]} mask violation(s) detected',
                        severity='high',
                        metadata={
                            'image_path': image_path,
                            'violations': results['mask_violations'],
                            'faces_detected': results['faces_detected']
                        }
                    )
                    results['alerts_created'] += 1
                    print(f"Created mask_violation alert (fallback)")
                except Exception as e:
                    print(f"Error creating fallback mask_violation alert: {str(e)}")
                    results['warnings'].append(f'Fallback alert creation error: {str(e)}')
            
            # Apply alert rules for image processing (reuse person_detections from above)
            person_detections = person_detections_for_allowed
            
            # Unauthorized persons for zone/rule alerts (1:1 matching so unknown person gets red_zone_entry)
            unauthorized_person_detections = VideoProcessingService._unauthorized_persons_1to1(
                person_detections, frame_matches
            )
            
            # Object detection for weapons and abandoned objects
            weapon_detections = self.object_detection.detect_weapons(frame, confidence_threshold=0.40)  # Lowered threshold
            abandoned_objects = self.object_detection.detect_abandoned_objects(frame)
            
            print(f"Image processing: Weapon detection - found {len(weapon_detections)} weapons")
            
            # Create alerts for weapons detected (skip in restricted zone when camera has allowed persons)
            if not skip_weapon_mask_suspicious_image:
                for weapon in weapon_detections:
                    try:
                        weapon_type = weapon.get('type', 'unknown')
                        confidence = weapon.get('confidence', 0.0)
                        detection_method = weapon.get('detection_method', 'unknown')
                        alert_result, alert_status = AlertService.create_alert(
                            camera_id=camera_id,
                            alert_type='weapon_detected',
                            message=f'Weapon detected: {weapon_type}',
                            severity='high',
                            metadata={
                                'image_path': image_path,
                                'weapon_type': weapon_type,
                                'confidence': confidence,
                                'bbox': weapon.get('bbox'),
                                'class_name': weapon.get('class_name', ''),
                                'detection_method': detection_method,
                                'near_person': weapon.get('near_person', False),
                                'aspect_ratio': weapon.get('aspect_ratio', 0)
                            }
                        )
                        if alert_status == 201:
                            results['alerts_created'] += 1
                            print(f"Created weapon_detected alert - {weapon_type} (confidence: {confidence:.2f})")
                        else:
                            print(f"Failed to create weapon alert: {alert_result}")
                    except Exception as e:
                        print(f"Error creating weapon alert: {str(e)}")
                        import traceback
                        traceback.print_exc()
            
            # Create alerts for abandoned objects
            for obj in abandoned_objects:
                try:
                    AlertService.create_alert(
                        camera_id=camera_id,
                        alert_type='unknown_object_left_behind',
                        message=f'Abandoned object detected: {obj.get("type", "unknown")}',
                        severity='high',
                        metadata={
                            'image_path': image_path,
                            'object_type': obj.get('type'),
                            'confidence': obj.get('confidence'),
                            'bbox': obj.get('bbox')
                        }
                    )
                    results['alerts_created'] += 1
                except Exception as e:
                    print(f"Error creating abandoned object alert: {str(e)}")
            
            # Always pass unauthorized persons to alert_rules so red_zone_entry and other zone alerts still fire
            # Apply alert rules (with error handling)
            timestamp = datetime.utcnow()
            
            # Update alert rules service to use calibrated pixels_per_meter
            if camera_config.get('pixels_per_meter'):
                self.alert_rules.pixels_per_meter = camera_config['pixels_per_meter']
            
            try:
                alert_rules_result = self.alert_rules.analyze_frame(
                    frame=frame,
                    person_detections=unauthorized_person_detections,
                    camera_id=camera_id,
                    timestamp=timestamp,
                    camera_config=camera_config,
                    fps=30.0
                )
                
                # Create alerts from alert rules (skip multiple_zone_violations in restricted zone with allowed list)
                for alert_data in alert_rules_result.get('alerts', []):
                    if skip_weapon_mask_suspicious_image and alert_data.get('alert_type') == 'multiple_zone_violations':
                        continue
                    try:
                        AlertService.create_alert(
                            camera_id=camera_id,
                            alert_type=alert_data.get('alert_type', 'rule_violation'),
                            message=alert_data.get('message', 'Alert rule violation detected'),
                            severity=alert_data.get('severity', 'medium'),
                            metadata={
                                'image_path': image_path,
                                **alert_data.get('metadata', {})
                            }
                        )
                        results['alerts_created'] += 1
                    except Exception as e:
                        print(f"Error creating alert rule alert: {str(e)}")
                        results['warnings'].append(f'Alert rule creation error: {str(e)}')
            except Exception as rules_error:
                print(f"Error in alert rules analysis for image: {str(rules_error)}")
                import traceback
                traceback.print_exc()
                results['warnings'].append(f'Alert rules analysis error: {str(rules_error)}')
            
            # Activities for images are created on upload in the video controller (image_uploaded), not here.
        
        except Exception as e:
            print(f"Image processing exception: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'error': f'Image processing failed: {str(e)}', 'traceback': traceback.format_exc()}, 500
        
        end_time = datetime.utcnow()
        results['processing_time'] = (end_time - start_time).total_seconds()
        
        print(f"Image processing complete: {results}")
        return results, 200

