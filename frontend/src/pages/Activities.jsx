import { useState, useEffect } from 'react';
import { activityService } from '../services/activityService';
import { cameraService } from '../services/cameraService';

const Activities = () => {
  const [activities, setActivities] = useState([]);
  const [cameras, setCameras] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [viewingImage, setViewingImage] = useState(null);
  const [selectedCameraId, setSelectedCameraId] = useState('all');

  useEffect(() => {
    loadCameras();
    loadActivities();
  }, []);

  const loadCameras = async () => {
    try {
      const data = await cameraService.getAll();
      const camerasList = Array.isArray(data) ? data : data.cameras || [];
      setCameras(camerasList);
    } catch (err) {
      console.error('Failed to load cameras:', err);
    }
  };

  const loadActivities = async () => {
    try {
      const data = await activityService.getAll();
      setActivities(Array.isArray(data) ? data : data.activities || []);
    } catch (err) {
      setError('Failed to load activities');
    } finally {
      setLoading(false);
    }
  };

  const getMediaName = (activity) => {
    if (activity.metadata) {
      const mediaPath = activity.metadata.image_path || activity.metadata.video_path;
      if (mediaPath) {
        return mediaPath.split('/').pop() || mediaPath;
      }
    }
    return null;
  };

  const isVideo = (activity) => {
    return activity.metadata && activity.metadata.video_path && !activity.metadata.image_path;
  };

  const getImageUrl = (activityId) => {
    const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5001/api';
    return `${API_BASE_URL}/activities/${activityId}/image`;
  };

  const handleViewMedia = async (activity) => {
    const mediaName = getMediaName(activity);
    if (!mediaName) {
      setError('No media file associated with this activity');
      return;
    }
    
    try {
      const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5001/api';
      const token = localStorage.getItem('token');
      
      const response = await fetch(getImageUrl(activity.id), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to load media file');
      }

      const blob = await response.blob();
      const blobUrl = URL.createObjectURL(blob);
      setViewingImage({ url: blobUrl, name: mediaName, isVideo: isVideo(activity) });
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

  // Filter activities based on selected camera
  const filteredActivities = selectedCameraId === 'all'
    ? activities
    : activities.filter((activity) => activity.camera_id === parseInt(selectedCameraId));

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
        <h2 className="text-2xl font-bold text-gray-900 drop-shadow-sm">Activities</h2>
        <div className="flex items-center gap-2">
          <label htmlFor="cameraFilter" className="text-sm text-gray-700 whitespace-nowrap">
            Filter by Camera:
          </label>
          <select
            id="cameraFilter"
            value={selectedCameraId}
            onChange={(e) => setSelectedCameraId(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md bg-white text-sm text-gray-700 focus:outline-none focus:ring-1 focus:ring-primary-500 focus:border-primary-500 min-w-[200px]"
          >
            <option value="all">All Cameras</option>
            {cameras.map((camera) => (
              <option key={camera.id} value={camera.id}>
                {camera.name} {camera.location ? `(${camera.location})` : ''}
              </option>
            ))}
          </select>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      {selectedCameraId !== 'all' && (
        <div className="mb-4 text-sm text-gray-600">
          Showing activities for: <span className="font-medium">{cameras.find(c => c.id === parseInt(selectedCameraId))?.name || 'Selected Camera'}</span>
        </div>
      )}

      <div className="bg-white/90 backdrop-blur-sm shadow-lg overflow-hidden sm:rounded-md border border-white/50">
        <ul className="divide-y divide-gray-200">
          {filteredActivities.length === 0 ? (
            <li className="px-6 py-4 text-center text-gray-500">
              {selectedCameraId === 'all' ? 'No activities found' : 'No activities found for selected camera'}
            </li>
          ) : (
            filteredActivities.map((activity) => (
              <li key={activity.id} className="px-6 py-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-2">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                        {activity.activity_type}
                      </span>
                      {activity.confidence_score && (
                        <span className="text-xs text-gray-500">
                          Confidence: {(activity.confidence_score * 100).toFixed(1)}%
                        </span>
                      )}
                    </div>
                    <h3 className="text-lg font-medium text-gray-900">{activity.description}</h3>
                    {activity.camera_name && (
                      <p className="text-sm text-gray-500 mt-1">Camera: {activity.camera_name}</p>
                    )}
                    {getMediaName(activity) && (
                      <div className="flex items-center gap-2 mt-2">
                        <span className="text-xs text-gray-600">
                          {isVideo(activity) ? 'Video' : 'Image'}: {getMediaName(activity)}
                        </span>
                        <button
                          onClick={() => handleViewMedia(activity)}
                          className="bg-blue-600 hover:bg-blue-700 text-white px-2 py-1 rounded text-xs font-medium"
                        >
                          View
                        </button>
                      </div>
                    )}
                    <p className="text-xs text-gray-400 mt-1">
                      {new Date(activity.timestamp).toLocaleString()}
                    </p>
                  </div>
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

export default Activities;

