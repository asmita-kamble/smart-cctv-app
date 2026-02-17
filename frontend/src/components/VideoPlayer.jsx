import { useEffect, useRef, useState } from 'react';
import Hls from 'hls.js';
import api from '../utils/api';

/**
 * Video Player Component for HLS streams
 * Supports RTSP streams converted to HLS format
 */
const VideoPlayer = ({ cameraId, autoPlay = true, controls = true, className = '' }) => {
  const videoRef = useRef(null);
  const hlsRef = useRef(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [isPlaying, setIsPlaying] = useState(false);

  useEffect(() => {
    const video = videoRef.current;
    if (!video || !cameraId) return;

    // Build HLS stream URL
    const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5001/api';
    const token = localStorage.getItem('token');
    const streamUrl = `${API_BASE_URL}/cameras/${cameraId}/stream/playlist.m3u8`;

    // Check if HLS is supported natively
    if (video.canPlayType('application/vnd.apple.mpegurl')) {
      // Native HLS support (Safari, iOS)
      // Note: Native HLS doesn't support custom headers, so we'll use query parameter for auth
      const streamUrlWithAuth = `${streamUrl}?token=${token}`;
      video.src = streamUrlWithAuth;
      if (autoPlay) {
        video.play().catch(err => {
          console.error('Error playing video:', err);
          setError('Failed to play video stream');
        });
      }
      setLoading(false);
    } else if (Hls.isSupported()) {
      // Use HLS.js for browsers that don't support native HLS
      const hls = new Hls({
        enableWorker: true,
        lowLatencyMode: true,
        backBufferLength: 90,
        maxBufferLength: 30,
        maxMaxBufferLength: 60,
        maxBufferSize: 60 * 1000 * 1000,
        maxBufferHole: 0.5,
        highBufferWatchdogPeriod: 2,
        nudgeOffset: 0.1,
        nudgeMaxRetry: 3,
        maxFragLoadingTimeOut: 4,
        maxLoadingDelay: 4,
        minAutoBitrate: 0,
        debug: false,
        xhrSetup: (xhr, url) => {
          // Add authentication token to requests
          xhr.setRequestHeader('Authorization', `Bearer ${token}`);
        }
      });

      hls.loadSource(streamUrl);
      hls.attachMedia(video);

      hls.on(Hls.Events.MANIFEST_PARSED, () => {
        setLoading(false);
        if (autoPlay) {
          video.play().catch(err => {
            console.error('Error playing video:', err);
            setError('Failed to play video stream');
          });
        }
      });

      hls.on(Hls.Events.ERROR, (event, data) => {
        if (data.fatal) {
          switch (data.type) {
            case Hls.ErrorTypes.NETWORK_ERROR:
              console.error('Fatal network error, trying to recover...');
              hls.startLoad();
              break;
            case Hls.ErrorTypes.MEDIA_ERROR:
              console.error('Fatal media error, trying to recover...');
              hls.recoverMediaError();
              break;
            default:
              console.error('Fatal error, destroying HLS instance');
              hls.destroy();
              setError('Failed to load video stream. Please check if the camera stream is active.');
              setLoading(false);
              break;
          }
        } else {
          // Non-fatal error, log for debugging
          console.warn('HLS warning:', data);
        }
      });

      hlsRef.current = hls;

      return () => {
        if (hlsRef.current) {
          hlsRef.current.destroy();
        }
      };
    } else {
      setError('HLS is not supported in this browser');
      setLoading(false);
    }

    // Handle video events
    const handlePlay = () => setIsPlaying(true);
    const handlePause = () => setIsPlaying(false);
    const handleError = (e) => {
      console.error('Video error:', e);
      setError('Failed to load video stream');
      setLoading(false);
    };

    video.addEventListener('play', handlePlay);
    video.addEventListener('pause', handlePause);
    video.addEventListener('error', handleError);

    return () => {
      video.removeEventListener('play', handlePlay);
      video.removeEventListener('pause', handlePause);
      video.removeEventListener('error', handleError);
    };
  }, [cameraId, autoPlay]);

  return (
    <div className={`relative ${className}`}>
      {loading && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-900 z-10">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto mb-4"></div>
            <p className="text-white text-sm">Loading stream...</p>
          </div>
        </div>
      )}
      {error && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-900 z-10">
          <div className="text-center text-white">
            <svg className="w-12 h-12 mx-auto mb-4 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p className="text-sm">{error}</p>
            <p className="text-xs text-gray-400 mt-2">Make sure the camera has an IP address and the stream is started</p>
          </div>
        </div>
      )}
      <video
        ref={videoRef}
        className="w-full h-full object-contain bg-black"
        controls={controls}
        playsInline
        muted={autoPlay} // Mute for autoplay (browser requirement)
      />
    </div>
  );
};

export default VideoPlayer;

