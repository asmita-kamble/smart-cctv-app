import { useState, useEffect } from 'react';
import { cameraService } from '../services/cameraService';

const LiveFeed = () => {
  const [cameras, setCameras] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedCamera, setSelectedCamera] = useState(null);
  const [fullscreen, setFullscreen] = useState(false);

  useEffect(() => {
    loadCameras();
  }, []);

  const loadCameras = async () => {
    try {
      const data = await cameraService.getAll();
      const camerasList = Array.isArray(data) ? data : data.cameras || [];
      setCameras(camerasList.filter(camera => camera.status === 'active'));
    } catch (err) {
      setError('Failed to load cameras');
    } finally {
      setLoading(false);
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

  const getPlaceholderImage = () => {
    // Use a neutral placeholder image for all cameras when live feed is not available
    // Returns a simple gray placeholder that looks like a CCTV feed
    return 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="800" height="600"%3E%3Crect width="800" height="600" fill="%231a1a1a"/%3E%3Cg fill="none" stroke="%23333" stroke-width="2"%3E%3Cpath d="M400 200 L400 400 M200 300 L600 300"/%3E%3C/g%3E%3Ccircle cx="400" cy="300" r="80" fill="none" stroke="%23333" stroke-width="2"/%3E%3Ctext x="50%25" y="50%25" text-anchor="middle" dy=".3em" fill="%23666" font-size="18" font-family="Arial, sans-serif"%3ENo Signal%3C/text%3E%3C/svg%3E';
  };

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
            {cameras.map((camera) => (
              <div
                key={camera.id}
                className="bg-white/90 backdrop-blur-sm shadow-lg rounded-lg border border-white/50 overflow-hidden hover:shadow-xl transition-shadow cursor-pointer"
                onClick={() => handleCameraClick(camera)}
              >
                <div className="relative aspect-video bg-gray-900">
                  {/* Placeholder live feed */}
                  <div className="absolute inset-0 flex items-center justify-center">
                    <img
                      src={getPlaceholderImage()}
                      alt={camera.name}
                      className="w-full h-full object-cover"
                      onError={(e) => {
                        e.target.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="800" height="600"%3E%3Crect width="800" height="600" fill="%23111"/%3E%3Ctext x="50%25" y="50%25" text-anchor="middle" dy=".3em" fill="%23999" font-size="24"%3ELive Feed Not Available%3C/text%3E%3C/svg%3E';
                      }}
                    />
                  </div>
                  {/* Live indicator */}
                  <div className="absolute top-2 right-2 flex items-center gap-2">
                    <span className="inline-flex items-center px-2 py-1 rounded bg-red-600 text-white text-xs font-medium">
                      <span className="w-2 h-2 bg-white rounded-full mr-1 animate-pulse"></span>
                      LIVE
                    </span>
                  </div>
                  {/* Camera info overlay */}
                  <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-3">
                    <h3 className="text-white font-semibold text-sm">{camera.name}</h3>
                    <p className="text-white/80 text-xs">{camera.location}</p>
                  </div>
                  {/* Click to expand hint */}
                  <div className="absolute inset-0 bg-black/0 hover:bg-black/10 transition-colors flex items-center justify-center opacity-0 hover:opacity-100">
                    <div className="bg-white/90 rounded-full p-3">
                      <svg className="w-6 h-6 text-gray-800" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
                      </svg>
                    </div>
                  </div>
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
                </div>
              </div>
            ))}
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
                <img
                  src={getPlaceholderImage()}
                  alt={selectedCamera.name}
                  className="max-w-full max-h-full object-contain"
                  onError={(e) => {
                    e.target.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080"%3E%3Crect width="1920" height="1080" fill="%23000"/%3E%3Ctext x="50%25" y="50%25" text-anchor="middle" dy=".3em" fill="%23999" font-size="48"%3ELive Feed Not Available%3C/text%3E%3C/svg%3E';
                  }}
                />
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

