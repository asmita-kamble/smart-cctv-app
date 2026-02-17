"""
Camera controller for managing surveillance cameras.
"""
from flask import Blueprint, request, jsonify, send_file, Response
from app.services.auth_service import AuthService
from app.repositories.camera_repository import CameraRepository
from app.middleware.auth_middleware import require_auth, require_admin
from app.services.streaming_service import streaming_service
import os

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
    rtsp_username = data.get('rtsp_username') or data.get('rtspUsername')
    rtsp_password = data.get('rtsp_password') or data.get('rtspPassword')
    rtsp_path = data.get('rtsp_path') or data.get('rtspPath')
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
            rtsp_username=rtsp_username,
            rtsp_password=rtsp_password,
            rtsp_path=rtsp_path,
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
        if 'rtsp_username' in data or 'rtspUsername' in data:
            camera.rtsp_username = data.get('rtsp_username') or data.get('rtspUsername')
        if 'rtsp_password' in data or 'rtspPassword' in data:
            camera.rtsp_password = data.get('rtsp_password') or data.get('rtspPassword')
        if 'rtsp_path' in data or 'rtspPath' in data:
            camera.rtsp_path = data.get('rtsp_path') or data.get('rtspPath')
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
    
    # Stop streaming if active
    streaming_service.stop_stream(camera_id)
    
    return jsonify({'message': 'Camera deleted successfully'}), 200


@camera_bp.route('/<int:camera_id>/stream/start', methods=['POST'])
@require_auth
def start_stream(camera_id, current_user):
    """Start RTSP stream for a camera."""
    camera = CameraRepository.find_by_id(camera_id)
    
    if not camera:
        return jsonify({'error': 'Camera not found'}), 404
    
    # Check access: admin or owner
    if not current_user.is_admin() and camera.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    if not camera.ip_address:
        return jsonify({'error': 'Camera IP address is required for streaming'}), 400
    
    # Get RTSP parameters from request (optional, overrides camera settings)
    data = request.get_json() or {}
    rtsp_port = data.get('rtsp_port', 554)
    
    # Use camera RTSP config if available, otherwise use request params or defaults
    rtsp_username = data.get('rtsp_username') or camera.rtsp_username
    rtsp_password = data.get('rtsp_password') or camera.rtsp_password
    rtsp_path = data.get('rtsp_path') or camera.rtsp_path or '/stream1'  # Default to /stream1 if not set
    
    # Build RTSP URL
    rtsp_url = streaming_service.build_rtsp_url(
        ip_address=camera.ip_address,
        port=rtsp_port,
        username=rtsp_username,
        password=rtsp_password,
        path=rtsp_path
    )
    
    # Start stream
    success = streaming_service.start_stream(camera_id, rtsp_url)
    
    if success:
        return jsonify({
            'message': 'Stream started successfully',
            'stream_url': f'/api/cameras/{camera_id}/stream/playlist.m3u8'
        }), 200
    else:
        return jsonify({'error': 'Failed to start stream. Check camera IP and RTSP settings.'}), 500


@camera_bp.route('/<int:camera_id>/stream/stop', methods=['POST'])
@require_auth
def stop_stream(camera_id, current_user):
    """Stop RTSP stream for a camera."""
    camera = CameraRepository.find_by_id(camera_id)
    
    if not camera:
        return jsonify({'error': 'Camera not found'}), 404
    
    # Check access: admin or owner
    if not current_user.is_admin() and camera.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    success = streaming_service.stop_stream(camera_id)
    
    if success:
        return jsonify({'message': 'Stream stopped successfully'}), 200
    else:
        return jsonify({'error': 'Failed to stop stream'}), 500


@camera_bp.route('/<int:camera_id>/stream/status', methods=['GET'])
@require_auth
def get_stream_status(camera_id, current_user):
    """Get streaming status for a camera."""
    camera = CameraRepository.find_by_id(camera_id)
    
    if not camera:
        return jsonify({'error': 'Camera not found'}), 404
    
    # Check access: admin or owner
    if not current_user.is_admin() and camera.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    is_active = streaming_service.is_stream_active(camera_id)
    
    return jsonify({
        'camera_id': camera_id,
        'streaming': is_active,
        'stream_url': f'/api/cameras/{camera_id}/stream/playlist.m3u8' if is_active else None
    }), 200


@camera_bp.route('/<int:camera_id>/stream/playlist.m3u8', methods=['GET'])
@require_auth
def get_hls_playlist(camera_id, current_user):
    """Serve HLS playlist file."""
    camera = CameraRepository.find_by_id(camera_id)
    
    if not camera:
        return jsonify({'error': 'Camera not found'}), 404
    
    # Check access: admin or owner
    if not current_user.is_admin() and camera.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    playlist_path = streaming_service.get_hls_playlist_path(camera_id)
    
    if not playlist_path or not playlist_path.exists():
        # Try to start stream automatically if IP is available
        if camera.ip_address:
            # Use camera RTSP config if available, otherwise use defaults
            rtsp_username = camera.rtsp_username
            rtsp_password = camera.rtsp_password
            rtsp_path = camera.rtsp_path or '/stream1'  # Default to /stream1 if not set
            
            rtsp_url = streaming_service.build_rtsp_url(
                ip_address=camera.ip_address,
                port=554,  # Default RTSP port
                username=rtsp_username,
                password=rtsp_password,
                path=rtsp_path
            )
            streaming_service.start_stream(camera_id, rtsp_url)
            playlist_path = streaming_service.get_hls_playlist_path(camera_id)
        
        if not playlist_path or not playlist_path.exists():
            return jsonify({'error': 'Stream not available. Please start the stream first.'}), 404
    
    # Read and modify playlist to fix segment URLs
    try:
        with open(playlist_path, 'r') as f:
            content = f.read()
        
        # Get base URL from request
        base_url = request.url_root.rstrip('/')
        
        # Replace segment paths with absolute API endpoints
        lines = content.split('\n')
        modified_lines = []
        for line in lines:
            if line.endswith('.ts') and not line.startswith('http'):
                # Convert relative path to absolute API endpoint
                segment_name = os.path.basename(line.strip())
                # Use absolute URL for segments
                modified_lines.append(f'{base_url}api/cameras/{camera_id}/stream/segment/{segment_name}')
            else:
                modified_lines.append(line)
        
        modified_content = '\n'.join(modified_lines)
        
        return Response(
            modified_content,
            mimetype='application/vnd.apple.mpegurl',
            headers={
                'Content-Type': 'application/vnd.apple.mpegurl',
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Access-Control-Allow-Origin': '*'
            }
        )
    except Exception as e:
        return jsonify({'error': f'Failed to read playlist: {str(e)}'}), 500


@camera_bp.route('/<int:camera_id>/stream/segment/<segment_name>', methods=['GET'])
@require_auth
def get_hls_segment(camera_id, current_user, segment_name):
    """Serve HLS segment file."""
    camera = CameraRepository.find_by_id(camera_id)
    
    if not camera:
        return jsonify({'error': 'Camera not found'}), 404
    
    # Check access: admin or owner
    if not current_user.is_admin() and camera.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    segment_path = streaming_service.get_hls_segment_path(camera_id, segment_name)
    
    if not segment_path or not segment_path.exists():
        return jsonify({'error': 'Segment not found'}), 404
    
    return send_file(
        str(segment_path),
        mimetype='video/mp2t',
        as_attachment=False,
        download_name=segment_name
    )

