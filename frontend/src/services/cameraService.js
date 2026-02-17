import api from '../utils/api';

export const cameraService = {
  getAll: async () => {
    const response = await api.get('/cameras');
    return response.data;
  },

  getById: async (id) => {
    const response = await api.get(`/cameras/${id}`);
    return response.data;
  },

  create: async (cameraData) => {
    const response = await api.post('/cameras', cameraData);
    return response.data;
  },

  update: async (id, cameraData) => {
    const response = await api.put(`/cameras/${id}`, cameraData);
    return response.data;
  },

  delete: async (id) => {
    const response = await api.delete(`/cameras/${id}`);
    return response.data;
  },

  uploadAllowedPersonImage: async (cameraId, imageFile, name = '') => {
    const formData = new FormData();
    formData.append('image', imageFile);
    if (name) {
      formData.append('name', name);
    }
    const response = await api.post(`/cameras/${cameraId}/allowed-persons`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  getAllowedPersons: async (cameraId) => {
    const response = await api.get(`/cameras/${cameraId}/allowed-persons`);
    return response.data;
  },

  deleteAllowedPerson: async (cameraId, allowedPersonId) => {
    const response = await api.delete(`/cameras/${cameraId}/allowed-persons/${allowedPersonId}`);
    return response.data;
  },
};

