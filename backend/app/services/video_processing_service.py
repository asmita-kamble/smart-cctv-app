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
from app.repositories.activity_repository import ActivityRepository
from app.repositories.camera_repository import CameraRepository
from app.services.alert_service import AlertService


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
            
            for frame_num, frame in self.extract_frames(video_path, frame_interval=30):
                timestamp = datetime.utcnow()
                
                # Person detection using YOLO (more accurate than face-based)
                person_detections = self.object_detection.detect_persons(frame, confidence_threshold=0.25)
                
                # Add unique IDs to person detections
                for i, person in enumerate(person_detections):
                    person['id'] = hash(f"{camera_id}_{frame_num}_{i}_{person.get('bbox', [0])[0]}")
                
                # Face detection (for mask and spoofing detection)
                face_results = self.face_detection.process_frame(frame)
                results['faces_detected'] += face_results['faces_detected']
                
                # Object detection for weapons and abandoned objects
                weapon_detections = self.object_detection.detect_weapons(frame, confidence_threshold=0.40)  # Lowered threshold
                abandoned_objects = self.object_detection.detect_abandoned_objects(frame, previous_frame)
                
                # Debug: Log weapon detection results
                if frame_num % 300 == 0:  # Log every 10 seconds
                    print(f"Frame {frame_num}: Weapon detection - found {len(weapon_detections)} weapons")
                
                # Create alerts for weapons detected
                for weapon in weapon_detections:
                    try:
                        weapon_type = weapon.get('type', 'unknown')
                        confidence = weapon.get('confidence', 0.0)
                        detection_method = weapon.get('detection_method', 'unknown')
                        
                        # Simple message without frame/confidence to allow proper deduplication
                        # Use very short deduplication window (1 second) for video processing
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
                            deduplicate=True,  # Re-enable deduplication
                            dedup_time_window=60  # 60 second window for video processing
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
                        dedup_time_window=1  # Very short window: 1 second for video processing
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
                            dedup_time_window=1  # Very short window: 1 second for video processing
                        )
                        if alert_status == 201:
                            results['alerts_created'] += 1
                
                # Mask detection
                mask_results = self.mask_detection.process_frame(frame)
                if mask_results['compliance_rate'] < 1.0:
                    mask_violations = sum(1 for m in mask_results['mask_compliance'] if not m['has_mask'])
                    results['mask_violations'] += mask_violations
                    
                    if mask_violations > 0:
                        # Create alert for mask violation (HIGH PRIORITY per alert rules)
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
                            dedup_time_window=1  # Very short window: 1 second for video processing
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
                    
                    # Determine activity type and confidence
                    if is_suspicious:
                        activity_type = suspicious_result.get('activity_type', 'suspicious_activity')
                        confidence = suspicious_result.get('confidence', 0.5)
                    else:
                        activity_type = 'motion_detected'
                        confidence = min(motion_percentage / 20.0, 1.0)  # Scale confidence based on motion
                    
                    # Create alert for suspicious activity
                    try:
                        # Simple message without motion percentage to prevent duplicates
                        simple_message = "Suspicious activity detected"
                        # Use very short deduplication window (1 second) for video processing
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
                            deduplicate=True,  # Re-enable deduplication
                            dedup_time_window=60  # 60 second window for video processing
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
                    
                    # Log activity
                    try:
                        activity_details = suspicious_result.get('details', {})
                        activity_details['video_path'] = video_path
                        activity_details['motion_percentage'] = motion_percentage
                        # Create description with activity type and motion info for logging
                        description = f"Suspicious activity: {activity_type}" + (f" (motion: {motion_percentage:.1f}%)" if motion_percentage > 0 else "")
                        ActivityRepository.create(
                            camera_id=camera_id,
                            activity_type=activity_type,
                            description=description,
                            confidence_score=confidence,
                            metadata=json.dumps(activity_details)
                        )
                    except Exception as e:
                        print(f"Frame {frame_num}: Error creating activity log: {str(e)}")
                
                # Apply alert rules (with error handling)
                # Update alert rules service to use calibrated pixels_per_meter
                if camera_config.get('pixels_per_meter'):
                    # Update the alert rules service with calibration
                    self.alert_rules.pixels_per_meter = camera_config['pixels_per_meter']
                
                try:
                    alert_rules_result = self.alert_rules.analyze_frame(
                        frame=frame,
                        person_detections=person_detections,
                        camera_id=camera_id,
                        timestamp=timestamp,
                        camera_config=camera_config,
                        fps=fps
                    )
                    
                    # Create alerts from alert rules
                    for alert_data in alert_rules_result.get('alerts', []):
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
                                dedup_time_window=1  # Very short window: 1 second for video processing
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
            
            # Mask detection
            try:
                mask_results = self.mask_detection.process_frame(frame)
                print(f"Mask detection - faces: {mask_results.get('faces_detected', 0)}, compliance: {mask_results.get('compliance_rate', 1.0)}")
                
                if mask_results.get('compliance_rate', 1.0) < 1.0:
                    mask_violations = sum(1 for m in mask_results.get('mask_compliance', []) if not m.get('has_mask', True))
                    results['mask_violations'] += mask_violations
                    
                    if mask_violations > 0:
                        # Create alert for mask violation (HIGH PRIORITY per alert rules)
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
            elif results['mask_violations'] > 0 and results['alerts_created'] == 0:
                # If mask violations detected but no alert created, create one
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
            
            # Apply alert rules for image processing
            # Person detection using YOLO (more accurate than face-based)
            person_detections = self.object_detection.detect_persons(frame, confidence_threshold=0.25)
            
            # Add unique IDs to person detections
            for i, person in enumerate(person_detections):
                person['id'] = hash(f"{camera_id}_{i}_{person.get('bbox', [0])[0]}")
            
            # Object detection for weapons and abandoned objects
            weapon_detections = self.object_detection.detect_weapons(frame, confidence_threshold=0.40)  # Lowered threshold
            abandoned_objects = self.object_detection.detect_abandoned_objects(frame)
            
            print(f"Image processing: Weapon detection - found {len(weapon_detections)} weapons")
            
            # Create alerts for weapons detected
            for weapon in weapon_detections:
                try:
                    weapon_type = weapon.get('type', 'unknown')
                    confidence = weapon.get('confidence', 0.0)
                    detection_method = weapon.get('detection_method', 'unknown')
                    
                    # Simple message without confidence/method to allow proper deduplication
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
            
            # Get camera configuration
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
            
            # Apply alert rules (with error handling)
            timestamp = datetime.utcnow()
            
            # Update alert rules service to use calibrated pixels_per_meter
            if camera_config.get('pixels_per_meter'):
                self.alert_rules.pixels_per_meter = camera_config['pixels_per_meter']
            
            try:
                alert_rules_result = self.alert_rules.analyze_frame(
                    frame=frame,
                    person_detections=person_detections,
                    camera_id=camera_id,
                    timestamp=timestamp,
                    camera_config=camera_config,
                    fps=30.0
                )
                
                # Create alerts from alert rules
                for alert_data in alert_rules_result.get('alerts', []):
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
            
            # Activity detection (for images, we can check for suspicious objects/patterns)
            # For now, we'll create a basic activity log
            if results['faces_detected'] > 0 or results['mask_violations'] > 0:
                try:
                    ActivityRepository.create(
                        camera_id=camera_id,
                        activity_type='image_analyzed',
                        description=f'Image analyzed: {results["faces_detected"]} faces, {results["mask_violations"]} mask violations',
                        confidence_score=0.8,
                        metadata=json.dumps({
                            'image_path': image_path,
                            'faces_detected': results['faces_detected'],
                            'mask_violations': results['mask_violations']
                        })
                    )
                except Exception as e:
                    print(f"Error creating activity log: {str(e)}")
                    results['warnings'].append(f'Activity log error: {str(e)}')
        
        except Exception as e:
            print(f"Image processing exception: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'error': f'Image processing failed: {str(e)}', 'traceback': traceback.format_exc()}, 500
        
        end_time = datetime.utcnow()
        results['processing_time'] = (end_time - start_time).total_seconds()
        
        print(f"Image processing complete: {results}")
        return results, 200

