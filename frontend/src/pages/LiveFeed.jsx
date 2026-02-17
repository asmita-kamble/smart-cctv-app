import { useState, useEffect } from 'react';
import { cameraService } from '../services/cameraService';
import VideoPlayer from '../components/VideoPlayer';

const LiveFeed = () => {
  const [cameras, setCameras] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedCamera, setSelectedCamera] = useState(null);
  const [fullscreen, setFullscreen] = useState(false);
  const [streamStatuses, setStreamStatuses] = useState({});
  const [startingStreams, setStartingStreams] = useState(new Set());

  useEffect(() => {
    loadCameras();
  }, []);

  const loadCameras = async () => {
    try {
      const data = await cameraService.getAll();
      const camerasList = Array.isArray(data) ? data : data.cameras || [];
      const activeCameras = camerasList.filter(camera => camera.status === 'active');
      setCameras(activeCameras);
      
      // Check stream status for each camera with IP address
      const statusPromises = activeCameras
        .filter(camera => camera.ip_address)
        .map(async (camera) => {
          try {
            const status = await cameraService.getStreamStatus(camera.id);
            return { cameraId: camera.id, status };
          } catch (err) {
            return { cameraId: camera.id, status: { streaming: false } };
          }
        });
      
      const statuses = await Promise.all(statusPromises);
      const statusMap = {};
      statuses.forEach(({ cameraId, status }) => {
        statusMap[cameraId] = status;
      });
      setStreamStatuses(statusMap);
      
      // Auto-start streams for cameras with IP addresses
      activeCameras
        .filter(camera => camera.ip_address && !statusMap[camera.id]?.streaming)
        .forEach(camera => {
          startCameraStream(camera.id);
        });
    } catch (err) {
      setError('Failed to load cameras');
    } finally {
      setLoading(false);
    }
  };

  const startCameraStream = async (cameraId) => {
    if (startingStreams.has(cameraId)) return; // Already starting
    
    setStartingStreams(prev => new Set(prev).add(cameraId));
    try {
      await cameraService.startStream(cameraId);
      // Update stream status
      const status = await cameraService.getStreamStatus(cameraId);
      setStreamStatuses(prev => ({ ...prev, [cameraId]: status }));
    } catch (err) {
      console.error(`Failed to start stream for camera ${cameraId}:`, err);
      // Don't show error for each camera, just log it
    } finally {
      setStartingStreams(prev => {
        const newSet = new Set(prev);
        newSet.delete(cameraId);
        return newSet;
      });
    }
  };

  const stopCameraStream = async (cameraId) => {
    try {
      await cameraService.stopStream(cameraId);
      setStreamStatuses(prev => ({ ...prev, [cameraId]: { streaming: false } }));
    } catch (err) {
      console.error(`Failed to stop stream for camera ${cameraId}:`, err);
    }
  };

  const handleCameraClick = (camera) => {
    setSelectedCamera(camera);
    setFullscreen(true);
  };

  const closeFullscreen = () => {
    setFullscreen(false);
    setSelectedCamera(null);
  };

  // Cleanup: stop streams when component unmounts
  useEffect(() => {
    return () => {
      // Stop all active streams on unmount
      cameras.forEach(camera => {
        if (camera.ip_address && streamStatuses[camera.id]?.streaming) {
          stopCameraStream(camera.id);
        }
      });
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);


  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <>
      {/* Full-screen background */}
      <div 
        className="fixed inset-0 -z-10"
        style={{
          backgroundImage: `linear-gradient(135deg, rgba(249, 250, 251, 0.90) 0%, rgba(243, 244, 246, 0.93) 100%), 
                           url('https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?ixlib=rb-4.0.3&auto=format&fit=crop&w=2070&q=80')`,
          backgroundSize: 'cover',
          backgroundPosition: 'center',
          backgroundRepeat: 'no-repeat',
          backgroundAttachment: 'fixed'
        }}
      />
      <div className="relative z-10">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold text-gray-900 drop-shadow-sm">Live Feed</h2>
          <div className="text-sm text-gray-600">
            {cameras.length} Active Camera{cameras.length !== 1 ? 's' : ''}
          </div>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        {cameras.length === 0 ? (
          <div className="bg-white/90 backdrop-blur-sm shadow-lg rounded-lg p-8 border border-white/50 text-center">
            <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
            </svg>
            <h3 className="mt-2 text-sm font-medium text-gray-900">No Active Cameras</h3>
            <p className="mt-1 text-sm text-gray-500">No active cameras available for live feed.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {cameras.map((camera) => {
              const isStreaming = streamStatuses[camera.id]?.streaming || false;
              const isStarting = startingStreams.has(camera.id);
              const hasIpAddress = !!camera.ip_address;
              
              return (
                <div
                  key={camera.id}
                  className="bg-white/90 backdrop-blur-sm shadow-lg rounded-lg border border-white/50 overflow-hidden hover:shadow-xl transition-shadow"
                >
                  <div className="relative aspect-video bg-gray-900">
                    {hasIpAddress ? (
                      isStreaming ? (
                        <VideoPlayer
                          cameraId={camera.id}
                          autoPlay={true}
                          controls={false}
                          className="w-full h-full"
                        />
                      ) : (
                        <div className="absolute inset-0 flex items-center justify-center bg-gray-900">
                          {isStarting ? (
                            <div className="text-center text-white">
                              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white mx-auto mb-2"></div>
                              <p className="text-sm">Starting stream...</p>
                            </div>
                          ) : (
                            <div className="text-center text-white">
                              <svg className="w-12 h-12 mx-auto mb-2 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                              </svg>
                              <p className="text-sm text-gray-400">Stream not started</p>
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  startCameraStream(camera.id);
                                }}
                                className="mt-2 px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white text-xs rounded"
                              >
                                Start Stream
                              </button>
                            </div>
                          )}
                        </div>
                      )
                    ) : (
                      <div className="absolute inset-0 flex items-center justify-center bg-gray-900">
                        <div className="text-center text-white">
                          <svg className="w-12 h-12 mx-auto mb-2 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 5.636l-3.536 3.536m0 5.656l3.536 3.536M9.172 9.172L5.636 5.636m3.536 9.192l-3.536 3.536M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-5 0a4 4 0 11-8 0 4 4 0 018 0z" />
                          </svg>
                          <p className="text-sm text-gray-400">No IP Address</p>
                          <p className="text-xs text-gray-500 mt-1">Add IP address to enable streaming</p>
                        </div>
                      </div>
                    )}
                    
                    {/* Live indicator */}
                    {isStreaming && (
                      <div className="absolute top-2 right-2 z-10">
                        <span className="inline-flex items-center px-2 py-1 rounded bg-red-600 text-white text-xs font-medium">
                          <span className="w-2 h-2 bg-white rounded-full mr-1 animate-pulse"></span>
                          LIVE
                        </span>
                      </div>
                    )}
                    
                    {/* Camera info overlay */}
                    <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-3 z-10">
                      <h3 className="text-white font-semibold text-sm">{camera.name}</h3>
                      <p className="text-white/80 text-xs">{camera.location}</p>
                    </div>
                    
                    {/* Click to expand hint */}
                    {isStreaming && (
                      <div 
                        className="absolute inset-0 bg-black/0 hover:bg-black/10 transition-colors flex items-center justify-center opacity-0 hover:opacity-100 cursor-pointer z-10"
                        onClick={() => handleCameraClick(camera)}
                      >
                        <div className="bg-white/90 rounded-full p-3">
                          <svg className="w-6 h-6 text-gray-800" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
                          </svg>
                        </div>
                      </div>
                    )}
                  </div>
                  <div className="p-3 bg-gray-50">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                          camera.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                        }`}>
                          {camera.status}
                        </span>
                        {camera.is_restricted_zone && (
                          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-800">
                            Restricted
                          </span>
                        )}
                      </div>
                      {camera.ip_address && (
                        <span className="text-xs text-gray-500">{camera.ip_address}</span>
                      )}
                    </div>
                    {isStreaming && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          stopCameraStream(camera.id);
                        }}
                        className="mt-2 w-full px-2 py-1 bg-red-600 hover:bg-red-700 text-white text-xs rounded"
                      >
                        Stop Stream
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Fullscreen Modal */}
        {fullscreen && selectedCamera && (
          <div 
            className="fixed inset-0 bg-black z-50 flex items-center justify-center"
            onClick={closeFullscreen}
          >
            <div className="relative w-full h-full flex flex-col">
              {/* Header */}
              <div className="absolute top-0 left-0 right-0 bg-black/80 text-white p-4 z-10 flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-semibold">{selectedCamera.name}</h3>
                  <p className="text-sm text-gray-300">{selectedCamera.location}</p>
                </div>
                <div className="flex items-center gap-4">
                  <span className="inline-flex items-center px-3 py-1 rounded bg-red-600 text-white text-sm font-medium">
                    <span className="w-2 h-2 bg-white rounded-full mr-2 animate-pulse"></span>
                    LIVE
                  </span>
                  <button
                    onClick={closeFullscreen}
                    className="bg-white/20 hover:bg-white/30 text-white rounded-full p-2 transition-colors"
                  >
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              </div>
              
              {/* Live Feed */}
              <div className="flex-1 flex items-center justify-center bg-black">
                {selectedCamera.ip_address && streamStatuses[selectedCamera.id]?.streaming ? (
                  <VideoPlayer
                    cameraId={selectedCamera.id}
                    autoPlay={true}
                    controls={true}
                    className="w-full h-full"
                  />
                ) : (
                  <div className="text-center text-white">
                    <svg className="w-24 h-24 mx-auto mb-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                    </svg>
                    <p className="text-xl mb-2">Stream Not Available</p>
                    {!selectedCamera.ip_address ? (
                      <p className="text-gray-400">Camera IP address is required for streaming</p>
                    ) : (
                      <div>
                        <p className="text-gray-400 mb-4">Please start the stream first</p>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            startCameraStream(selectedCamera.id);
                          }}
                          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded"
                        >
                          Start Stream
                        </button>
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Footer Info */}
              <div className="absolute bottom-0 left-0 right-0 bg-black/80 text-white p-4 z-10">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4 text-sm">
                    <span>Status: <span className="text-green-400">{selectedCamera.status}</span></span>
                    {selectedCamera.ip_address && (
                      <span>IP: <span className="text-gray-300">{selectedCamera.ip_address}</span></span>
                    )}
                    {selectedCamera.is_restricted_zone && (
                      <span className="text-red-400">Restricted Zone</span>
                    )}
                  </div>
                  <div className="text-sm text-gray-400">
                    {new Date().toLocaleString()}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </>
  );
};

export default LiveFeed;

