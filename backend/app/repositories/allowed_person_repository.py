"""
AllowedPerson repository for data access operations.
Abstracts database queries for AllowedPerson model.
"""
from typing import Optional, List
from app.models.allowed_person import AllowedPerson
from app.utils.database import db


class AllowedPersonRepository:
    """Repository for AllowedPerson entity operations."""
    
    @staticmethod
    def create(camera_id: int, image_path: str, name: str = None) -> AllowedPerson:
        """
        Create a new allowed person record.
        
        Args:
            camera_id: Associated camera ID
            image_path: Path to the stored image file
            name: Optional name/identifier for the person
            
        Returns:
            Created AllowedPerson object
        """
        allowed_person = AllowedPerson(
            camera_id=camera_id,
            image_path=image_path,
            name=name
        )
        db.session.add(allowed_person)
        db.session.commit()
        return allowed_person
    
    @staticmethod
    def find_by_id(allowed_person_id: int) -> Optional[AllowedPerson]:
        """Find allowed person by ID."""
        return AllowedPerson.query.get(allowed_person_id)
    
    @staticmethod
    def find_by_camera_id(camera_id: int, limit: int = None, offset: int = 0) -> List[AllowedPerson]:
        """Find all allowed persons for a specific camera."""
        query = AllowedPerson.query.filter_by(camera_id=camera_id).order_by(AllowedPerson.created_at.desc())
        if limit:
            query = query.limit(limit).offset(offset)
        return query.all()
    
    @staticmethod
    def find_all(limit: int = None, offset: int = 0) -> List[AllowedPerson]:
        """Get all allowed persons with optional pagination."""
        query = AllowedPerson.query.order_by(AllowedPerson.created_at.desc())
        if limit:
            query = query.limit(limit).offset(offset)
        return query.all()
    
    @staticmethod
    def update(allowed_person: AllowedPerson) -> AllowedPerson:
        """Update allowed person in database."""
        db.session.commit()
        return allowed_person
    
    @staticmethod
    def delete(allowed_person_id: int) -> bool:
        """Delete allowed person by ID."""
        allowed_person = AllowedPersonRepository.find_by_id(allowed_person_id)
        if allowed_person:
            db.session.delete(allowed_person)
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def delete_by_camera_id(camera_id: int) -> int:
        """Delete all allowed persons for a camera. Returns count of deleted records."""
        count = AllowedPerson.query.filter_by(camera_id=camera_id).delete()
        db.session.commit()
        return count
    
    @staticmethod
    def count_by_camera_id(camera_id: int) -> int:
        """Count allowed persons for a camera."""
        return AllowedPerson.query.filter_by(camera_id=camera_id).count()

