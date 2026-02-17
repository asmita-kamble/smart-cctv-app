"""
Authentication middleware for protecting routes and role-based access control.
"""
from functools import wraps
from flask import request, jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from app.services.auth_service import AuthService


def require_auth(f):
    """Decorator to require authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # Log the authorization header for debugging
            auth_header = request.headers.get('Authorization', '')
            print(f"Auth middleware - Authorization header: {auth_header[:50] if auth_header else 'MISSING'}...")
            
            verify_jwt_in_request()
            user_id_identity = get_jwt_identity()
            print(f"Auth middleware - User ID from token: {user_id_identity} (type: {type(user_id_identity)})")
            
            # JWT identity is stored as string, convert to int for database lookup
            try:
                user_id = int(user_id_identity) if user_id_identity else None
            except (ValueError, TypeError):
                print(f"Auth middleware - Invalid user ID format: {user_id_identity}")
                return jsonify({'error': 'Invalid token format'}), 401
            
            if not user_id:
                return jsonify({'error': 'Invalid token - no user ID'}), 401
                
            user = AuthService.get_user_by_id(user_id)
            
            if not user or not user.is_active:
                print(f"Auth middleware - User not found or inactive: user={user}, is_active={user.is_active if user else 'N/A'}")
                return jsonify({'error': 'Invalid or inactive user'}), 401
            
            print(f"Auth middleware - Authentication successful for user: {user.email} (role: {user.role})")
            # Add user to kwargs for use in route handlers
            kwargs['current_user'] = user
            return f(*args, **kwargs)
        except Exception as e:
            print(f"Auth middleware - Exception: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': 'Authentication required', 'details': str(e)}), 401
    
    return decorated_function


def require_admin(f):
    """Decorator to require admin role."""
    @wraps(f)
    @require_auth
    def decorated_function(*args, **kwargs):
        user = kwargs.get('current_user')
        
        if not user or not user.is_admin():
            return jsonify({'error': 'Admin access required'}), 403
        
        return f(*args, **kwargs)
    
    return decorated_function

