"""
Camera repository for data access operations.
Abstracts database queries for Camera model.
"""
from typing import Optional, List
from app.models.camera import Camera
from app.utils.database import db


class CameraRepository:
    """Repository for Camera entity operations."""
    
    @staticmethod
    def create(name: str, location: str, user_id: int, ip_address: str = None, 
               rtsp_username: str = None, rtsp_password: str = None, rtsp_path: str = None,
               is_restricted_zone: bool = False, status: str = 'active') -> Camera:
        """
        Create a new camera.
        
        Args:
            name: Camera name
            location: Camera location
            user_id: Owner user ID
            ip_address: Optional IP address
            rtsp_username: Optional RTSP username
            rtsp_password: Optional RTSP password
            rtsp_path: Optional RTSP path (defaults to /stream1 if not provided)
            is_restricted_zone: Whether this is a restricted zone (ON/OFF)
            status: Camera status
            
        Returns:
            Created Camera object
        """
        camera = Camera(
            name=name,
            location=location,
            user_id=user_id,
            ip_address=ip_address,
            rtsp_username=rtsp_username,
            rtsp_password=rtsp_password,
            rtsp_path=rtsp_path,
            is_restricted_zone=is_restricted_zone,
            status=status
        )
        db.session.add(camera)
        db.session.commit()
        return camera
    
    @staticmethod
    def find_by_id(camera_id: int) -> Optional[Camera]:
        """Find camera by ID."""
        return Camera.query.get(camera_id)
    
    @staticmethod
    def find_by_user_id(user_id: int, limit: int = None, offset: int = 0) -> List[Camera]:
        """Find all cameras owned by a user."""
        query = Camera.query.filter_by(user_id=user_id)
        if limit:
            query = query.limit(limit).offset(offset)
        return query.all()
    
    @staticmethod
    def find_all(limit: int = None, offset: int = 0) -> List[Camera]:
        """Get all cameras with optional pagination."""
        query = Camera.query
        if limit:
            query = query.limit(limit).offset(offset)
        return query.all()
    
    @staticmethod
    def find_by_status(status: str, limit: int = None, offset: int = 0) -> List[Camera]:
        """Find cameras by status."""
        query = Camera.query.filter_by(status=status)
        if limit:
            query = query.limit(limit).offset(offset)
        return query.all()
    
    @staticmethod
    def find_by_name(name: str, exclude_id: int = None) -> Optional[Camera]:
        """Find camera by name (case-insensitive)."""
        query = Camera.query.filter(Camera.name.ilike(name.strip()))
        if exclude_id:
            query = query.filter(Camera.id != exclude_id)
        return query.first()
    
    @staticmethod
    def update(camera: Camera) -> Camera:
        """Update camera in database."""
        db.session.commit()
        return camera
    
    @staticmethod
    def delete(camera_id: int) -> bool:
        """Delete camera by ID."""
        camera = CameraRepository.find_by_id(camera_id)
        if camera:
            db.session.delete(camera)
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def count_by_user_id(user_id: int) -> int:
        """Count cameras owned by a user."""
        return Camera.query.filter_by(user_id=user_id).count()

