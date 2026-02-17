"""
RTSP Streaming Service for converting RTSP streams to HLS format.
Manages FFmpeg processes to convert RTSP camera feeds to web-compatible HLS streams.
"""
import os
import subprocess
import threading
import time
from typing import Optional, Dict
from pathlib import Path


class StreamingService:
    """Service for managing RTSP to HLS stream conversions."""
    
    # Store active FFmpeg processes
    _active_streams: Dict[int, subprocess.Popen] = {}
    _stream_locks: Dict[int, threading.Lock] = {}
    
    # Base directory for HLS output
    HLS_OUTPUT_DIR = Path('streams')
    
    def __init__(self):
        """Initialize streaming service."""
        # Create streams directory if it doesn't exist
        self.HLS_OUTPUT_DIR.mkdir(exist_ok=True)
    
    @staticmethod
    def build_rtsp_url(ip_address: str, port: int = 554, username: str = None, password: str = None, path: str = '/stream1') -> str:
        """
        Build RTSP URL from camera IP address.
        
        Args:
            ip_address: Camera IP address
            port: RTSP port (default: 554)
            username: Optional username for authentication
            password: Optional password for authentication
            path: RTSP stream path (default: /stream1)
            
        Returns:
            RTSP URL string
        """
        if username and password:
            return f'rtsp://{username}:{password}@{ip_address}:{port}{path}'
        return f'rtsp://{ip_address}:{port}{path}'
    
    def start_stream(self, camera_id: int, rtsp_url: str, hls_time: int = 2, hls_list_size: int = 3) -> bool:
        """
        Start converting RTSP stream to HLS format.
        
        Args:
            camera_id: Camera ID
            rtsp_url: RTSP stream URL
            hls_time: Segment duration in seconds (default: 2)
            hls_list_size: Number of segments in playlist (default: 3)
            
        Returns:
            True if stream started successfully, False otherwise
        """
        # Check if stream already exists
        if camera_id in self._active_streams:
            process = self._active_streams[camera_id]
            if process.poll() is None:  # Process is still running
                return True
        
        # Create lock for this camera if it doesn't exist
        if camera_id not in self._stream_locks:
            self._stream_locks[camera_id] = threading.Lock()
        
        with self._stream_locks[camera_id]:
            try:
                # Create camera-specific output directory
                camera_dir = self.HLS_OUTPUT_DIR / str(camera_id)
                camera_dir.mkdir(exist_ok=True)
                
                # HLS output path
                playlist_path = camera_dir / 'playlist.m3u8'
                
                # FFmpeg command to convert RTSP to HLS
                ffmpeg_cmd = [
                    'ffmpeg',
                    '-rtsp_transport', 'tcp',  # Use TCP for better reliability
                    '-i', rtsp_url,
                    '-c:v', 'libx264',  # Video codec
                    '-c:a', 'aac',  # Audio codec (if audio exists)
                    '-hls_time', str(hls_time),  # Segment duration
                    '-hls_list_size', str(hls_list_size),  # Number of segments
                    '-hls_flags', 'delete_segments',  # Delete old segments
                    '-hls_segment_filename', str(camera_dir / 'segment_%03d.ts'),
                    '-f', 'hls',
                    str(playlist_path),
                    '-loglevel', 'error',  # Reduce log output
                    '-y'  # Overwrite output files
                ]
                
                # Start FFmpeg process
                process = subprocess.Popen(
                    ffmpeg_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    stdin=subprocess.PIPE
                )
                
                # Wait a moment to check if process started successfully
                time.sleep(1)
                
                if process.poll() is not None:
                    # Process terminated immediately (error)
                    stderr = process.stderr.read().decode() if process.stderr else 'Unknown error'
                    print(f"FFmpeg failed to start for camera {camera_id}: {stderr}")
                    return False
                
                # Store process
                self._active_streams[camera_id] = process
                print(f"Started RTSP stream for camera {camera_id}")
                return True
                
            except Exception as e:
                print(f"Error starting stream for camera {camera_id}: {str(e)}")
                return False
    
    def stop_stream(self, camera_id: int) -> bool:
        """
        Stop HLS stream conversion for a camera.
        
        Args:
            camera_id: Camera ID
            
        Returns:
            True if stream stopped successfully, False otherwise
        """
        if camera_id not in self._active_streams:
            return True  # Already stopped
        
        try:
            process = self._active_streams[camera_id]
            
            # Terminate FFmpeg process
            process.terminate()
            
            # Wait for process to terminate (with timeout)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Force kill if it doesn't terminate
                process.kill()
                process.wait()
            
            # Remove from active streams
            del self._active_streams[camera_id]
            
            # Clean up HLS files
            camera_dir = self.HLS_OUTPUT_DIR / str(camera_id)
            if camera_dir.exists():
                try:
                    import shutil
                    shutil.rmtree(camera_dir)
                except Exception as e:
                    print(f"Error cleaning up HLS files for camera {camera_id}: {str(e)}")
            
            print(f"Stopped RTSP stream for camera {camera_id}")
            return True
            
        except Exception as e:
            print(f"Error stopping stream for camera {camera_id}: {str(e)}")
            return False
    
    def is_stream_active(self, camera_id: int) -> bool:
        """
        Check if stream is currently active.
        
        Args:
            camera_id: Camera ID
            
        Returns:
            True if stream is active, False otherwise
        """
        if camera_id not in self._active_streams:
            return False
        
        process = self._active_streams[camera_id]
        return process.poll() is None  # None means process is still running
    
    def get_hls_playlist_path(self, camera_id: int) -> Optional[Path]:
        """
        Get path to HLS playlist file.
        
        Args:
            camera_id: Camera ID
            
        Returns:
            Path to playlist.m3u8 file or None if not found
        """
        playlist_path = self.HLS_OUTPUT_DIR / str(camera_id) / 'playlist.m3u8'
        if playlist_path.exists():
            return playlist_path
        return None
    
    def get_hls_segment_path(self, camera_id: int, segment_name: str) -> Optional[Path]:
        """
        Get path to HLS segment file.
        
        Args:
            camera_id: Camera ID
            segment_name: Segment filename (e.g., 'segment_000.ts')
            
        Returns:
            Path to segment file or None if not found
        """
        segment_path = self.HLS_OUTPUT_DIR / str(camera_id) / segment_name
        if segment_path.exists():
            return segment_path
        return None


# Global instance
streaming_service = StreamingService()

