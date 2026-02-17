"""
AllowedPerson controller for managing allowed person images for cameras.
"""
from flask import Blueprint, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from app.repositories.allowed_person_repository import AllowedPersonRepository
from app.repositories.camera_repository import CameraRepository
from app.middleware.auth_middleware import require_auth
from app.utils.validators import validate_image_file
from app.config import Config
import os
from datetime import datetime

allowed_person_bp = Blueprint('allowed_person', __name__, url_prefix='/api/cameras')


@allowed_person_bp.route('/<int:camera_id>/allowed-persons', methods=['POST'])
@require_auth
def upload_allowed_person_image(camera_id, current_user):
    """Upload an allowed person image for a camera."""
    # Verify camera access
    camera = CameraRepository.find_by_id(camera_id)
    if not camera:
        return jsonify({'error': 'Camera not found'}), 404
    
    if not current_user.is_admin() and camera.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Validate file
    if not validate_image_file(file.filename):
        return jsonify({'error': 'Invalid file type. Allowed: jpg, jpeg, png, gif'}), 400
    
    try:
        # Create allowed_persons directory if it doesn't exist
        allowed_persons_dir = os.path.join(Config.UPLOAD_FOLDER, 'allowed_persons')
        os.makedirs(allowed_persons_dir, exist_ok=True)
        
        # Generate unique filename
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        safe_filename = secure_filename(file.filename)
        filename = f"{camera_id}_{timestamp}_{safe_filename}"
        filepath = os.path.join(allowed_persons_dir, filename)
        
        # Save file
        file.save(filepath)
        
        # Get optional name from form data
        name = request.form.get('name', '')
        
        # Create database record
        allowed_person = AllowedPersonRepository.create(
            camera_id=camera_id,
            image_path=filepath,
            name=name if name else None
        )
        
        return jsonify({
            'message': 'Allowed person image uploaded successfully',
            'allowed_person': allowed_person.to_dict()
        }), 201
    
    except Exception as e:
        return jsonify({'error': f'Failed to upload image: {str(e)}'}), 500


@allowed_person_bp.route('/<int:camera_id>/allowed-persons', methods=['GET'])
@require_auth
def get_allowed_persons(camera_id, current_user):
    """Get all allowed persons for a camera."""
    # Verify camera access
    camera = CameraRepository.find_by_id(camera_id)
    if not camera:
        return jsonify({'error': 'Camera not found'}), 404
    
    if not current_user.is_admin() and camera.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        allowed_persons = AllowedPersonRepository.find_by_camera_id(camera_id)
        return jsonify({
            'allowed_persons': [ap.to_dict() for ap in allowed_persons],
            'count': len(allowed_persons)
        }), 200
    except Exception as e:
        return jsonify({'error': f'Failed to get allowed persons: {str(e)}'}), 500


@allowed_person_bp.route('/<int:camera_id>/allowed-persons/<int:allowed_person_id>', methods=['DELETE'])
@require_auth
def delete_allowed_person(camera_id, allowed_person_id, current_user):
    """Delete an allowed person image."""
    # Verify camera access
    camera = CameraRepository.find_by_id(camera_id)
    if not camera:
        return jsonify({'error': 'Camera not found'}), 404
    
    if not current_user.is_admin() and camera.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    # Verify allowed person belongs to camera
    allowed_person = AllowedPersonRepository.find_by_id(allowed_person_id)
    if not allowed_person:
        return jsonify({'error': 'Allowed person not found'}), 404
    
    if allowed_person.camera_id != camera_id:
        return jsonify({'error': 'Allowed person does not belong to this camera'}), 400
    
    try:
        # Delete file if it exists
        if os.path.exists(allowed_person.image_path):
            os.remove(allowed_person.image_path)
        
        # Delete database record
        AllowedPersonRepository.delete(allowed_person_id)
        
        return jsonify({'message': 'Allowed person deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': f'Failed to delete allowed person: {str(e)}'}), 500


@allowed_person_bp.route('/<int:camera_id>/allowed-persons/<int:allowed_person_id>/image', methods=['GET'])
@require_auth
def get_allowed_person_image(camera_id, allowed_person_id, current_user):
    """Serve an allowed person image file."""
    # Verify camera access
    camera = CameraRepository.find_by_id(camera_id)
    if not camera:
        return jsonify({'error': 'Camera not found'}), 404
    
    if not current_user.is_admin() and camera.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    # Verify allowed person belongs to camera
    allowed_person = AllowedPersonRepository.find_by_id(allowed_person_id)
    if not allowed_person:
        return jsonify({'error': 'Allowed person not found'}), 404
    
    if allowed_person.camera_id != camera_id:
        return jsonify({'error': 'Allowed person does not belong to this camera'}), 400
    
    try:
        # Check if file exists
        if not os.path.exists(allowed_person.image_path):
            return jsonify({'error': 'Image file not found'}), 404
        
        # Get directory and filename
        directory = os.path.dirname(allowed_person.image_path)
        filename = os.path.basename(allowed_person.image_path)
        
        return send_from_directory(directory, filename)
    except Exception as e:
        return jsonify({'error': f'Failed to serve image: {str(e)}'}), 500

