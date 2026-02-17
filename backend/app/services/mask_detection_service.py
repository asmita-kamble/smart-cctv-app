"""
Mask detection service for identifying mask compliance.
Uses computer vision techniques to detect if faces are wearing masks.
"""
import cv2
import numpy as np
from typing import Dict, List, Tuple
import face_recognition


class MaskDetectionService:
    """Service for mask detection and compliance tracking."""
    
    def __init__(self):
        """Initialize mask detection service."""
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
    
    def detect_mask(self, frame: np.ndarray, face_location: Tuple) -> Dict:
        """
        Detect if a face is wearing a mask.
        This is a simplified implementation. In production, use trained ML models.
        
        Args:
            frame: Video frame
            face_location: Face location tuple (top, right, bottom, left)
            
        Returns:
            Dictionary with mask detection results
        """
        top, right, bottom, left = face_location
        face_roi = frame[top:bottom, left:right]
        
        if face_roi.size == 0:
            return {
                'has_mask': False,
                'confidence': 0.0
            }
        
        # Calculate face dimensions
        face_height = bottom - top
        face_width = right - left
        
        # Mask typically covers lower half of face (nose and mouth area)
        # Check the lower portion of the face for mask-like patterns
        lower_face_start = int(face_height * 0.4)  # Start from 40% down the face
        lower_face_roi = face_roi[lower_face_start:, :]
        
        if lower_face_roi.size == 0:
            return {
                'has_mask': False,
                'confidence': 0.0
            }
        
        # Convert to HSV for better color analysis
        hsv_roi = cv2.cvtColor(lower_face_roi, cv2.COLOR_BGR2HSV)
        
        # Masks are typically blue, white, or have specific color ranges
        # This is a heuristic approach - use trained models in production
        lower_blue = np.array([100, 50, 50])
        upper_blue = np.array([130, 255, 255])
        blue_mask = cv2.inRange(hsv_roi, lower_blue, upper_blue)
        
        # Check for white/light colors (surgical masks)
        lower_white = np.array([0, 0, 200])
        upper_white = np.array([180, 30, 255])
        white_mask = cv2.inRange(hsv_roi, lower_white, upper_white)
        
        # Calculate mask coverage percentage
        blue_coverage = np.sum(blue_mask > 0) / blue_mask.size
        white_coverage = np.sum(white_mask > 0) / white_mask.size
        total_coverage = max(blue_coverage, white_coverage)
        
        # Heuristic: If more than 30% of lower face is covered, likely has mask
        has_mask = total_coverage > 0.3
        confidence = min(total_coverage * 2, 1.0)  # Scale to 0-1
        
        return {
            'has_mask': has_mask,
            'confidence': float(confidence),
            'coverage_percentage': float(total_coverage * 100)
        }
    
    def process_frame(self, frame: np.ndarray) -> Dict:
        """
        Process a video frame for mask detection.
        
        Args:
            frame: Video frame as numpy array
            
        Returns:
            Dictionary with mask detection results
        """
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Find face locations
        face_locations = face_recognition.face_locations(rgb_frame)
        
        results = {
            'faces_detected': len(face_locations),
            'mask_compliance': [],
            'compliance_rate': 0.0
        }
        
        mask_count = 0
        
        for face_location in face_locations:
            top, right, bottom, left = face_location
            mask_result = self.detect_mask(frame, (top, right, bottom, left))
            
            if mask_result['has_mask']:
                mask_count += 1
            
            results['mask_compliance'].append({
                'location': {
                    'top': int(top),
                    'right': int(right),
                    'bottom': int(bottom),
                    'left': int(left)
                },
                'has_mask': mask_result['has_mask'],
                'confidence': mask_result['confidence']
            })
        
        # Calculate compliance rate
        if len(face_locations) > 0:
            results['compliance_rate'] = float(mask_count / len(face_locations))
        else:
            results['compliance_rate'] = 1.0  # No faces = 100% compliance
        
        return results

