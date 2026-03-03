"""
Authentication controller for handling login and registration endpoints.
"""
from flask import Blueprint, request, jsonify
from app.services.auth_service import AuthService
from app.middleware.auth_middleware import require_auth

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        email = data.get('email')
        username = data.get('username')
        password = data.get('password')
        role = data.get('role', 'user')
        
        if not email or not username or not password:
            return jsonify({
                'error': 'Email, username, and password are required',
                'received': {
                    'has_email': bool(email),
                    'has_username': bool(username),
                    'has_password': bool(password)
                }
            }), 400
        
        result, status_code = AuthService.register(email, username, password, role)
        return jsonify(result), status_code
    except Exception as e:
        return jsonify({'error': f'Registration error: {str(e)}'}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """Authenticate user and return JWT token."""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400
    
    result, status_code = AuthService.login(email, password)
    return jsonify(result), status_code


@auth_bp.route('/verify-email', methods=['GET', 'POST'])
def verify_email():
    """Verify user email using token from the verification link."""
    token = None
    if request.method == 'GET':
        token = request.args.get('token')
    else:
        data = request.get_json() or {}
        token = data.get('token')
    if not token:
        return jsonify({'error': 'Verification token is required'}), 400
    result, status_code = AuthService.verify_email(token)
    return jsonify(result), status_code


@auth_bp.route('/me', methods=['GET'])
@require_auth
def get_current_user(current_user):
    """Get current authenticated user information."""
    return jsonify({
        'user': current_user.to_dict()
    }), 200


@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """Request password reset token."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        email = data.get('email')
        
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        
        result, status_code = AuthService.forgot_password(email)
        return jsonify(result), status_code
    except Exception as e:
        return jsonify({'error': f'Forgot password error: {str(e)}'}), 500


@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """Reset password using reset token."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        token = data.get('token')
        new_password = data.get('password')
        
        if not token or not new_password:
            return jsonify({'error': 'Token and password are required'}), 400
        
        result, status_code = AuthService.reset_password(token, new_password)
        return jsonify(result), status_code
    except Exception as e:
        return jsonify({'error': f'Reset password error: {str(e)}'}), 500


@auth_bp.route('/accept-invite', methods=['POST'])
def accept_invite():
    """Accept invite: set password using token from invite email. No auth required."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        token = data.get('token')
        password = data.get('password')
        if not token or not password:
            return jsonify({'error': 'Token and password are required'}), 400
        result, status_code = AuthService.accept_invite(token, password)
        return jsonify(result), status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/profile', methods=['PATCH', 'POST'])
@require_auth
def update_profile(current_user):
    """Update current user's profile (username and/or email)."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        username = data.get('username')
        email = data.get('email')
        result, status_code = AuthService.update_profile(current_user, username=username, email=email)
        return jsonify(result), status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@auth_bp.route('/change-password', methods=['POST'])
@require_auth
def change_password(current_user):
    """Change current user's password. Requires current password."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        if not current_password or not new_password:
            return jsonify({'error': 'Current password and new password are required'}), 400
        result, status_code = AuthService.change_password(
            current_user, current_password, new_password
        )
        return jsonify(result), status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500

