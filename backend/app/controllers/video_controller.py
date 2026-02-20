"""
Video processing controller for handling video and image uploads and analysis.
"""
from flask import Blueprint, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from app.services.video_processing_service import VideoProcessingService
from app.repositories.camera_repository import CameraRepository
from app.middleware.auth_middleware import require_auth
from app.utils.validators import validate_video_file, validate_image_file
from app.config import Config
import os

video_bp = Blueprint('video', __name__, url_prefix='/api/videos')


@video_bp.route('/upload', methods=['POST'])
@require_auth
def upload_video(current_user):
    """Upload and process a video file."""
    if 'video' not in request.files:
        return jsonify({'error': 'No video file provided'}), 400
    
    file = request.files['video']
    camera_id = request.form.get('camera_id', type=int)
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not camera_id:
        return jsonify({'error': 'Camera ID is required'}), 400
    
    # Verify camera access
    camera = CameraRepository.find_by_id(camera_id)
    if not camera:
        return jsonify({'error': 'Camera not found'}), 404
    
    if not current_user.is_admin() and camera.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    # Validate file
    video_service = VideoProcessingService()
    if not video_service.validate_video_file(file.filename):
        return jsonify({'error': 'Invalid file type. Allowed: mp4, avi, mov, mkv, webm'}), 400
    
    try:
        # Save video
        filename = secure_filename(file.filename)
        video_path = video_service.save_video(file, filename)
        
        # Process video (this can be done asynchronously in production)
        results, status_code = video_service.process_video(video_path, camera_id)
        
        if status_code == 200:
            return jsonify({
                'message': 'Video processed successfully',
                'video_path': video_path,
                'results': results
            }), 200
        else:
            return jsonify(results), status_code
    
    except Exception as e:
        return jsonify({'error': f'Video processing failed: {str(e)}'}), 500


@video_bp.route('/process/<int:camera_id>', methods=['POST'])
@require_auth
def process_video_for_camera(camera_id, current_user):
    """Process an already uploaded video for a specific camera."""
    data = request.get_json()
    
    if not data or 'video_path' not in data:
        return jsonify({'error': 'Video path is required'}), 400
    
    video_path = data['video_path']
    
    # Verify camera access
    camera = CameraRepository.find_by_id(camera_id)
    if not camera:
        return jsonify({'error': 'Camera not found'}), 404
    
    if not current_user.is_admin() and camera.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    # Verify file exists
    if not os.path.exists(video_path):
        return jsonify({'error': 'Video file not found'}), 404
    
    try:
        video_service = VideoProcessingService()
        results, status_code = video_service.process_video(video_path, camera_id)
        return jsonify(results), status_code
    except Exception as e:
        return jsonify({'error': f'Video processing failed: {str(e)}'}), 500


@video_bp.route('/upload-image', methods=['POST'])
@require_auth
def upload_image(current_user):
    """Upload and process an image file."""
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400
    
    file = request.files['image']
    camera_id = request.form.get('camera_id', type=int)
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not camera_id:
        return jsonify({'error': 'Camera ID is required'}), 400
    
    # Verify camera access
    camera = CameraRepository.find_by_id(camera_id)
    if not camera:
        return jsonify({'error': 'Camera not found'}), 404
    
    if not current_user.is_admin() and camera.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    # Validate file
    if not validate_image_file(file.filename):
        return jsonify({'error': 'Invalid file type. Allowed: jpg, jpeg, png, gif'}), 400
    
    try:
        video_service = VideoProcessingService()
        # Save image
        filename = secure_filename(file.filename)
        image_path = video_service.save_image(file, filename)
        
        # Process image
        results, status_code = video_service.process_image(image_path, camera_id)
        
        if status_code == 200:
            return jsonify({
                'message': 'Image processed successfully',
                'image_path': image_path,
                'results': results
            }), 200
        else:
            return jsonify(results), status_code
    
    except Exception as e:
        return jsonify({'error': f'Image processing failed: {str(e)}'}), 500


@video_bp.route('/media/<path:filename>', methods=['GET'])
@require_auth
def get_media(current_user):
    """Serve uploaded media files."""
    try:
        return send_from_directory(Config.UPLOAD_FOLDER, filename)
    except Exception as e:
        return jsonify({'error': f'File not found: {str(e)}'}), 404

