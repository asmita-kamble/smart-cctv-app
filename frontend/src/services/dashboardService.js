import api from '../utils/api';

export const dashboardService = {
  getOverview: async () => {
    const response = await api.get('/dashboard/overview');
    return response.data;
  },

  getAllCameras: async () => {
    const response = await api.get('/dashboard/cameras');
    return response.data;
  },
};

