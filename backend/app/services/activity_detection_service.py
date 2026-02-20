"""
Activity detection service for identifying suspicious or unusual activities.
Analyzes video feeds for abnormal behavior patterns.
"""
import cv2
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime


class ActivityDetectionService:
    """Service for detecting suspicious activities and behaviors."""
    
    def __init__(self):
        """Initialize activity detection service."""
        # Background subtractor for motion detection
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=500, varThreshold=50, detectShadows=True
        )
        self.motion_threshold = 500  # Lower threshold: Minimum pixels for motion detection (reduced from 1000)
        self.suspicious_activity_types = [
            'rapid_movement',
            'loitering',
            'unusual_object',
            'crowd_gathering',
            'unauthorized_access'
        ]
    
    def detect_motion(self, frame: np.ndarray) -> Dict:
        """
        Detect motion in video frame.
        
        Args:
            frame: Video frame as numpy array
            
        Returns:
            Dictionary with motion detection results
        """
        # Apply background subtraction
        fg_mask = self.bg_subtractor.apply(frame)
        
        # Remove noise
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)
        
        # Calculate motion area
        motion_pixels = cv2.countNonZero(fg_mask)
        frame_area = frame.shape[0] * frame.shape[1]
        motion_percentage = (motion_pixels / frame_area) * 100
        
        # Detect if motion is significant
        has_motion = motion_pixels > self.motion_threshold
        
        return {
            'has_motion': has_motion,
            'motion_pixels': int(motion_pixels),
            'motion_percentage': float(motion_percentage),
            'motion_mask': fg_mask
        }
    
    def detect_suspicious_activity(self, frame: np.ndarray, previous_frame: Optional[np.ndarray] = None) -> Dict:
        """
        Detect suspicious activities in video frame.
        
        Args:
            frame: Current video frame
            previous_frame: Previous frame for comparison
            
        Returns:
            Dictionary with suspicious activity detection results
        """
        results = {
            'is_suspicious': False,
            'activity_type': None,
            'confidence': 0.0,
            'details': {}
        }
        
        # Detect motion
        motion_result = self.detect_motion(frame)
        
        # Check for rapid movement (high motion percentage)
        # Lower threshold to be more sensitive (5% instead of 15%)
        motion_threshold = 5.0  # More than 5% of frame has motion
        if motion_result['motion_percentage'] > motion_threshold:
            results['is_suspicious'] = True
            results['activity_type'] = 'rapid_movement'
            results['confidence'] = min(motion_result['motion_percentage'] / 30, 1.0)  # Adjusted scaling
            results['details'] = {
                'motion_percentage': motion_result['motion_percentage'],
                'reason': f'High motion detected ({motion_result["motion_percentage"]:.1f}%)'
            }
        
        # Frame difference analysis (if previous frame available)
        if previous_frame is not None:
            # Calculate frame difference
            diff = cv2.absdiff(frame, previous_frame)
            gray_diff = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
            _, thresh = cv2.threshold(gray_diff, 30, 255, cv2.THRESH_BINARY)
            
            # Find contours
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Check for large objects or multiple objects
            large_objects = [c for c in contours if cv2.contourArea(c) > 5000]
            
            if len(large_objects) > 3:  # Multiple large objects
                results['is_suspicious'] = True
                results['activity_type'] = 'crowd_gathering'
                results['confidence'] = min(len(large_objects) / 10, 1.0)
                results['details'] = {
                    'object_count': len(large_objects),
                    'reason': 'Multiple large objects detected'
                }
        
        return results
    
    def analyze_frame(self, frame: np.ndarray, previous_frame: Optional[np.ndarray] = None) -> Dict:
        """
        Comprehensive frame analysis for activity detection.
        
        Args:
            frame: Current video frame
            previous_frame: Previous frame for comparison
            
        Returns:
            Dictionary with complete analysis results
        """
        motion_result = self.detect_motion(frame)
        suspicious_result = self.detect_suspicious_activity(frame, previous_frame)
        
        return {
            'motion': motion_result,
            'suspicious_activity': suspicious_result,
            'timestamp': datetime.utcnow().isoformat()
        }

