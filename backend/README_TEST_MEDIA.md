# Test Media Creation

## Quick Setup

To create test images and videos for testing alerts:

```bash
# Activate virtual environment (if not already active)
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Run the test media generator
python create_test_media.py
```

This will create test files in `backend/test_media/` directory.

## Alternative: Download Sample Media

If you prefer to use real-world test media, you can download sample files:

### Test Images
- Download sample face images from: https://www.pexels.com/search/person/
- Or use any JPG/PNG images with faces

### Test Videos  
- Download sample videos from: https://www.pexels.com/videos/
- Look for videos with people walking, crowds, etc.
- Supported formats: MP4, AVI, MOV, MKV

## Using the Test Media

1. Start your backend and frontend servers
2. Login to the dashboard
3. Add a camera (if you haven't already)
4. Click "Upload Media" on the camera
5. Select a test image or video from `backend/test_media/`
6. Wait for processing
7. Check the Dashboard or Alerts page to see generated alerts

## What Gets Created

The script creates:
- `test_face_1.jpg` - Simple face image
- `test_no_mask_1.jpg` - Face without mask (triggers mask violation)
- `test_with_mask_1.jpg` - Face with mask
- `test_video_short.mp4` - 3-second test video
- `test_video_medium.mp4` - 5-second test video

Note: These are simple geometric test images. For more realistic testing, use actual photos/videos with real faces.

