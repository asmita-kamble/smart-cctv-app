"""
Activity controller for managing detected activities.
"""
from flask import Blueprint, request, jsonify, send_from_directory
from app.repositories.activity_repository import ActivityRepository
from app.repositories.camera_repository import CameraRepository
from app.middleware.auth_middleware import require_auth
from app.config import Config
import os
import json

activity_bp = Blueprint('activity', __name__, url_prefix='/api/activities')


@activity_bp.route('', methods=['GET'])
@require_auth
def get_activities(current_user):
    """Get activities (filtered by user's cameras unless admin)."""
    camera_id = request.args.get('camera_id', type=int)
    activity_type = request.args.get('activity_type')
    limit = request.args.get('limit', type=int, default=100)
    offset = request.args.get('offset', type=int, default=0)
    
    if camera_id:
        # Check access
        camera = CameraRepository.find_by_id(camera_id)
        if not camera:
            return jsonify({'error': 'Camera not found'}), 404
        if not current_user.is_admin() and camera.user_id != current_user.id:
            return jsonify({'error': 'Access denied'}), 403
        
        if activity_type:
            activities = ActivityRepository.find_by_camera_and_type(camera_id, activity_type, limit, offset)
        else:
            activities = ActivityRepository.find_by_camera_id(camera_id, limit, offset)
    elif activity_type:
        activities = ActivityRepository.find_by_type(activity_type, limit, offset)
    else:
        activities = ActivityRepository.find_recent(limit, offset)
    
    return jsonify({
        'activities': [activity.to_dict() for activity in activities],
        'count': len(activities)
    }), 200


@activity_bp.route('/<int:activity_id>', methods=['GET'])
@require_auth
def get_activity(activity_id, current_user):
    """Get activity by ID."""
    activity = ActivityRepository.find_by_id(activity_id)
    
    if not activity:
        return jsonify({'error': 'Activity not found'}), 404
    
    # Check access
    camera = CameraRepository.find_by_id(activity.camera_id)
    if not current_user.is_admin() and camera.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    return jsonify({'activity': activity.to_dict()}), 200


@activity_bp.route('/<int:activity_id>/image', methods=['GET'])
@require_auth
def get_activity_image(activity_id, current_user):
    """Serve the image file associated with an activity."""
    activity = ActivityRepository.find_by_id(activity_id)
    if not activity:
        return jsonify({'error': 'Activity not found'}), 404
    
    # Check access: admin or camera owner
    camera = CameraRepository.find_by_id(activity.camera_id)
    if not camera:
        return jsonify({'error': 'Camera not found'}), 404
    
    if not current_user.is_admin() and camera.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    # Extract image or video path from metadata
    file_path = None
    if activity.meta_data:
        try:
            metadata = json.loads(activity.meta_data)
            file_path = metadata.get('image_path') or metadata.get('video_path')
        except (json.JSONDecodeError, TypeError):
            pass
    
    if not file_path:
        return jsonify({'error': 'No media file associated with this activity'}), 404
    
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

