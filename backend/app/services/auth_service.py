"""
Authentication service for user login, registration, and JWT token management.
"""
from typing import Optional, Dict
from flask_jwt_extended import create_access_token
from app.repositories.user_repository import UserRepository
from app.models.user import User
from app.utils.validators import validate_email, validate_password


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

