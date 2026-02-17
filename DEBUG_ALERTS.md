# Debugging Alert Creation

## Issue: Alerts Not Being Created

If alerts are not being created when uploading images/videos, follow these debugging steps:

## Changes Made

1. **Enhanced Logging**: Added detailed console logging throughout the processing pipeline
2. **Error Handling**: Added try-catch blocks around all detection and alert creation steps
3. **Fallback Alert**: Always creates at least one alert per image upload (for testing)
4. **Better Error Messages**: More descriptive error messages in responses

## How to Debug

### Step 1: Check Backend Logs

When you upload an image, watch the backend console. You should see logs like:

```
Processing image: /path/to/image.jpg
Image shape: (480, 640, 3)
Faces detected: 0
Mask detection - faces: 0, compliance: 1.0
No alerts created yet - creating default test alert
AlertService.create_alert called: camera_id=1, type=image_processed, severity=low
Camera found: Test Camera (ID: 1)
Alert created successfully: ID=5, type=image_processed
Created default test alert: 5
Image processing complete: {...}
```

### Step 2: Check What's Happening

**If you see "Faces detected: 0":**
- The face detection library (`face_recognition`) didn't find any faces
- This is normal for simple geometric test images
- A test alert will still be created

**If you see errors:**
- Check the error message and traceback
- Common issues:
  - `face_recognition` not installed properly
  - Database connection issues
  - Camera not found

### Step 3: Test with Real Images

The `face_recognition` library works best with:
- Clear, well-lit photos
- Front-facing faces
- Good resolution (at least 640x480)
- Real human faces (not geometric shapes)

### Step 4: Verify Alerts in Database

Check if alerts are being created in the database:

```sql
SELECT * FROM alerts ORDER BY created_at DESC LIMIT 10;
```

Or check via the API:
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:5001/api/alerts
```

## Expected Behavior

### For Test Images (Geometric Shapes)
- **Faces detected:** 0 (expected - simple shapes aren't recognized as faces)
- **Alerts created:** 1 (test alert will be created)
- **Alert type:** `image_processed`
- **Severity:** `low`

### For Real Images with Faces
- **Faces detected:** 1 or more
- **Alerts created:** 
  - 1+ if mask violations detected
  - 1+ if spoofed faces detected
  - 1 default alert if no violations but faces detected

### For Real Images with Masked Faces
- **Faces detected:** 1 or more
- **Mask violations:** 0 (if masks detected properly)
- **Alerts created:** 1 (default test alert)

## Troubleshooting

### No Alerts Created at All

1. **Check backend logs** for errors
2. **Verify camera exists:**
   ```bash
   curl -H "Authorization: Bearer TOKEN" http://localhost:5001/api/cameras
   ```
3. **Check database connection:**
   - Ensure PostgreSQL is running
   - Check database credentials in `.env`

### Alerts Created But Not Showing in UI

1. **Check frontend console** for errors
2. **Verify API response:**
   ```bash
   curl -H "Authorization: Bearer TOKEN" http://localhost:5001/api/alerts
   ```
3. **Check token is valid** and not expired

### Face Detection Not Working

1. **Install face_recognition properly:**
   ```bash
   pip install face-recognition
   ```
2. **Test face detection directly:**
   ```python
   import face_recognition
   import cv2
   
   image = cv2.imread('test.jpg')
   rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
   face_locations = face_recognition.face_locations(rgb_image)
   print(f"Found {len(face_locations)} faces")
   ```

## Testing

### Test 1: Upload Test Image
1. Upload `test_no_mask_1.jpg` (from test_media folder)
2. Check backend logs
3. Should see: "Faces detected: 0" or "Faces detected: 1"
4. Should see: "Alert created successfully"
5. Check Dashboard or Alerts page

### Test 2: Upload Real Photo
1. Upload a clear photo with a face
2. Check backend logs for face detection
3. Should see faces detected
4. Should see alerts created

### Test 3: Upload Image with Mask
1. Upload image with person wearing mask
2. Should detect faces
3. Should detect masks (compliance rate < 1.0 if some don't have masks)
4. Should create appropriate alerts

## Next Steps

If alerts still aren't being created:

1. **Share backend logs** from image upload
2. **Check database** directly to see if alerts exist
3. **Test API directly** with curl/Postman
4. **Verify all dependencies** are installed correctly

## Notes

- The fallback alert ensures at least one alert is created per upload for testing
- Real face detection requires the `face_recognition` library to work properly
- Simple geometric test images won't trigger face detection
- Use real photos for best results

