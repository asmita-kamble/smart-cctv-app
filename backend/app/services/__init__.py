"""Service modules for business logic."""
from app.services.auth_service import AuthService
from app.services.face_detection_service import FaceDetectionService
from app.services.mask_detection_service import MaskDetectionService
from app.services.activity_detection_service import ActivityDetectionService
from app.services.alert_service import AlertService
from app.services.video_processing_service import VideoProcessingService
from app.services.streaming_service import StreamingService, streaming_service

__all__ = [
    'AuthService',
    'FaceDetectionService',
    'MaskDetectionService',
    'ActivityDetectionService',
    'AlertService',
    'VideoProcessingService',
    'StreamingService',
    'streaming_service'
]

