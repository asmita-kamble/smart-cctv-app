import api from '../utils/api';

export const activityService = {
  getAll: async (params = {}) => {
    const response = await api.get('/activities', { params });
    return response.data;
  },

  getById: async (id) => {
    const response = await api.get(`/activities/${id}`);
    return response.data;
  },
};

