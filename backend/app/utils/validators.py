"""
Validation utilities for input validation.
"""
import re

# Max lengths for DB columns
EMAIL_MAX_LENGTH = 120


def validate_email(email):
    """
    Validate email format.
    Returns True if valid, False otherwise.
    """
    if email is None or not isinstance(email, str):
        return False
    email = email.strip()
    if not email or len(email) > EMAIL_MAX_LENGTH:
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def normalize_email(email):
    """Normalize email: strip whitespace and convert to lowercase."""
    if email is None or not isinstance(email, str):
        return ''
    return email.strip().lower()[:EMAIL_MAX_LENGTH]


def validate_password(password):
    """Validate password strength."""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit"
    return True, "Password is valid"


def validate_video_file(filename):
    """Validate video file extension."""
    allowed_extensions = {'mp4', 'avi', 'mov', 'mkv', 'webm'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


def validate_image_file(filename):
    """Validate image file extension."""
    allowed_extensions = {'jpg', 'jpeg', 'png', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

