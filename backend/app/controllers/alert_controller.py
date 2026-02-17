"""
Alert controller for managing security alerts.
"""
from flask import Blueprint, request, jsonify, send_from_directory
from app.services.alert_service import AlertService
from app.repositories.alert_repository import AlertRepository
from app.repositories.camera_repository import CameraRepository
from app.middleware.auth_middleware import require_auth, require_admin
from app.config import Config
import os
import json

alert_bp = Blueprint('alert', __name__, url_prefix='/api/alerts')


@alert_bp.route('', methods=['GET'])
@require_auth
def get_alerts(current_user):
    """Get alerts (filtered by user's cameras unless admin)."""
    camera_id = request.args.get('camera_id', type=int)
    status = request.args.get('status')
    severity = request.args.get('severity')
    limit = request.args.get('limit', type=int, default=100)
    offset = request.args.get('offset', type=int, default=0)
    
    if camera_id:
        # Check access
        from app.repositories.camera_repository import CameraRepository
        camera = CameraRepository.find_by_id(camera_id)
        if not camera:
            return jsonify({'error': 'Camera not found'}), 404
        if not current_user.is_admin() and camera.user_id != current_user.id:
            return jsonify({'error': 'Access denied'}), 403
        
        result, status_code = AlertService.get_alerts_by_camera(camera_id, limit, offset)
        return jsonify(result), status_code
    
    if status == 'pending':
        result, status_code = AlertService.get_pending_alerts(limit, offset)
        return jsonify(result), status_code
    
    if severity:
        result, status_code = AlertService.get_alerts_by_severity(severity, limit, offset)
        return jsonify(result), status_code
    
    # Get recent alerts
    result, status_code = AlertService.get_recent_alerts(limit)
    return jsonify(result), status_code


@alert_bp.route('/<int:alert_id>', methods=['GET'])
@require_auth
def get_alert(alert_id, current_user):
    """Get alert by ID."""
    result, status_code = AlertService.get_alert(alert_id)
    return jsonify(result), status_code


@alert_bp.route('/<int:alert_id>/resolve', methods=['POST'])
@require_auth
def resolve_alert(alert_id, current_user):
    """Resolve an alert."""
    result, status_code = AlertService.resolve_alert(alert_id)
    return jsonify(result), status_code


@alert_bp.route('/statistics', methods=['GET'])
@require_auth
@require_admin
def get_alert_statistics(current_user):
    """Get alert statistics for dashboard (admin only)."""
    result, status_code = AlertService.get_alert_statistics()
    return jsonify(result), status_code


@alert_bp.route('/<int:alert_id>/image', methods=['GET'])
@require_auth
def get_alert_image(alert_id, current_user):
    """Serve the image file associated with an alert."""
    alert = AlertRepository.find_by_id(alert_id)
    if not alert:
        return jsonify({'error': 'Alert not found'}), 404
    
    # Check access: admin or camera owner
    camera = CameraRepository.find_by_id(alert.camera_id)
    if not camera:
        return jsonify({'error': 'Camera not found'}), 404
    
    if not current_user.is_admin() and camera.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    # Extract image or video path from metadata
    file_path = None
    if alert.meta_data:
        try:
            metadata = json.loads(alert.meta_data)
            file_path = metadata.get('image_path') or metadata.get('video_path')
        except (json.JSONDecodeError, TypeError):
            pass
    
    if not file_path:
        return jsonify({'error': 'No media file associated with this alert'}), 404
    
    # Check if file exists
    if not os.path.exists(file_path):
        return jsonify({'error': 'Media file not found'}), 404
    
    try:
        # Get directory and filename
        directory = os.path.dirname(file_path)
        filename = os.path.basename(file_path)
        
        return send_from_directory(directory, filename)
    except Exception as e:
        return jsonify({'error': f'Failed to serve media file: {str(e)}'}), 500

