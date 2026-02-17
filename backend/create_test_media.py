"""
Script to create test images and videos for testing the Smart CCTV system.
This script generates sample test media files that can be used to trigger alerts.
"""
import os
import cv2
import numpy as np
from datetime import datetime

# Create test media directory
TEST_MEDIA_DIR = os.path.join(os.path.dirname(__file__), 'test_media')
os.makedirs(TEST_MEDIA_DIR, exist_ok=True)


def create_test_image_with_face(filename='test_face.jpg', width=640, height=480):
    """Create a simple test image with a face-like shape."""
    # Create a blank image
    img = np.zeros((height, width, 3), dtype=np.uint8)
    img.fill(200)  # Light gray background
    
    # Draw a simple face (circle for head, ovals for eyes, line for mouth)
    center_x, center_y = width // 2, height // 2
    
    # Head (circle)
    cv2.circle(img, (center_x, center_y), 100, (220, 180, 140), -1)  # Skin color
    
    # Eyes (two ovals)
    cv2.ellipse(img, (center_x - 30, center_y - 20), (15, 20), 0, 0, 360, (50, 50, 50), -1)  # Left eye
    cv2.ellipse(img, (center_x + 30, center_y - 20), (15, 20), 0, 0, 360, (50, 50, 50), -1)  # Right eye
    
    # Nose (small triangle)
    pts = np.array([[center_x, center_y], [center_x - 10, center_y + 20], [center_x + 10, center_y + 20]], np.int32)
    cv2.fillPoly(img, [pts], (180, 140, 100))
    
    # Mouth (arc)
    cv2.ellipse(img, (center_x, center_y + 30), (30, 15), 0, 0, 180, (100, 50, 50), 3)
    
    # Add text label
    cv2.putText(img, 'Test Face Image', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    cv2.putText(img, f'Created: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', 
                (10, height - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 100, 100), 1)
    
    filepath = os.path.join(TEST_MEDIA_DIR, filename)
    cv2.imwrite(filepath, img)
    print(f"Created test image: {filepath}")
    return filepath


def create_test_image_without_mask(filename='test_no_mask.jpg', width=640, height=480):
    """Create a test image showing a face without a mask."""
    img = create_test_image_with_face(filename, width, height)
    # Add text indicating no mask
    img_array = cv2.imread(img)
    cv2.putText(img_array, 'NO MASK DETECTED', (10, 60), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    cv2.imwrite(img, img_array)
    print(f"Created test image (no mask): {img}")
    return img


def create_test_image_with_mask(filename='test_with_mask.jpg', width=640, height=480):
    """Create a test image showing a face with a mask."""
    # Create base face image
    img = np.zeros((height, width, 3), dtype=np.uint8)
    img.fill(200)
    
    center_x, center_y = width // 2, height // 2
    
    # Head
    cv2.circle(img, (center_x, center_y), 100, (220, 180, 140), -1)
    
    # Eyes
    cv2.ellipse(img, (center_x - 30, center_y - 20), (15, 20), 0, 0, 360, (50, 50, 50), -1)
    cv2.ellipse(img, (center_x + 30, center_y - 20), (15, 20), 0, 0, 360, (50, 50, 50), -1)
    
    # Mask (blue rectangle covering mouth area)
    cv2.rectangle(img, (center_x - 50, center_y + 10), (center_x + 50, center_y + 50), (0, 100, 200), -1)
    cv2.rectangle(img, (center_x - 50, center_y + 10), (center_x + 50, center_y + 50), (0, 150, 255), 2)
    
    # Add text
    cv2.putText(img, 'Test Face with Mask', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    cv2.putText(img, f'Created: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', 
                (10, height - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 100, 100), 1)
    
    filepath = os.path.join(TEST_MEDIA_DIR, filename)
    cv2.imwrite(filepath, img)
    print(f"Created test image (with mask): {filepath}")
    return filepath


def create_test_video(filename='test_video.mp4', duration_seconds=5, fps=30, width=640, height=480):
    """Create a simple test video with moving content."""
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    filepath = os.path.join(TEST_MEDIA_DIR, filename)
    out = cv2.VideoWriter(filepath, fourcc, fps, (width, height))
    
    total_frames = duration_seconds * fps
    
    for frame_num in range(total_frames):
        # Create a frame with moving content
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        frame.fill(150)
        
        # Moving circle (simulates movement)
        x = int(width // 2 + 100 * np.sin(2 * np.pi * frame_num / total_frames))
        y = int(height // 2 + 50 * np.cos(2 * np.pi * frame_num / total_frames))
        
        # Draw moving object
        cv2.circle(frame, (x, y), 50, (0, 255, 0), -1)
        
        # Add face-like shape that moves
        face_x = int(width // 2 + 50 * np.cos(2 * np.pi * frame_num / total_frames))
        face_y = int(height // 2 + 30 * np.sin(2 * np.pi * frame_num / total_frames))
        
        # Head
        cv2.circle(frame, (face_x, face_y), 40, (220, 180, 140), -1)
        # Eyes
        cv2.circle(frame, (face_x - 15, face_y - 10), 5, (0, 0, 0), -1)
        cv2.circle(frame, (face_x + 15, face_y - 10), 5, (0, 0, 0), -1)
        # Mouth
        cv2.ellipse(frame, (face_x, face_y + 10), (20, 10), 0, 0, 180, (100, 50, 50), 2)
        
        # Add frame number and timestamp
        cv2.putText(frame, f'Frame: {frame_num}/{total_frames}', (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(frame, f'Time: {frame_num/fps:.2f}s', (10, 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(frame, 'Test Video for CCTV System', (10, height - 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        
        out.write(frame)
    
    out.release()
    print(f"Created test video: {filepath} ({duration_seconds}s, {fps}fps)")
    return filepath


def create_all_test_media():
    """Create all test media files."""
    print("Creating test media files...")
    print("=" * 50)
    
    # Create test images
    create_test_image_with_face('test_face_1.jpg')
    create_test_image_without_mask('test_no_mask_1.jpg')
    create_test_image_with_mask('test_with_mask_1.jpg')
    
    # Create additional variations
    create_test_image_with_face('test_face_2.jpg', 800, 600)
    create_test_image_without_mask('test_no_mask_2.jpg', 800, 600)
    
    # Create test videos
    create_test_video('test_video_short.mp4', duration_seconds=3, fps=15)
    create_test_video('test_video_medium.mp4', duration_seconds=5, fps=30)
    
    print("=" * 50)
    print(f"All test media files created in: {TEST_MEDIA_DIR}")
    print("\nYou can now upload these files through the Cameras page to test alert generation.")


if __name__ == '__main__':
    create_all_test_media()

