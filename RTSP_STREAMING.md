# RTSP Live Streaming Feature

This document describes the RTSP live streaming functionality added to the Smart CCTV application.

## Overview

The application now supports live video streaming from IP cameras using the RTSP (Real-Time Streaming Protocol) protocol. RTSP streams are converted to HLS (HTTP Live Streaming) format for web browser compatibility.

## Architecture

### Backend
- **Streaming Service** (`backend/app/services/streaming_service.py`): Manages FFmpeg processes to convert RTSP streams to HLS format
- **Camera Controller** (`backend/app/controllers/camera_controller.py`): Provides REST API endpoints for:
  - Starting/stopping streams
  - Getting stream status
  - Serving HLS playlists and segments

### Frontend
- **VideoPlayer Component** (`frontend/src/components/VideoPlayer.jsx`): React component that plays HLS streams using hls.js library
- **LiveFeed Page** (`frontend/src/pages/LiveFeed.jsx`): Updated to display live streams from cameras with IP addresses

## Prerequisites

### System Requirements
1. **FFmpeg** must be installed on the backend server:
   - macOS: `brew install ffmpeg`
   - Ubuntu/Debian: `sudo apt-get install ffmpeg`
   - Windows: Download from https://ffmpeg.org/download.html

2. **Camera Requirements**:
   - Camera must have an IP address configured
   - Camera must support RTSP protocol
   - Camera must be accessible from the backend server

### Frontend Dependencies
- `hls.js` library (added to `package.json`)

## Usage

### 1. Add Camera with IP Address

When creating or editing a camera, provide the IP address:
- Navigate to Cameras page
- Click "Add Camera" or edit an existing camera
- Enter the IP address (e.g., `192.168.1.100`)
- Save the camera

### 2. Start Live Stream

#### Automatic Start
- When viewing the Live Feed page, streams are automatically started for cameras with IP addresses

#### Manual Start
- On the Live Feed page, click "Start Stream" button for a camera
- Or use the API endpoint:
  ```bash
  POST /api/cameras/{camera_id}/stream/start
  ```

### 3. View Live Stream

- Navigate to the **Live Feed** page
- Active cameras with IP addresses will display live video streams
- Click on a camera feed to view in fullscreen mode
- Click "Stop Stream" to stop a stream

### 4. RTSP Configuration

By default, the system uses:
- RTSP Port: `554` (standard RTSP port)
- RTSP Path: `/stream1` (common default path)

To customize RTSP settings, use the start stream API with parameters:
```json
{
  "rtsp_port": 554,
  "rtsp_path": "/stream1",
  "rtsp_username": "admin",
  "rtsp_password": "password"
}
```

## API Endpoints

### Start Stream
```
POST /api/cameras/{camera_id}/stream/start
```
Starts RTSP to HLS conversion for a camera.

**Request Body (optional):**
```json
{
  "rtsp_port": 554,
  "rtsp_path": "/stream1",
  "rtsp_username": "admin",
  "rtsp_password": "password"
}
```

### Stop Stream
```
POST /api/cameras/{camera_id}/stream/stop
```
Stops the stream conversion for a camera.

### Get Stream Status
```
GET /api/cameras/{camera_id}/stream/status
```
Returns the current streaming status.

**Response:**
```json
{
  "camera_id": 1,
  "streaming": true,
  "stream_url": "/api/cameras/1/stream/playlist.m3u8"
}
```

### Get HLS Playlist
```
GET /api/cameras/{camera_id}/stream/playlist.m3u8
```
Serves the HLS playlist file (M3U8 format).

### Get HLS Segment
```
GET /api/cameras/{camera_id}/stream/segment/{segment_name}
```
Serves individual HLS segment files (.ts files).

## RTSP URL Format

The system builds RTSP URLs in the following format:

**Without authentication:**
```
rtsp://{ip_address}:{port}{path}
```

**With authentication:**
```
rtsp://{username}:{password}@{ip_address}:{port}{path}
```

**Example:**
```
rtsp://192.168.1.100:554/stream1
rtsp://admin:password@192.168.1.100:554/stream1
```

## Common RTSP Paths

Different camera manufacturers use different RTSP paths:

- **Hikvision**: `/Streaming/Channels/1` or `/h264/ch1/main/av_stream`
- **Dahua**: `/cam/realmonitor?channel=1&subtype=0`
- **Axis**: `/axis-media/media.amp`
- **Generic**: `/stream1`, `/live`, `/video`

## Troubleshooting

### Stream Not Starting
1. **Check FFmpeg Installation**:
   ```bash
   ffmpeg -version
   ```

2. **Check Camera IP Address**:
   - Verify the IP address is correct
   - Test camera accessibility: `ping {camera_ip}`

3. **Check RTSP URL**:
   - Verify RTSP port (usually 554)
   - Check RTSP path (varies by manufacturer)
   - Test with VLC: `vlc rtsp://{ip}:{port}{path}`

4. **Check Backend Logs**:
   - Look for FFmpeg errors in console output
   - Check if stream directory is created: `backend/streams/{camera_id}/`

### Stream Not Playing in Browser
1. **Check Browser Support**:
   - Chrome/Edge: Uses HLS.js (should work)
   - Firefox: Uses HLS.js (should work)
   - Safari: Native HLS support (should work)

2. **Check Network**:
   - Verify backend is accessible from frontend
   - Check CORS configuration
   - Verify authentication token is valid

3. **Check Console**:
   - Open browser developer tools
   - Check for JavaScript errors
   - Check Network tab for failed requests

### Performance Issues
1. **Reduce Stream Quality**:
   - Modify FFmpeg command in `streaming_service.py`
   - Add `-preset fast` or `-preset ultrafast`
   - Reduce resolution: `-s 640x480`

2. **Adjust HLS Settings**:
   - Reduce `hls_time` (segment duration)
   - Reduce `hls_list_size` (number of segments)

## File Structure

```
backend/
├── app/
│   ├── services/
│   │   └── streaming_service.py    # RTSP to HLS conversion service
│   └── controllers/
│       └── camera_controller.py    # Streaming API endpoints
└── streams/                        # HLS output directory (auto-created)
    └── {camera_id}/
        ├── playlist.m3u8           # HLS playlist
        └── segment_*.ts            # HLS video segments

frontend/
├── src/
│   ├── components/
│   │   └── VideoPlayer.jsx        # HLS video player component
│   └── pages/
│       └── LiveFeed.jsx            # Live feed page with streams
```

## Security Considerations

1. **Authentication**: All streaming endpoints require authentication
2. **Access Control**: Users can only access streams for cameras they own (or all cameras if admin)
3. **RTSP Credentials**: Store camera credentials securely (consider encrypting in database)
4. **Network Security**: Ensure RTSP streams are on a secure network

## Future Enhancements

- [ ] Support for multiple RTSP streams per camera
- [ ] Stream recording functionality
- [ ] Stream quality selection (SD/HD)
- [ ] WebRTC support for lower latency
- [ ] Stream analytics and monitoring
- [ ] Automatic stream reconnection on failure

## Notes

- HLS segments are automatically cleaned up when streams stop
- Streams are started on-demand (when requested)
- Multiple users can view the same stream (single FFmpeg process per camera)
- Streams persist until explicitly stopped or camera is deleted

