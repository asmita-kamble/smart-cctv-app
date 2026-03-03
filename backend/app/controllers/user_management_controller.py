"""
User Management controller for admin: list users, invite, deactivate, reactivate.
"""
from flask import Blueprint, request, jsonify
from app.services.user_management_service import UserManagementService
from app.middleware.auth_middleware import require_admin

users_bp = Blueprint('users', __name__, url_prefix='/api/users')


@users_bp.route('', methods=['GET'])
@require_admin
def list_users(current_user):
    """List all users with optional pagination. Admin only."""
    try:
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        limit = min(max(1, limit), 500)
        offset = max(0, offset)
        result, status_code = UserManagementService.list_users(limit=limit, offset=offset)
        return jsonify(result), status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@users_bp.route('/invite', methods=['POST'])
@require_admin
def invite_user(current_user):
    """Invite a new user or admin. Admin only."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        email = data.get('email')
        username = data.get('username')
        role = data.get('role', 'user')
        if not email or not username:
            return jsonify({'error': 'Email and username are required'}), 400
        result, status_code = UserManagementService.invite_user(
            email=email,
            username=username,
            role=role,
            inviter=current_user,
        )
        return jsonify(result), status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@users_bp.route('/<int:user_id>/deactivate', methods=['PATCH', 'POST'])
@require_admin
def deactivate_user(user_id, current_user):
    """Deactivate a user. Admin only."""
    result, status_code = UserManagementService.deactivate_user(user_id, current_user)
    return jsonify(result), status_code


@users_bp.route('/<int:user_id>/activate', methods=['PATCH', 'POST'])
@require_admin
def reactivate_user(user_id, current_user):
    """Reactivate a user. Admin only."""
    result, status_code = UserManagementService.reactivate_user(user_id)
    return jsonify(result), status_code
