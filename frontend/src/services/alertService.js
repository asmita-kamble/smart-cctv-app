import api from '../utils/api';

export const alertService = {
  getAll: async (params = {}) => {
    const response = await api.get('/alerts', { params });
    return response.data;
  },

  getById: async (id) => {
    const response = await api.get(`/alerts/${id}`);
    return response.data;
  },

  resolve: async (id) => {
    const response = await api.post(`/alerts/${id}/resolve`);
    return response.data;
  },

  getStatistics: async () => {
    const response = await api.get('/alerts/statistics');
    return response.data;
  },
};

