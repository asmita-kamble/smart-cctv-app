import api from '../utils/api';

export const userManagementService = {
  listUsers: async (params = {}) => {
    const { limit = 100, offset = 0 } = params;
    const response = await api.get('/users', { params: { limit, offset } });
    return response.data;
  },

  inviteUser: async (data) => {
    const response = await api.post('/users/invite', data);
    return response.data;
  },

  deactivateUser: async (userId) => {
    const response = await api.post(`/users/${userId}/deactivate`);
    return response.data;
  },

  reactivateUser: async (userId) => {
    const response = await api.post(`/users/${userId}/activate`);
    return response.data;
  },
};
