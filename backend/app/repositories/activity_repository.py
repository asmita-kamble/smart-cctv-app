"""
Activity repository for data access operations.
Abstracts database queries for Activity model.
"""
from typing import Optional, List
from datetime import datetime
from app.models.activity import Activity
from app.utils.database import db


class ActivityRepository:
    """Repository for Activity entity operations."""
    
    @staticmethod
    def create(camera_id: int, activity_type: str, description: str, 
               confidence_score: float = None, metadata: str = None, 
               timestamp: datetime = None) -> Activity:
        """
        Create a new activity record.
        
        Args:
            camera_id: Associated camera ID
            activity_type: Type of activity
            description: Activity description
            confidence_score: Detection confidence
            metadata: Optional JSON metadata
            timestamp: When activity occurred
            
        Returns:
            Created Activity object
        """
        activity = Activity(
            camera_id=camera_id,
            activity_type=activity_type,
            description=description,
            confidence_score=confidence_score,
            meta_data=metadata,
            timestamp=timestamp or datetime.utcnow()
        )
        db.session.add(activity)
        db.session.commit()
        return activity
    
    @staticmethod
    def find_by_id(activity_id: int) -> Optional[Activity]:
        """Find activity by ID."""
        return Activity.query.get(activity_id)
    
    @staticmethod
    def find_by_camera_id(camera_id: int, limit: int = None, offset: int = 0) -> List[Activity]:
        """Find activities for a specific camera."""
        query = Activity.query.filter_by(camera_id=camera_id).order_by(Activity.timestamp.desc())
        if limit:
            query = query.limit(limit).offset(offset)
        return query.all()
    
    @staticmethod
    def find_by_type(activity_type: str, limit: int = None, offset: int = 0) -> List[Activity]:
        """Find activities by type."""
        query = Activity.query.filter_by(activity_type=activity_type).order_by(Activity.timestamp.desc())
        if limit:
            query = query.limit(limit).offset(offset)
        return query.all()
    
    @staticmethod
    def find_recent(limit: int = 100, offset: int = 0) -> List[Activity]:
        """Find recent activities."""
        query = Activity.query.order_by(Activity.timestamp.desc())
        if limit:
            query = query.limit(limit).offset(offset)
        return query.all()
    
    @staticmethod
    def find_by_date_range(start_date: datetime, end_date: datetime, 
                          limit: int = None, offset: int = 0) -> List[Activity]:
        """Find activities within a date range."""
        query = Activity.query.filter(
            Activity.timestamp >= start_date,
            Activity.timestamp <= end_date
        ).order_by(Activity.timestamp.desc())
        if limit:
            query = query.limit(limit).offset(offset)
        return query.all()
    
    @staticmethod
    def find_by_camera_and_type(camera_id: int, activity_type: str, 
                                limit: int = None, offset: int = 0) -> List[Activity]:
        """Find activities by camera and type."""
        query = Activity.query.filter_by(
            camera_id=camera_id,
            activity_type=activity_type
        ).order_by(Activity.timestamp.desc())
        if limit:
            query = query.limit(limit).offset(offset)
        return query.all()
    
    @staticmethod
    def update(activity: Activity) -> Activity:
        """Update activity in database."""
        db.session.commit()
        return activity
    
    @staticmethod
    def delete(activity_id: int) -> bool:
        """Delete activity by ID."""
        activity = ActivityRepository.find_by_id(activity_id)
        if activity:
            db.session.delete(activity)
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def count_by_camera_id(camera_id: int) -> int:
        """Count activities for a camera."""
        return Activity.query.filter_by(camera_id=camera_id).count()

