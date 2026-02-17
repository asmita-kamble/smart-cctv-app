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
from app.repositories.activity_repository import ActivityRepository
from app.services.alert_service import AlertService


class VideoProcessingService:
    """Service for video processing and analysis."""
    
    def __init__(self):
        """Initialize video processing service."""
        self.face_detection = FaceDetectionService()
        self.mask_detection = MaskDetectionService()
        self.activity_detection = ActivityDetectionService()
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
        
        try:
            for frame_num, frame in self.extract_frames(video_path, frame_interval=30):
                # Face detection
                face_results = self.face_detection.process_frame(frame)
                results['faces_detected'] += face_results['faces_detected']
                
                # Check for spoofed faces
                for face in face_results['faces']:
                    if face['is_spoofed']:
                        results['spoofed_faces'] += 1
                        # Create alert for spoofed face
                        AlertService.create_alert(
                            camera_id=camera_id,
                            alert_type='face_spoof',
                            message=f'Spoofed face detected at frame {frame_num}',
                            severity='high',
                            metadata={
                                'video_path': video_path,
                                'frame': frame_num,
                                'confidence': face['spoof_confidence']
                            }
                        )
                        results['alerts_created'] += 1
                
                # Mask detection
                mask_results = self.mask_detection.process_frame(frame)
                if mask_results['compliance_rate'] < 1.0:
                    mask_violations = sum(1 for m in mask_results['mask_compliance'] if not m['has_mask'])
                    results['mask_violations'] += mask_violations
                    
                    if mask_violations > 0:
                        # Create alert for mask violation
                        AlertService.create_alert(
                            camera_id=camera_id,
                            alert_type='mask_violation',
                            message=f'{mask_violations} mask violation(s) detected at frame {frame_num}',
                            severity='medium',
                            metadata={
                                'video_path': video_path,
                                'frame': frame_num,
                                'violations': mask_violations
                            }
                        )
                        results['alerts_created'] += 1
                
                # Activity detection
                activity_results = self.activity_detection.analyze_frame(frame, previous_frame)
                if activity_results['suspicious_activity']['is_suspicious']:
                    results['suspicious_activities'] += 1
                    # Create alert for suspicious activity
                    AlertService.create_alert(
                        camera_id=camera_id,
                        alert_type='suspicious_activity',
                        message=f"Suspicious activity detected: {activity_results['suspicious_activity']['activity_type']}",
                        severity='high',
                        metadata={
                            'video_path': video_path,
                            'frame': frame_num,
                            'activity_type': activity_results['suspicious_activity']['activity_type'],
                            'confidence': activity_results['suspicious_activity']['confidence']
                        }
                    )
                    results['alerts_created'] += 1
                    
                    # Log activity
                    activity_details = activity_results['suspicious_activity'].get('details', {})
                    activity_details['video_path'] = video_path
                    ActivityRepository.create(
                        camera_id=camera_id,
                        activity_type=activity_results['suspicious_activity']['activity_type'],
                        description=activity_results['suspicious_activity'].get('details', {}).get('reason', 'Suspicious activity detected'),
                        confidence_score=activity_results['suspicious_activity']['confidence'],
                        metadata=json.dumps(activity_details)
                    )
                
                previous_frame = frame.copy()
                results['frames_processed'] += 1
        
        except Exception as e:
            return {'error': f'Video processing failed: {str(e)}'}, 500
        
        end_time = datetime.utcnow()
        results['processing_time'] = (end_time - start_time).total_seconds()
        
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
                            message=f'Spoofed face detected in image',
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
                        # Create alert for mask violation
                        try:
                            AlertService.create_alert(
                                camera_id=camera_id,
                                alert_type='mask_violation',
                                message=f'{mask_violations} mask violation(s) detected in image',
                                severity='medium',
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
                        message=f'{results["mask_violations"]} mask violation(s) detected in image',
                        severity='medium',
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

