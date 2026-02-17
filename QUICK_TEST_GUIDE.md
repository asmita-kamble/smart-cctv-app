# Quick Test Guide - Creating Alerts

This guide shows you how to quickly test the alert system with sample media files.

## Method 1: Generate Test Media (Easiest)

### Step 1: Generate Test Files

```bash
cd backend
./generate_test_media.sh
```

Or manually:
```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
python create_test_media.py
```

This creates test files in `backend/test_media/`:
- `test_face_1.jpg` - Basic face image
- `test_no_mask_1.jpg` - Face without mask (will trigger mask violation alert)
- `test_with_mask_1.jpg` - Face with mask
- `test_video_short.mp4` - 3-second test video
- `test_video_medium.mp4` - 5-second test video

### Step 2: Upload and Test

1. **Start Backend:**
   ```bash
   cd backend
   source venv/bin/activate
   python run.py
   ```

2. **Start Frontend:**
   ```bash
   cd frontend
   npm run dev
   ```

3. **Login and Add Camera:**
   - Go to http://localhost:3000
   - Login with admin account
   - Navigate to "Cameras" page
   - Click "Add Camera"
   - Enter name: "Test Camera"
   - Enter location: "Test Location"
   - Click "Create"

4. **Upload Test Media:**
   - Click "Upload Media" on your camera
   - Select `test_no_mask_1.jpg` (this should trigger a mask violation alert)
   - Wait for processing
   - You should see: "Image processed successfully! Alerts created: X"

5. **View Alerts:**
   - Go to "Dashboard" - you'll see recent alerts
   - Go to "Alerts" page - you'll see all alerts with details

## Method 2: Use Your Own Images/Videos

You can use any images or videos you have:

**Supported Image Formats:**
- JPG, JPEG, PNG, GIF

**Supported Video Formats:**
- MP4, AVI, MOV, MKV

**Recommended:**
- Use photos with clear faces for best detection
- Videos should be at least 3-5 seconds for activity detection
- File size limit: 1GB

## Expected Alert Types

### 1. Mask Violation Alert
- **Trigger:** Face detected without mask
- **Severity:** Medium
- **Test with:** `test_no_mask_1.jpg` or any photo of a person without a mask

### 2. Face Spoof Alert  
- **Trigger:** Detected fake/spoofed face
- **Severity:** High
- **Test with:** Images with suspicious face patterns

### 3. Suspicious Activity Alert
- **Trigger:** Unusual movement patterns in video
- **Severity:** High
- **Test with:** Videos with rapid or unusual movement

## Troubleshooting

### No Alerts Created
- Check backend console for errors
- Verify face detection models are loaded
- Try a different image/video file
- Check that the camera was created successfully

### Upload Fails
- Verify file size is under 1GB
- Check file extension is supported
- Ensure you're logged in and have camera access
- Check backend logs for specific error messages

### Processing Takes Long
- Video processing analyzes frames at intervals
- Large videos may take several minutes
- Use shorter videos (3-5 seconds) for quick testing

## Test File Locations

- **Generated test files:** `backend/test_media/`
- **Uploaded files:** `uploads/` (project root)

## Next Steps

After testing with generated files, try:
1. Using real photos/videos with actual faces
2. Testing different alert types
3. Checking alert details on the Alerts page
4. Resolving alerts to test the workflow

For more details, see `TEST_MEDIA_GUIDE.md`

