import { useState, useEffect } from 'react';
import { alertService } from '../services/alertService';

const Alerts = () => {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [viewingImage, setViewingImage] = useState(null);
  const [activeTab, setActiveTab] = useState('pending'); // 'pending' or 'resolved'

  useEffect(() => {
    loadAlerts();
  }, []);

  const loadAlerts = async () => {
    try {
      const data = await alertService.getAll();
      setAlerts(Array.isArray(data) ? data : data.alerts || []);
    } catch (err) {
      setError('Failed to load alerts');
    } finally {
      setLoading(false);
    }
  };

  const handleResolve = async (id) => {
    try {
      await alertService.resolve(id);
      loadAlerts();
    } catch (err) {
      setError('Failed to resolve alert');
    }
  };

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical':
        return 'bg-red-100 text-red-800';
      case 'high':
        return 'bg-orange-100 text-orange-800';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800';
      case 'low':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'resolved':
        return 'bg-green-100 text-green-800';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getMediaName = (alert) => {
    if (alert.metadata) {
      const mediaPath = alert.metadata.image_path || alert.metadata.video_path;
      if (mediaPath) {
        return mediaPath.split('/').pop() || mediaPath;
      }
    }
    return null;
  };

  const isVideo = (alert) => {
    return alert.metadata && alert.metadata.video_path && !alert.metadata.image_path;
  };

  const getImageUrl = (alertId) => {
    const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5001/api';
    return `${API_BASE_URL}/alerts/${alertId}/image`;
  };

  const handleViewMedia = async (alert) => {
    const mediaName = getMediaName(alert);
    if (!mediaName) {
      setError('No media file associated with this alert');
      return;
    }
    
    try {
      const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5001/api';
      const token = localStorage.getItem('token');
      
      const response = await fetch(getImageUrl(alert.id), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to load media file');
      }

      const blob = await response.blob();
      const blobUrl = URL.createObjectURL(blob);
      setViewingImage({ url: blobUrl, name: mediaName, isVideo: isVideo(alert) });
    } catch (error) {
      console.error('Error loading media:', error);
      setError('Failed to load media file');
    }
  };

  const closeImageView = () => {
    if (viewingImage && viewingImage.url) {
      URL.revokeObjectURL(viewingImage.url);
    }
    setViewingImage(null);
  };

  // Filter alerts based on active tab
  const filteredAlerts = alerts.filter((alert) => {
    if (activeTab === 'pending') {
      return alert.status === 'pending';
    } else {
      return alert.status === 'resolved';
    }
  });

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
      <h2 className="text-2xl font-bold text-gray-900 mb-6 drop-shadow-sm">Alerts</h2>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      {/* Tabs */}
      <div className="mb-6 border-b border-gray-200 bg-white/90 backdrop-blur-sm rounded-lg p-4">
        <nav className="-mb-px flex space-x-8" aria-label="Tabs">
          <button
            onClick={() => setActiveTab('pending')}
            className={`${
              activeTab === 'pending'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition-colors`}
          >
            Pending
            {alerts.filter((a) => a.status === 'pending').length > 0 && (
              <span className={`ml-2 py-0.5 px-2 rounded-full text-xs ${
                activeTab === 'pending' ? 'bg-primary-100 text-primary-800' : 'bg-gray-100 text-gray-600'
              }`}>
                {alerts.filter((a) => a.status === 'pending').length}
              </span>
            )}
          </button>
          <button
            onClick={() => setActiveTab('resolved')}
            className={`${
              activeTab === 'resolved'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition-colors`}
          >
            Resolved
            {alerts.filter((a) => a.status === 'resolved').length > 0 && (
              <span className={`ml-2 py-0.5 px-2 rounded-full text-xs ${
                activeTab === 'resolved' ? 'bg-primary-100 text-primary-800' : 'bg-gray-100 text-gray-600'
              }`}>
                {alerts.filter((a) => a.status === 'resolved').length}
              </span>
            )}
          </button>
        </nav>
      </div>

      <div className="bg-white/90 backdrop-blur-sm shadow-lg overflow-hidden sm:rounded-md border border-white/50">
        <ul className="divide-y divide-gray-200">
          {filteredAlerts.length === 0 ? (
            <li className="px-6 py-4 text-center text-gray-500">
              No {activeTab} alerts found
            </li>
          ) : (
            filteredAlerts.map((alert) => (
              <li key={alert.id} className="px-6 py-4">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-2">
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getSeverityColor(
                          alert.severity
                        )}`}
                      >
                        {alert.severity}
                      </span>
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(
                          alert.status
                        )}`}
                      >
                        {alert.status}
                      </span>
                    </div>
                    <h3 className="text-lg font-medium text-gray-900">{alert.alert_type}</h3>
                    <p className="text-sm text-gray-500 mt-1">{alert.message}</p>
                    {alert.camera_name && (
                      <p className="text-xs text-gray-400 mt-1">Camera: {alert.camera_name}</p>
                    )}
                    {getMediaName(alert) && (
                      <div className="flex items-center gap-2 mt-2">
                        <span className="text-xs text-gray-600">
                          {isVideo(alert) ? 'Video' : 'Image'}: {getMediaName(alert)}
                        </span>
                        <button
                          onClick={() => handleViewMedia(alert)}
                          className="bg-blue-600 hover:bg-blue-700 text-white px-2 py-1 rounded text-xs font-medium"
                        >
                          View
                        </button>
                      </div>
                    )}
                    <p className="text-xs text-gray-400 mt-1">
                      {new Date(alert.created_at).toLocaleString()}
                    </p>
                  </div>
                  {alert.status === 'pending' && (
                    <button
                      onClick={() => handleResolve(alert.id)}
                      className="ml-4 bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-md text-sm font-medium"
                    >
                      Resolve
                    </button>
                  )}
                </div>
              </li>
            ))
          )}
        </ul>
      </div>

      {/* Image View Modal */}
      {viewingImage && (
        <div className="fixed inset-0 bg-black bg-opacity-75 overflow-y-auto h-full w-full z-50 flex items-center justify-center">
          <div className="relative max-w-4xl max-h-[90vh] m-4">
            <button
              onClick={closeImageView}
              className="absolute top-2 right-2 bg-white bg-opacity-80 hover:bg-opacity-100 text-gray-800 rounded-full p-2 z-10"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
            <div className="bg-white rounded-lg overflow-hidden">
              <div className="p-4 border-b">
                <h3 className="text-lg font-semibold text-gray-900">{viewingImage.name}</h3>
              </div>
              <div className="p-4">
                {viewingImage.isVideo ? (
                  <video
                    src={viewingImage.url}
                    controls
                    className="max-w-full max-h-[70vh] mx-auto"
                    onError={(e) => {
                      console.error('Video load error:', e);
                    }}
                  >
                    Your browser does not support the video tag.
                  </video>
                ) : (
                  <img
                    src={viewingImage.url}
                    alt={viewingImage.name}
                    className="max-w-full max-h-[70vh] mx-auto object-contain"
                    onError={(e) => {
                      e.target.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="400" height="300"%3E%3Crect width="400" height="300" fill="%23ddd"/%3E%3Ctext x="50%25" y="50%25" text-anchor="middle" dy=".3em" fill="%23999"%3EImage not found%3C/text%3E%3C/svg%3E';
                    }}
                  />
                )}
              </div>
            </div>
          </div>
        </div>
      )}
      </div>
    </>
  );
};

export default Alerts;

