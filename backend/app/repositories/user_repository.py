"""
User repository for data access operations.
Abstracts database queries for User model.
"""
from typing import Optional, List
from app.models.user import User
from app.utils.database import db


class UserRepository:
    """Repository for User entity operations."""
    
    @staticmethod
    def create(email: str, username: str, password: str, role: str = 'user') -> User:
        """
        Create a new user.
        
        Args:
            email: User email
            username: Username
            password: Plain text password (will be hashed)
            role: User role (admin/user)
            
        Returns:
            Created User object
        """
        user = User(email=email, username=username, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user
    
    @staticmethod
    def find_by_id(user_id: int) -> Optional[User]:
        """Find user by ID."""
        return User.query.get(user_id)
    
    @staticmethod
    def find_by_email(email: str) -> Optional[User]:
        """Find user by email."""
        return User.query.filter_by(email=email).first()
    
    @staticmethod
    def find_by_username(username: str) -> Optional[User]:
        """Find user by username."""
        return User.query.filter_by(username=username).first()
    
    @staticmethod
    def find_all(limit: int = None, offset: int = 0) -> List[User]:
        """Get all users with optional pagination."""
        query = User.query
        if limit:
            query = query.limit(limit).offset(offset)
        return query.all()
    
    @staticmethod
    def update(user: User) -> User:
        """Update user in database."""
        db.session.commit()
        return user
    
    @staticmethod
    def delete(user_id: int) -> bool:
        """Delete user by ID."""
        user = UserRepository.find_by_id(user_id)
        if user:
            db.session.delete(user)
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def exists_by_email(email: str) -> bool:
        """Check if user with email exists."""
        return User.query.filter_by(email=email).first() is not None
    
    @staticmethod
    def exists_by_username(username: str) -> bool:
        """Check if user with username exists."""
        return User.query.filter_by(username=username).first() is not None
    
    @staticmethod
    def find_by_reset_token(token: str) -> Optional[User]:
        """Find user by reset token."""
        return User.query.filter_by(reset_token=token).first()
    
    @staticmethod
    def update_password(user: User, new_password: str) -> User:
        """Update user password and clear reset token."""
        user.set_password(new_password)
        user.reset_token = None
        user.reset_token_expires = None
        db.session.commit()
        return user

