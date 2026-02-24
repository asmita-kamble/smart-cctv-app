import api from '../utils/api';

export const videoService = {
  upload: async (file, cameraId) => {
    const formData = new FormData();
    formData.append('video', file);
    formData.append('camera_id', cameraId);

    const response = await api.post('/videos/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  uploadImage: async (file, cameraId) => {
    const formData = new FormData();
    formData.append('image', file);
    formData.append('camera_id', cameraId);

    const response = await api.post('/videos/upload-image', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  process: async (cameraId) => {
    const response = await api.post(`/videos/process/${cameraId}`);
    return response.data;
  },

  getMediaUrl: (filename) => {
    return `${api.defaults.baseURL}/videos/media/${filename}`;
  },

  getDetections: async (cameraId, videoFilename) => {
    if (!cameraId || !videoFilename) return { fps: 30, frames: {} };
    const name = typeof videoFilename === 'string' ? videoFilename.split(/[/\\]/).pop() : '';
    if (!name) return { fps: 30, frames: {} };
    const response = await api.get('/videos/detections', {
      params: { camera_id: cameraId, video_filename: name },
    });
    return response.data || { fps: 30, frames: {} };
  },
};

