"""
Camera Calibration Service for accurate distance and speed measurements.
"""
import numpy as np
from typing import Dict, Optional, Tuple
import math


class CameraCalibrationService:
    """Service for camera calibration and distance/speed calculations."""
    
    @staticmethod
    def calculate_pixels_per_meter(camera_height: float, camera_angle: float,
                                  reference_object_height: float,
                                  reference_object_pixels: float,
                                  frame_height: int) -> float:
        """
        Calculate pixels per meter based on camera calibration parameters.
        
        Args:
            camera_height: Camera height in meters
            camera_angle: Camera angle in degrees (0 = horizontal, 90 = vertical down)
            reference_object_height: Reference object height in meters (e.g., average person = 1.7m)
            reference_object_pixels: Reference object height in pixels
            frame_height: Frame height in pixels
            
        Returns:
            Pixels per meter value
        """
        if reference_object_pixels <= 0 or reference_object_height <= 0:
            return None
        
        # Simple calculation: if we know object height in pixels and meters
        pixels_per_meter = reference_object_pixels / reference_object_height
        
        # Adjust for camera angle (simplified)
        angle_rad = math.radians(camera_angle)
        if angle_rad > 0:
            # Account for perspective distortion
            pixels_per_meter = pixels_per_meter / math.cos(angle_rad)
        
        return pixels_per_meter
    
    @staticmethod
    def calculate_distance(pixel_distance: float, pixels_per_meter: Optional[float]) -> Optional[float]:
        """
        Calculate real-world distance from pixel distance.
        
        Args:
            pixel_distance: Distance in pixels
            pixels_per_meter: Calibration value (pixels per meter)
            
        Returns:
            Distance in meters, or None if calibration not available
        """
        if pixels_per_meter is None or pixels_per_meter <= 0:
            return None
        
        return pixel_distance / pixels_per_meter
    
    @staticmethod
    def calculate_speed(pixel_distance: float, time_seconds: float,
                       pixels_per_meter: Optional[float]) -> Optional[float]:
        """
        Calculate speed in m/s from pixel distance and time.
        
        Args:
            pixel_distance: Distance moved in pixels
            time_seconds: Time elapsed in seconds
            pixels_per_meter: Calibration value (pixels per meter)
            
        Returns:
            Speed in m/s, or None if calibration not available
        """
        if time_seconds <= 0:
            return None
        
        distance = CameraCalibrationService.calculate_distance(pixel_distance, pixels_per_meter)
        if distance is None:
            return None
        
        return distance / time_seconds
    
    @staticmethod
    def get_calibration_config(camera) -> Dict:
        """
        Get calibration configuration from camera object.
        
        Args:
            camera: Camera model instance
            
        Returns:
            Dictionary with calibration parameters
        """
        return {
            'pixels_per_meter': camera.pixels_per_meter,
            'camera_height': camera.camera_height,
            'camera_angle': camera.camera_angle,
            'reference_object_height': camera.reference_object_height,
            'is_calibrated': camera.pixels_per_meter is not None and camera.pixels_per_meter > 0
        }
    
    @staticmethod
    def get_zone_config(camera) -> Dict:
        """
        Get zone configuration from camera object.
        
        Args:
            camera: Camera model instance
            
        Returns:
            Dictionary with zone configurations
        """
        import json
        
        def parse_json_field(field_value):
            if not field_value:
                return []
            try:
                return json.loads(field_value)
            except (json.JSONDecodeError, TypeError):
                return []
        
        return {
            'is_restricted_zone': camera.is_restricted_zone,
            'red_zones': parse_json_field(camera.red_zones),
            'yellow_zones': parse_json_field(camera.yellow_zones),
            'sensitive_areas': parse_json_field(camera.sensitive_areas),
            'perimeter_lines': parse_json_field(camera.perimeter_lines)
        }

