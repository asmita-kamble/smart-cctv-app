"""
Camera controller for managing surveillance cameras.
"""
from flask import Blueprint, request, jsonify
from app.services.auth_service import AuthService
from app.repositories.camera_repository import CameraRepository
from app.middleware.auth_middleware import require_auth, require_admin

camera_bp = Blueprint('camera', __name__, url_prefix='/api/cameras')


@camera_bp.route('', methods=['POST'])
@require_auth
def create_camera(current_user):
    """Create a new camera."""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    name = data.get('name')
    location = data.get('location')
    ip_address = data.get('ip_address') or data.get('ip')  # Support both 'ip' and 'ip_address'
    is_restricted_zone = data.get('is_restricted_zone', False)
    status = data.get('status', 'active')
    
    if not name or not location:
        return jsonify({'error': 'Name and location are required'}), 400
    
    # Check for duplicate name
    existing_camera = CameraRepository.find_by_name(name)
    if existing_camera:
        return jsonify({'error': 'Camera name already exists. Please choose a different name.'}), 400
    
    try:
        camera = CameraRepository.create(
            name=name,
            location=location,
            user_id=current_user.id,
            ip_address=ip_address,
            is_restricted_zone=is_restricted_zone,
            status=status
        )
        return jsonify({
            'message': 'Camera created successfully',
            'camera': camera.to_dict()
        }), 201
    except Exception as e:
        return jsonify({'error': f'Failed to create camera: {str(e)}'}), 500


@camera_bp.route('', methods=['GET'])
@require_auth
def get_cameras(current_user):
    """Get cameras (all for admin, own for regular users)."""
    limit = request.args.get('limit', type=int)
    offset = request.args.get('offset', type=int, default=0)
    
    if current_user.is_admin():
        cameras = CameraRepository.find_all(limit, offset)
    else:
        cameras = CameraRepository.find_by_user_id(current_user.id, limit, offset)
    
    return jsonify({
        'cameras': [camera.to_dict() for camera in cameras],
        'count': len(cameras)
    }), 200


@camera_bp.route('/<int:camera_id>', methods=['GET'])
@require_auth
def get_camera(camera_id, current_user):
    """Get camera by ID."""
    camera = CameraRepository.find_by_id(camera_id)
    
    if not camera:
        return jsonify({'error': 'Camera not found'}), 404
    
    # Check access: admin or owner
    if not current_user.is_admin() and camera.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    return jsonify({'camera': camera.to_dict()}), 200


@camera_bp.route('/<int:camera_id>', methods=['PUT'])
@require_auth
def update_camera(camera_id, current_user):
    """Update camera."""
    camera = CameraRepository.find_by_id(camera_id)
    
    if not camera:
        return jsonify({'error': 'Camera not found'}), 404
    
    # Check access: admin or owner
    if not current_user.is_admin() and camera.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    data = request.get_json()
    if data:
        # Check for duplicate name if name is being updated
        if 'name' in data and data['name']:
            new_name = data['name'].strip()
            if new_name != camera.name:
                existing_camera = CameraRepository.find_by_name(new_name, exclude_id=camera_id)
                if existing_camera:
                    return jsonify({'error': 'Camera name already exists. Please choose a different name.'}), 400
            camera.name = new_name
        if 'location' in data:
            camera.location = data['location']
        if 'ip_address' in data or 'ip' in data:
            camera.ip_address = data.get('ip_address') or data.get('ip')
        if 'is_restricted_zone' in data:
            camera.is_restricted_zone = data['is_restricted_zone']
        if 'status' in data:
            camera.status = data['status']
        
        try:
            CameraRepository.update(camera)
            return jsonify({
                'message': 'Camera updated successfully',
                'camera': camera.to_dict()
            }), 200
        except Exception as e:
            return jsonify({'error': f'Failed to update camera: {str(e)}'}), 500
    
    return jsonify({'error': 'No data provided'}), 400


@camera_bp.route('/<int:camera_id>', methods=['DELETE'])
@require_auth
def delete_camera(camera_id, current_user):
    """Delete camera."""
    camera = CameraRepository.find_by_id(camera_id)
    
    if not camera:
        return jsonify({'error': 'Camera not found'}), 404
    
    # Check access: admin or owner
    if not current_user.is_admin() and camera.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    CameraRepository.delete(camera_id)
    return jsonify({'message': 'Camera deleted successfully'}), 200

