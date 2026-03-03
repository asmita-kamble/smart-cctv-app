"""
User Management service for admin operations: invite users, list users, deactivate/activate.
"""
import secrets
from datetime import datetime, timedelta
from typing import Dict, Tuple, List, Optional
from flask import current_app

from app.repositories.user_repository import UserRepository
from app.models.user import User
from app.utils.validators import validate_email, validate_password, normalize_email
from app.utils.database import db
from app.services.email_service import EmailService


class UserManagementService:
    """Service for admin user management: invite, list, deactivate, reactivate."""

    INVITE_TOKEN_EXPIRY_DAYS = 7

    @staticmethod
    def list_users(limit: int = 100, offset: int = 0) -> Tuple[Dict, int]:
        """
        List all users with optional pagination. Admin only.

        Returns:
            Tuple of (dict with users and total, status_code)
        """
        users = UserRepository.find_all(limit=limit, offset=offset)
        # Get total count without limit
        total = User.query.count()
        return {
            'users': [u.to_dict() for u in users],
            'total': total,
            'limit': limit,
            'offset': offset,
        }, 200

    @staticmethod
    def invite_user(
        email: str,
        username: str,
        role: str,
        inviter: User,
    ) -> Tuple[Dict, int]:
        """
        Invite a new user (or admin). Creates user with invite token and sends email.
        Admin only.

        Args:
            email: Invitee email
            username: Invitee username
            role: 'user' or 'admin'
            inviter: The admin user sending the invite

        Returns:
            Tuple of (result_dict, status_code)
        """
        email = normalize_email(email)
        if not email:
            return {'error': 'Email is required'}, 400
        if not validate_email(email):
            return {'error': 'Invalid email format'}, 400
        if role not in ('user', 'admin'):
            return {'error': 'Role must be "user" or "admin"'}, 400
        if not username or not username.strip():
            return {'error': 'Username is required'}, 400
        username = username.strip()
        if len(username) > 80:
            return {'error': 'Username too long'}, 400

        if UserRepository.exists_by_email(email):
            return {'error': 'A user with this email already exists'}, 409
        if UserRepository.exists_by_username(username):
            return {'error': 'Username already taken'}, 409

        temp_password = secrets.token_urlsafe(24)
        invite_token = secrets.token_urlsafe(32)
        invite_token_expires = datetime.utcnow() + timedelta(days=UserManagementService.INVITE_TOKEN_EXPIRY_DAYS)

        try:
            user = UserRepository.create_invited(
                email=email,
                username=username,
                role=role,
                temp_password=temp_password,
                invite_token=invite_token,
                invite_token_expires=invite_token_expires,
            )
            frontend_url = current_app.config.get('FRONTEND_URL', 'http://localhost:3000').rstrip('/')
            invite_url = f"{frontend_url}/accept-invite?token={invite_token}"
            inviter_name = inviter.username or inviter.email or 'An admin'
            email_result, email_status = EmailService.send_invite_email(
                user_email=user.email,
                username=user.username,
                invite_url=invite_url,
                inviter_name=inviter_name,
                role=user.role,
            )
            if email_status != 200:
                print(f"Failed to send invite email: {email_result.get('error', 'Unknown error')}")
            return {
                'message': 'Invitation sent. The user will receive an email to set their password.',
                'user': user.to_dict(),
            }, 201
        except Exception as e:
            db.session.rollback()
            return {'error': f'Invite failed: {str(e)}'}, 500

    @staticmethod
    def deactivate_user(user_id: int, current_admin: User) -> Tuple[Dict, int]:
        """Deactivate a user by ID. Admin only. Cannot deactivate self."""
        if user_id == current_admin.id:
            return {'error': 'You cannot deactivate your own account'}, 400
        user = UserRepository.find_by_id(user_id)
        if not user:
            return {'error': 'User not found'}, 404
        UserRepository.set_active(user, False)
        return {'message': 'User deactivated', 'user': user.to_dict()}, 200

    @staticmethod
    def reactivate_user(user_id: int) -> Tuple[Dict, int]:
        """Reactivate a user by ID. Admin only."""
        user = UserRepository.find_by_id(user_id)
        if not user:
            return {'error': 'User not found'}, 404
        UserRepository.set_active(user, True)
        return {'message': 'User reactivated', 'user': user.to_dict()}, 200
