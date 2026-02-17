"""
Dashboard controller for admin dashboard and monitoring.
"""
from flask import Blueprint, jsonify
from app.services.alert_service import AlertService
from app.repositories.camera_repository import CameraRepository
from app.repositories.activity_repository import ActivityRepository
from app.middleware.auth_middleware import require_auth, require_admin

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')


@dashboard_bp.route('/overview', methods=['GET'])
@require_auth
@require_admin
def get_overview(current_user):
    """Get dashboard overview statistics (admin only)."""
    # Get camera statistics
    total_cameras = len(CameraRepository.find_all())
    active_cameras = len(CameraRepository.find_by_status('active'))
    
    # Get alert statistics
    alert_stats, _ = AlertService.get_alert_statistics()
    
    # Get recent activities count
    recent_activities = ActivityRepository.find_recent(limit=50)
    
    return jsonify({
        'cameras': {
            'total': total_cameras,
            'active': active_cameras,
            'inactive': total_cameras - active_cameras
        },
        'alerts': alert_stats,
        'recent_activities_count': len(recent_activities)
    }), 200


@dashboard_bp.route('/cameras', methods=['GET'])
@require_auth
@require_admin
def get_all_cameras(current_user):
    """Get all cameras for dashboard (admin only)."""
    cameras = CameraRepository.find_all()
    return jsonify({
        'cameras': [camera.to_dict() for camera in cameras],
        'count': len(cameras)
    }), 200

