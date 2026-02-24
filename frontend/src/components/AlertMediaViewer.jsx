import { useState, useEffect, useRef, useCallback } from 'react';
import { FaceDetector, FilesetResolver } from '@mediapipe/tasks-vision';

const WASM_BASE = 'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@latest/wasm';
const FACE_MODEL =
  'https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/1/blaze_face_short_range.tflite';

const FACE_BORDER_COLOR = '#00e676';
const FACE_BORDER_WIDTH = 3;
const DETECTION_INTERVAL_MS = 150;
const DETECTION_PERSIST_MS = 600;

/**
 * Loads the MediaPipe Face Detector once (IMAGE mode) for reuse.
 * IMAGE mode treats each frame independently so replay and seeking work.
 */
let cachedDetector = null;
async function getFaceDetector() {
  if (!cachedDetector) {
    const vision = await FilesetResolver.forVisionTasks(WASM_BASE);
    cachedDetector = await FaceDetector.createFromOptions(vision, {
      baseOptions: { modelAssetPath: FACE_MODEL },
      runningMode: 'IMAGE',
      minDetectionConfidence: 0.35,
    });
  }
  return cachedDetector;
}

/**
 * Alert media viewer with face detection overlay.
 * Draws a colored border around detected human faces when playing video or viewing image in the Alerts tab.
 */
const AlertMediaViewer = ({ src, name, isVideo, onClose }) => {
  const containerRef = useRef(null);
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const offscreenCanvasRef = useRef(null);
  const imgRef = useRef(null);
  const rafRef = useRef(null);
  const lastDetectTimeRef = useRef(0);
  const detectorRef = useRef(null);
  const lastDetectionsRef = useRef([]);
  const lastDetectionsTimeRef = useRef(0);
  const lastSourceSizeRef = useRef({ w: 0, h: 0 });

  const [modelLoading, setModelLoading] = useState(true);
  const [modelError, setModelError] = useState('');
  const [faceDetector, setFaceDetector] = useState(null);
  const [faceCount, setFaceCount] = useState(null);

  useEffect(() => {
    setFaceCount(null);
  }, [src]);

  useEffect(() => {
    let cancelled = false;
    getFaceDetector()
      .then((detector) => {
        if (!cancelled) {
          detectorRef.current = detector;
          setFaceDetector(detector);
          setModelLoading(false);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          console.error('Face detector load error:', err);
          setModelError('Face detection unavailable');
          setModelLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const drawFacesOnCanvas = useCallback(
    (detections, sourceWidth, sourceHeight, canvas) => {
      if (!canvas) return;
      const ctx = canvas.getContext('2d');
      if (!ctx) return;
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      if (!detections?.length) return;
      const scaleX = canvas.width / sourceWidth;
      const scaleY = canvas.height / sourceHeight;
      for (const d of detections) {
        const box = d.boundingBox;
        if (!box) continue;
        let x = box.originX;
        let y = box.originY;
        let w = box.width;
        let h = box.height;
        if (x <= 1 && y <= 1 && w <= 1 && h <= 1) {
          x *= sourceWidth;
          y *= sourceHeight;
          w *= sourceWidth;
          h *= sourceHeight;
        }
        x *= scaleX;
        y *= scaleY;
        w *= scaleX;
        h *= scaleY;
        ctx.strokeStyle = FACE_BORDER_COLOR;
        ctx.lineWidth = FACE_BORDER_WIDTH;
        ctx.strokeRect(x, y, w, h);
      }
    },
    []
  );

  const alignCanvasToVideo = useCallback(() => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!video || !canvas || !container) return;
    const rect = video.getBoundingClientRect();
    const containerRect = container.getBoundingClientRect();
    canvas.style.width = `${rect.width}px`;
    canvas.style.height = `${rect.height}px`;
    canvas.width = Math.round(rect.width);
    canvas.height = Math.round(rect.height);
    canvas.style.left = `${rect.left - containerRect.left}px`;
    canvas.style.top = `${rect.top - containerRect.top}px`;
  }, []);

  useEffect(() => {
    if (!isVideo || !faceDetector || !src) return;
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas) return;

    const runDetection = () => {
      const v = videoRef.current;
      const displayCanvas = canvasRef.current;
      const detector = detectorRef.current;
      if (!v || !displayCanvas || !detector) return;
      if (v.readyState < 2 || v.videoWidth === 0 || v.videoHeight === 0) {
        rafRef.current = requestAnimationFrame(runDetection);
        return;
      }
      const now = performance.now();
      if (now - lastDetectTimeRef.current >= DETECTION_INTERVAL_MS) {
        lastDetectTimeRef.current = now;
        let offscreen = offscreenCanvasRef.current;
        if (!offscreen || offscreen.width !== v.videoWidth || offscreen.height !== v.videoHeight) {
          offscreen = document.createElement('canvas');
          offscreen.width = v.videoWidth;
          offscreen.height = v.videoHeight;
          offscreenCanvasRef.current = offscreen;
        }
        const ctx = offscreen.getContext('2d');
        if (ctx) {
          ctx.drawImage(v, 0, 0, offscreen.width, offscreen.height);
          const sw = offscreen.width;
          const sh = offscreen.height;
          try {
            const result = detector.detect(offscreen);
            const detections = result?.detections ?? [];
            if (detections.length > 0) {
              lastDetectionsRef.current = detections;
              lastDetectionsTimeRef.current = now;
              lastSourceSizeRef.current = { w: sw, h: sh };
              setFaceCount(detections.length);
              drawFacesOnCanvas(detections, sw, sh, displayCanvas);
            } else {
              if (now - lastDetectionsTimeRef.current < DETECTION_PERSIST_MS && lastDetectionsRef.current.length > 0) {
                const last = lastDetectionsRef.current;
                const { w, h } = lastSourceSizeRef.current;
                drawFacesOnCanvas(last, w, h, displayCanvas);
              } else {
                drawFacesOnCanvas([], sw, sh, displayCanvas);
                setFaceCount(0);
              }
            }
          } catch (e) {
            if (process.env.NODE_ENV === 'development') {
              console.warn('Face detection frame error:', e?.message);
            }
            if (lastDetectionsRef.current.length > 0 && now - lastDetectionsTimeRef.current < DETECTION_PERSIST_MS) {
              const { w, h } = lastSourceSizeRef.current;
              drawFacesOnCanvas(lastDetectionsRef.current, w, h, displayCanvas);
            }
          }
        }
      } else {
        rafRef.current = requestAnimationFrame(runDetection);
        return;
      }
      rafRef.current = requestAnimationFrame(runDetection);
    };

    const onPlay = () => {
      lastDetectTimeRef.current = 0;
      alignCanvasToVideo();
      runDetection();
    };
    const onPause = () => {
      setFaceCount(null);
      lastDetectionsRef.current = [];
      if (rafRef.current) {
        cancelAnimationFrame(rafRef.current);
        rafRef.current = null;
      }
      if (canvasRef.current) {
        const ctx = canvasRef.current.getContext('2d');
        if (ctx) ctx.clearRect(0, 0, canvasRef.current.width, canvasRef.current.height);
      }
    };
    const onResize = () => alignCanvasToVideo();

    video.addEventListener('play', onPlay);
    video.addEventListener('pause', onPause);
    window.addEventListener('resize', onResize);
    video.addEventListener('loadedmetadata', alignCanvasToVideo);

    if (!video.paused && !video.ended) {
      alignCanvasToVideo();
      runDetection();
    }

    return () => {
      video.removeEventListener('play', onPlay);
      video.removeEventListener('pause', onPause);
      window.removeEventListener('resize', onResize);
      video.removeEventListener('loadedmetadata', alignCanvasToVideo);
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, [isVideo, faceDetector, src, drawFacesOnCanvas, alignCanvasToVideo]);

  useEffect(() => {
    if (isVideo || !faceDetector || !src) return;
    const img = imgRef.current;
    const canvas = canvasRef.current;
    if (!img || !canvas) return;

    const onLoad = () => {
      const naturalW = img.naturalWidth;
      const naturalH = img.naturalHeight;
      const displayW = img.offsetWidth;
      const displayH = img.offsetHeight;
      canvas.width = displayW;
      canvas.height = displayH;
      canvas.style.width = displayW + 'px';
      canvas.style.height = displayH + 'px';
      try {
        const result = faceDetector.detect(img);
        const detections = result?.detections ?? [];
        setFaceCount(detections.length);
        drawFacesOnCanvas(detections, naturalW, naturalH, canvas);
      } catch (e) {
        console.error('Face detection on image:', e);
      }
    };

    if (img.complete && img.naturalWidth) onLoad();
    else img.addEventListener('load', onLoad);
    return () => img.removeEventListener('load', onLoad);
  }, [isVideo, faceDetector, src, drawFacesOnCanvas]);

  return (
    <div className="bg-white rounded-lg overflow-hidden">
      <div className="p-4 border-b">
        <h3 className="text-lg font-semibold text-gray-900">{name}</h3>
        {modelLoading && (
          <p className="text-xs text-gray-500 mt-1">Loading face detection...</p>
        )}
        {modelError && (
          <p className="text-xs text-amber-600 mt-1">{modelError}</p>
        )}
        {!modelLoading && !modelError && isVideo && (
          <p className="text-xs text-gray-500 mt-1">
            Play the video to see face borders. {faceCount != null && `Faces detected: ${faceCount}`}
          </p>
        )}
      </div>
      <div className="p-4 relative inline-block max-w-full" ref={containerRef}>
        {isVideo ? (
          <>
            <video
              ref={videoRef}
              src={src}
              controls
              className="max-w-full max-h-[70vh] mx-auto block"
              onError={(e) => console.error('Video load error:', e)}
            >
              Your browser does not support the video tag.
            </video>
            {faceDetector && (
              <canvas
                ref={canvasRef}
                className="absolute pointer-events-none z-10"
                style={{ left: 0, top: 0 }}
              />
            )}
          </>
        ) : (
          <>
            <img
              ref={imgRef}
              src={src}
              alt={name}
              className="max-w-full max-h-[70vh] mx-auto object-contain block"
              onError={(e) => {
                e.target.src =
                  "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='400' height='300'%3E%3Crect width='400' height='300' fill='%23ddd'/%3E%3Ctext x='50%25' y='50%25' text-anchor='middle' dy='.3em' fill='%23999'%3EImage not found%3C/text%3E%3C/svg%3E";
              }}
            />
            {faceDetector && (
              <canvas
                ref={canvasRef}
                className="absolute left-0 top-0 pointer-events-none"
              />
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default AlertMediaViewer;
