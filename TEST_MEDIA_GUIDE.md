# Test Media Guide

This guide explains how to create and use test images and videos to test the Smart CCTV alert system.

## Quick Start

### Option 1: Generate Test Media (Recommended)

Run the test media generation script:

```bash
cd backend
python create_test_media.py
```

This will create test images and videos in `backend/test_media/` directory:
- `test_face_1.jpg` - Simple face image
- `test_no_mask_1.jpg` - Face without mask (should trigger mask violation alert)
- `test_with_mask_1.jpg` - Face with mask
- `test_video_short.mp4` - 3-second test video
- `test_video_medium.mp4` - 5-second test video

### Option 2: Use Your Own Media Files

You can use any images or videos you have. The system supports:

**Images:**
- JPG, JPEG, PNG, GIF
- Recommended size: 640x480 or larger

**Videos:**
- MP4, AVI, MOV, MKV
- Any resolution and duration

## How to Test Alerts

1. **Start the Backend:**
   ```bash
   cd backend
   python run.py
   ```

2. **Start the Frontend:**
   ```bash
   cd frontend
   npm run dev
   ```

3. **Login to the Dashboard:**
   - Navigate to http://localhost:3000
   - Login with your admin account

4. **Add a Camera:**
   - Go to the "Cameras" page
   - Click "Add Camera"
   - Enter a name (e.g., "Test Camera 1")
   - Enter a location (e.g., "Main Entrance")
   - Click "Create"

5. **Upload Test Media:**
   - Click "Upload Media" on the camera you just created
   - Select a test image or video file
   - Wait for processing to complete
   - You should see a success message with the number of alerts created

6. **View Alerts:**
   - Go to the "Dashboard" to see recent alerts
   - Go to the "Alerts" page to see all alerts
   - Alerts will show:
     - Alert type (mask_violation, face_spoof, suspicious_activity)
     - Severity level (low, medium, high, critical)
     - Camera name
     - Timestamp

## Expected Alert Types

### Mask Violation Alert
- **Trigger:** Face detected without a mask
- **Severity:** Medium
- **Test File:** `test_no_mask_1.jpg` or `test_no_mask_2.jpg`

### Face Spoof Alert
- **Trigger:** Detected spoofed face (fake face detection)
- **Severity:** High
- **Test File:** Any image with suspicious face patterns

### Suspicious Activity Alert
- **Trigger:** Unusual movement or activity patterns in video
- **Severity:** High
- **Test File:** Videos with rapid movement or unusual patterns

## Test Media File Locations

Generated test files are saved in:
```
backend/test_media/
```

Uploaded files (from the web interface) are saved in:
```
uploads/
```

## Troubleshooting

### No Alerts Created
- Make sure the face detection models are properly initialized
- Check backend logs for processing errors
- Verify the image/video file is valid and readable

### Processing Takes Too Long
- Video processing analyzes frames at intervals (every 30th frame by default)
- Large videos may take several minutes
- Consider using shorter test videos (3-5 seconds) for quick testing

### File Upload Fails
- Check file size (max 1GB by default)
- Verify file extension is supported
- Ensure camera exists and you have access to it

## Advanced Testing

### Create Custom Test Images

You can modify `create_test_media.py` to create custom test scenarios:

```python
# Create image with specific characteristics
img = create_test_image_with_face('custom_test.jpg', width=1920, height=1080)
```

### Download Real Test Videos

For more realistic testing, you can download sample videos from:
- [Pexels Videos](https://www.pexels.com/videos/) - Free stock videos
- [Pixabay Videos](https://pixabay.com/videos/) - Free stock videos

Look for videos with:
- People walking
- Crowded scenes
- Indoor/outdoor surveillance-like footage

## Notes

- Test images are simple geometric shapes that may not trigger all detection features
- For production testing, use real images/videos with actual faces
- The face detection and mask detection services use ML models that work best with real human faces
- Test videos are basic animations; real videos will provide better testing results

