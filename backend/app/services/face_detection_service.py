"""
Face detection service for identifying real and spoofed faces.
Uses OpenCV and face_recognition library for face detection and verification.
"""
import cv2
import numpy as np
import face_recognition
from typing import Dict, List, Tuple, Optional
import json


class FaceDetectionService:
    """Service for face detection and spoofing detection."""
    
    def __init__(self):
        """Initialize face detection service."""
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
    
    def detect_faces(self, frame: np.ndarray) -> List[Dict]:
        """
        Detect faces in a video frame.
        
        Args:
            frame: Video frame as numpy array
            
        Returns:
            List of detected faces with bounding boxes and encodings
        """
        # Convert BGR to RGB (face_recognition uses RGB)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Find face locations
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
        
        faces = []
        for i, (top, right, bottom, left) in enumerate(face_locations):
            face_data = {
                'location': {
                    'top': int(top),
                    'right': int(right),
                    'bottom': int(bottom),
                    'left': int(left)
                },
                'encoding': face_encodings[i].tolist() if i < len(face_encodings) else None,
                'confidence': 1.0  # face_recognition doesn't provide confidence, using 1.0
            }
            faces.append(face_data)
        
        return faces
    
    def detect_spoofed_face(self, frame: np.ndarray, face_location: Tuple) -> Dict:
        """
        Detect if a face is spoofed (photo, video, mask attack).
        This is a simplified implementation. In production, use advanced ML models.
        
        Args:
            frame: Video frame
            face_location: Face location tuple (top, right, bottom, left)
            
        Returns:
            Dictionary with spoofing detection results
        """
        top, right, bottom, left = face_location
        face_roi = frame[top:bottom, left:right]
        
        if face_roi.size == 0:
            return {
                'is_spoofed': False,
                'confidence': 0.0,
                'method': 'unknown'
            }
        
        # Convert to grayscale for analysis
        gray_roi = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
        
        # Basic spoofing detection using texture analysis
        # In production, use deep learning models (e.g., Anti-Spoofing models)
        laplacian_var = cv2.Laplacian(gray_roi, cv2.CV_64F).var()
        
        # Heuristic: Real faces typically have higher texture variance
        # This is a simplified approach - use proper ML models in production
        is_spoofed = laplacian_var < 100  # Threshold can be tuned
        confidence = min(abs(laplacian_var - 100) / 100, 1.0)
        
        return {
            'is_spoofed': is_spoofed,
            'confidence': float(confidence),
            'method': 'texture_analysis',
            'laplacian_variance': float(laplacian_var)
        }
    
    def process_frame(self, frame: np.ndarray) -> Dict:
        """
        Process a video frame for face detection and spoofing detection.
        
        Args:
            frame: Video frame as numpy array
            
        Returns:
            Dictionary with detection results
        """
        faces = self.detect_faces(frame)
        
        results = {
            'faces_detected': len(faces),
            'faces': []
        }
        
        for face in faces:
            face_location = (
                face['location']['top'],
                face['location']['right'],
                face['location']['bottom'],
                face['location']['left']
            )
            
            spoof_result = self.detect_spoofed_face(frame, face_location)
            
            face_result = {
                'location': face['location'],
                'is_spoofed': spoof_result['is_spoofed'],
                'spoof_confidence': spoof_result['confidence'],
                'detection_confidence': face.get('confidence', 1.0)
            }
            
            results['faces'].append(face_result)
        
        return results

