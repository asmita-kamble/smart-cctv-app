"""
Authentication service for user login, registration, and JWT token management.
"""
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict
from flask_jwt_extended import create_access_token
from app.repositories.user_repository import UserRepository
from app.models.user import User
from app.utils.validators import validate_email, validate_password
from app.utils.database import db


class AuthService:
    """Service for authentication and authorization operations."""
    
    @staticmethod
    def register(email: str, username: str, password: str, role: str = 'user') -> Dict:
        """
        Register a new user.
        
        Args:
            email: User email
            username: Username
            password: Plain text password
            role: User role (default: 'user')
            
        Returns:
            Dictionary with user data and token, or error message
        """
        # Validate email
        if not validate_email(email):
            return {'error': 'Invalid email format'}, 400
        
        # Validate password
        is_valid, message = validate_password(password)
        if not is_valid:
            return {'error': message}, 400
        
        # Check if user exists
        if UserRepository.exists_by_email(email):
            return {'error': 'Email already registered'}, 409
        
        if UserRepository.exists_by_username(username):
            return {'error': 'Username already taken'}, 409
        
        # Create user
        try:
            user = UserRepository.create(email, username, password, role)
            access_token = create_access_token(identity=str(user.id))
            
            return {
                'message': 'User registered successfully',
                'user': user.to_dict(),
                'access_token': access_token
            }, 201
        except Exception as e:
            return {'error': f'Registration failed: {str(e)}'}, 500
    
    @staticmethod
    def login(email: str, password: str) -> Dict:
        """
        Authenticate user and generate JWT token.
        
        Args:
            email: User email
            password: Plain text password
            
        Returns:
            Dictionary with user data and token, or error message
        """
        # Find user
        user = UserRepository.find_by_email(email)
        if not user:
            return {'error': 'Invalid email or password'}, 401
        
        # Check password
        if not user.check_password(password):
            return {'error': 'Invalid email or password'}, 401
        
        # Check if user is active
        if not user.is_active:
            return {'error': 'Account is deactivated'}, 403
        
        # Generate token - identity must be a string
        access_token = create_access_token(identity=str(user.id))
        
        return {
            'message': 'Login successful',
            'user': user.to_dict(),
            'access_token': access_token
        }, 200
    
    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[User]:
        """Get user by ID."""
        return UserRepository.find_by_id(user_id)
    
    @staticmethod
    def verify_token(user_id: int) -> Optional[User]:
        """Verify JWT token and return user."""
        return UserRepository.find_by_id(user_id)
    
    @staticmethod
    def forgot_password(email: str) -> Dict:
        """
        Generate password reset token for user.
        
        Args:
            email: User email
            
        Returns:
            Dictionary with success message and reset token, or error message
        """
        # Validate email
        if not validate_email(email):
            return {'error': 'Invalid email format'}, 400
        
        # Find user
        user = UserRepository.find_by_email(email)
        if not user:
            # Don't reveal if email exists for security
            return {
                'message': 'If an account with that email exists, a password reset link has been sent.'
            }, 200
        
        # Check if user is active
        if not user.is_active:
            return {'error': 'Account is deactivated'}, 403
        
        # Generate secure reset token
        reset_token = secrets.token_urlsafe(32)
        reset_token_expires = datetime.utcnow() + timedelta(hours=1)  # Token expires in 1 hour
        
        # Save token to user
        user.reset_token = reset_token
        user.reset_token_expires = reset_token_expires
        db.session.commit()
        
        # In production, send email with reset link
        # For now, return token in response (for development/testing)
        return {
            'message': 'Password reset token generated successfully',
            'reset_token': reset_token,  # Remove this in production, send via email instead
            'expires_at': reset_token_expires.isoformat()
        }, 200
    
    @staticmethod
    def reset_password(token: str, new_password: str) -> Dict:
        """
        Reset user password using reset token.
        
        Args:
            token: Password reset token
            new_password: New password
            
        Returns:
            Dictionary with success message, or error message
        """
        # Validate password
        is_valid, message = validate_password(new_password)
        if not is_valid:
            return {'error': message}, 400
        
        # Find user by token
        user = UserRepository.find_by_reset_token(token)
        if not user:
            return {'error': 'Invalid or expired reset token'}, 400
        
        # Check if token is expired
        if user.reset_token_expires and user.reset_token_expires < datetime.utcnow():
            # Clear expired token
            user.reset_token = None
            user.reset_token_expires = None
            db.session.commit()
            return {'error': 'Reset token has expired'}, 400
        
        # Update password and clear token
        try:
            UserRepository.update_password(user, new_password)
            return {
                'message': 'Password reset successfully'
            }, 200
        except Exception as e:
            return {'error': f'Password reset failed: {str(e)}'}, 500

