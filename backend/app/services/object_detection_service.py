"""
Object Detection Service using YOLOv8 for detecting weapons and objects.
"""
import cv2
import numpy as np
from typing import Dict, List, Optional
import os


class ObjectDetectionService:
    """Service for object detection using YOLOv8."""
    
    def __init__(self):
        """Initialize object detection service."""
        self.model = None
        self.model_loaded = False
        self.weapon_classes = ['knife', 'gun', 'pistol', 'rifle', 'baseball bat', 'bat']  # COCO classes that might be weapons
        
        # Try to load YOLO model
        try:
            from ultralytics import YOLO
            # Use YOLOv8n (nano) for faster inference, or yolov8s/m/l/x for better accuracy
            model_path = os.getenv('YOLO_MODEL_PATH', 'yolov8n.pt')  # Default to nano model
            self.model = YOLO(model_path)
            self.model_loaded = True
            print(f"YOLO model loaded successfully: {model_path}")
        except ImportError:
            print("Warning: ultralytics not installed. Object detection will be disabled.")
            print("Install with: pip install ultralytics")
            self.model_loaded = False
        except Exception as e:
            print(f"Warning: Failed to load YOLO model: {str(e)}")
            self.model_loaded = False
    
    def detect_objects(self, frame: np.ndarray, confidence_threshold: float = 0.25) -> List[Dict]:
        """
        Detect objects in a video frame using YOLO.
        
        Args:
            frame: Video frame as numpy array
            confidence_threshold: Minimum confidence for detections
            
        Returns:
            List of detected objects with bounding boxes and class information
        """
        if not self.model_loaded or self.model is None:
            return []
        
        try:
            # Run YOLO inference
            results = self.model(frame, conf=confidence_threshold, verbose=False)
            
            detections = []
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for i in range(len(boxes)):
                        # Get box coordinates (x1, y1, x2, y2)
                        box = boxes.xyxy[i].cpu().numpy()
                        confidence = float(boxes.conf[i].cpu().numpy())
                        class_id = int(boxes.cls[i].cpu().numpy())
                        class_name = self.model.names[class_id]
                        
                        # Convert to [x, y, w, h] format
                        x1, y1, x2, y2 = box
                        width = x2 - x1
                        height = y2 - y1
                        
                        detections.append({
                            'bbox': [int(x1), int(y1), int(width), int(height)],
                            'class_id': class_id,
                            'class_name': class_name,
                            'confidence': confidence,
                            'type': 'object'
                        })
            
            return detections
        except Exception as e:
            print(f"Error in object detection: {str(e)}")
            return []
    
    def detect_weapons(self, frame: np.ndarray, confidence_threshold: float = 0.50) -> List[Dict]:
        """
        Detect weapons in a video frame.
        
        Note: Standard COCO dataset doesn't include weapon classes. This method:
        1. Checks for weapon-like objects in COCO classes (sports equipment, tools)
        2. Uses heuristics (shape, size, position) to identify potential weapons
        3. For production, use a custom-trained weapon detection model
        
        Args:
            frame: Video frame as numpy array
            confidence_threshold: Minimum confidence for weapon detection (default: 0.50, lowered for testing)
            
        Returns:
            List of detected weapons
        """
        if not self.model_loaded:
            print("Warning: YOLO model not loaded, weapon detection disabled")
            return []
        
        # Get all object detections with lower threshold to catch more objects
        all_detections = self.detect_objects(frame, confidence_threshold=0.25)
        
        # Get person detections to check proximity
        persons = self.detect_persons(frame, confidence_threshold=0.25)
        
        print(f"Debug weapon detection: Found {len(all_detections)} objects, {len(persons)} persons")
        
        # Filter for weapons - COCO classes that might be weapons or weapon-like
        # Expanded list of weapon-like objects
        weapon_like_classes = [
            'sports ball', 'baseball bat', 'tennis racket', 'skateboard',
            'bottle', 'cup', 'cell phone', 'remote', 'book', 'scissors',
            'umbrella', 'handbag', 'backpack', 'suitcase', 'laptop',
            'mouse', 'keyboard', 'tv', 'monitor', 'clock', 'vase'
        ]
        
        weapons = []
        detected_classes = set()
        
        for detection in all_detections:
            class_name = detection.get('class_name', '').lower()
            confidence = detection.get('confidence', 0.0)
            detected_classes.add(class_name)
            
            # Direct weapon class match (if model has weapon classes)
            is_weapon = any(weapon in class_name for weapon in self.weapon_classes)
            
            # Check for weapon-like objects that could be misidentified
            is_weapon_like = any(weapon_like in class_name for weapon_like in weapon_like_classes)
            
            # Heuristic: Check if object is near a person and has weapon-like characteristics
            bbox = detection.get('bbox', [])
            if bbox and len(bbox) >= 4:
                x, y, w, h = bbox[0], bbox[1], bbox[2], bbox[3]
                obj_center = (x + w/2, y + h/2)
                
                # Check proximity to persons
                near_person = False
                min_distance = float('inf')
                for person in persons:
                    p_bbox = person.get('bbox', [])
                    if p_bbox and len(p_bbox) >= 4:
                        px, py, pw, ph = p_bbox[0], p_bbox[1], p_bbox[2], p_bbox[3]
                        p_center = (px + pw/2, py + ph/2)
                        
                        # Calculate distance
                        distance = np.sqrt((obj_center[0] - p_center[0])**2 + (obj_center[1] - p_center[1])**2)
                        min_distance = min(min_distance, distance)
                        
                        # If object is within person's bounding box or very close (increased threshold)
                        if (px <= x <= px + pw and py <= y <= py + ph) or distance < 200:  # Increased from 100 to 200
                            near_person = True
                            break
                
                # Heuristic: Elongated objects (high aspect ratio) near persons could be weapons
                aspect_ratio = h / w if w > 0 else 0
                is_elongated = aspect_ratio > 1.5 or aspect_ratio < 0.67  # More lenient: 1.5:1 or 2:3 ratio
                
                # Size check: weapons are typically small to medium sized
                area = w * h
                frame_area = frame.shape[0] * frame.shape[1]
                size_ratio = area / frame_area if frame_area > 0 else 0
                reasonable_size = 0.0005 < size_ratio < 0.15  # More lenient: 0.05% to 15% of frame
                
                # More lenient detection logic:
                # 1. Direct weapon match (always trigger)
                # 2. Weapon-like object near person (relaxed requirements)
                # 3. Any elongated object near person with reasonable size
                # 4. High-confidence weapon-like object even without person (fallback)
                should_detect = False
                detection_reason = ""
                
                if is_weapon:
                    should_detect = True
                    detection_reason = "direct_weapon"
                elif is_weapon_like and near_person:
                    # If weapon-like and near person, be more lenient
                    should_detect = True
                    detection_reason = "weapon_like_near_person"
                elif near_person and (is_elongated or reasonable_size):
                    # Any suspicious object near person
                    should_detect = True
                    detection_reason = "suspicious_object_near_person"
                elif is_weapon_like and confidence >= 0.6:
                    # High-confidence weapon-like object even without person proximity
                    should_detect = True
                    detection_reason = "high_confidence_weapon_like"
                
                if should_detect and confidence >= confidence_threshold:
                    weapon_type = 'potential_weapon' if not is_weapon else class_name
                    weapons.append({
                        'type': weapon_type,
                        'confidence': confidence,
                        'bbox': bbox,
                        'class_id': detection.get('class_id'),
                        'class_name': class_name,
                        'detection_method': detection_reason,
                        'near_person': near_person,
                        'aspect_ratio': aspect_ratio,
                        'min_distance_to_person': min_distance if persons else None
                    })
                    print(f"Weapon detected: {weapon_type} (class: {class_name}, confidence: {confidence:.2f}, "
                          f"method: {detection_reason}, near_person: {near_person}, aspect_ratio: {aspect_ratio:.2f}, "
                          f"distance: {min_distance:.1f}px)")
                elif is_weapon_like or near_person:
                    # Debug why it wasn't detected
                    print(f"Debug: Object '{class_name}' (conf: {confidence:.2f}) not detected as weapon - "
                          f"is_weapon: {is_weapon}, is_weapon_like: {is_weapon_like}, near_person: {near_person}, "
                          f"is_elongated: {is_elongated}, reasonable_size: {reasonable_size}, "
                          f"confidence_ok: {confidence >= confidence_threshold}")
        
        # Debug: Print detected classes if no weapons found
        if not weapons:
            if len(detected_classes) > 0:
                print(f"Debug: No weapons detected. Detected classes: {', '.join(sorted(detected_classes))}")
            if len(persons) == 0:
                print(f"Debug: No persons detected - weapon detection requires persons for proximity check")
            else:
                print(f"Debug: {len(persons)} persons detected but no weapons found")
        
        return weapons
    
    def detect_persons(self, frame: np.ndarray, confidence_threshold: float = 0.25) -> List[Dict]:
        """
        Detect persons in a video frame using YOLO.
        
        Args:
            frame: Video frame as numpy array
            confidence_threshold: Minimum confidence for person detection
            
        Returns:
            List of detected persons with bounding boxes
        """
        if not self.model_loaded:
            return []
        
        try:
            # Run YOLO inference
            results = self.model(frame, conf=confidence_threshold, classes=[0], verbose=False)  # Class 0 is 'person' in COCO
            
            persons = []
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for i in range(len(boxes)):
                        # Get box coordinates (x1, y1, x2, y2)
                        box = boxes.xyxy[i].cpu().numpy()
                        confidence = float(boxes.conf[i].cpu().numpy())
                        class_id = int(boxes.cls[i].cpu().numpy())
                        
                        # Convert to [x, y, w, h] format
                        x1, y1, x2, y2 = box
                        width = x2 - x1
                        height = y2 - y1
                        
                        persons.append({
                            'bbox': [int(x1), int(y1), int(width), int(height)],
                            'confidence': confidence,
                            'class_id': class_id,
                            'type': 'person'
                        })
            
            return persons
        except Exception as e:
            print(f"Error in person detection: {str(e)}")
            return []
    
    def detect_abandoned_objects(self, frame: np.ndarray, previous_frame: Optional[np.ndarray] = None,
                                 confidence_threshold: float = 0.25) -> List[Dict]:
        """
        Detect abandoned objects (bags, backpacks, etc.) in a video frame.
        
        Args:
            frame: Current video frame
            previous_frame: Previous frame for comparison
            confidence_threshold: Minimum confidence for detection
            
        Returns:
            List of detected abandoned objects
        """
        if not self.model_loaded:
            return []
        
        # Get all object detections
        all_detections = self.detect_objects(frame, confidence_threshold=confidence_threshold)
        
        # Filter for bags, backpacks, suitcases, etc.
        # COCO classes: handbag (26), suitcase (28), backpack (24), etc.
        bag_classes = ['handbag', 'suitcase', 'backpack', 'bag', 'luggage']
        
        abandoned_objects = []
        for detection in all_detections:
            class_name = detection.get('class_name', '').lower()
            confidence = detection.get('confidence', 0.0)
            
            if any(bag in class_name for bag in bag_classes) and confidence >= confidence_threshold:
                abandoned_objects.append({
                    'type': class_name,
                    'confidence': confidence,
                    'bbox': detection.get('bbox'),
                    'class_id': detection.get('class_id')
                })
        
        return abandoned_objects

