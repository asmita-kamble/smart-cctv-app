import api from '../utils/api';

export const authService = {
  register: async (userData) => {
    try {
      console.log('authService.register - sending:', userData);
      const response = await api.post('/auth/register', userData);
      console.log('authService.register - response:', response.data);
      return response.data;
    } catch (error) {
      console.error('authService.register error:', {
        message: error.message,
        response: error.response?.data,
        status: error.response?.status,
      });
      throw error;
    }
  },

  login: async (email, password) => {
    try {
      console.log('=== authService.login START ===');
      console.log('Email:', email);
      console.log('API base URL:', import.meta.env.VITE_API_URL || 'http://localhost:5001/api');
      console.log('Full endpoint:', `${import.meta.env.VITE_API_URL || 'http://localhost:5001/api'}/auth/login`);
      
      // Validate inputs
      if (!email || !password) {
        throw new Error('Email and password are required');
      }
      
      console.log('Making API POST request...');
      const requestData = { email, password };
      console.log('Request data (password hidden):', { email, password: '***' });
      
      const response = await api.post('/auth/login', requestData);
      console.log('=== API RESPONSE RECEIVED ===');
      console.log('Response status:', response.status);
      console.log('Response headers:', response.headers);
      console.log('Response data:', response.data);
      console.log('Response data type:', typeof response.data);
      console.log('Response data keys:', Object.keys(response.data || {}));
      
      // Handle different possible response formats
      const token = response.data?.access_token || response.data?.token;
      const user = response.data?.user || response.data;
      
      console.log('Extracted token:', token ? `EXISTS (${token.length} chars)` : 'NONE');
      console.log('Extracted user:', user);
      
      if (token) {
        try {
          localStorage.setItem('token', token);
          console.log('✓ Token stored in localStorage');
          
          if (user) {
            const userStr = JSON.stringify(user);
            localStorage.setItem('user', userStr);
            console.log('✓ User stored in localStorage');
            console.log('User data:', user);
          }
          console.log('Token preview:', token.substring(0, 30) + '...');
        } catch (storageError) {
          console.error('ERROR storing in localStorage:', storageError);
          throw new Error('Failed to store authentication data: ' + storageError.message);
        }
      } else {
        console.error('ERROR: No token in response!');
        console.error('Full response data:', JSON.stringify(response.data, null, 2));
        throw new Error('No access token received from server. Response: ' + JSON.stringify(response.data));
      }
      
      console.log('=== authService.login SUCCESS ===');
      return response.data;
    } catch (error) {
      console.error('=== authService.login ERROR ===');
      console.error('Error name:', error.name);
      console.error('Error message:', error.message);
      console.error('Error stack:', error.stack);
      console.error('Has response?', !!error.response);
      if (error.response) {
        console.error('Response status:', error.response.status);
        console.error('Response data:', error.response.data);
        console.error('Response headers:', error.response.headers);
      }
      console.error('Request config:', error.config);
      throw error;
    }
  },

  logout: () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  },

  getCurrentUser: async () => {
    const response = await api.get('/auth/me');
    return response.data;
  },

  getStoredUser: () => {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
  },

  getToken: () => {
    return localStorage.getItem('token');
  },

  isAuthenticated: () => {
    return !!localStorage.getItem('token');
  },

  forgotPassword: async (email) => {
    try {
      const response = await api.post('/auth/forgot-password', { email });
      return response.data;
    } catch (error) {
      console.error('authService.forgotPassword error:', {
        message: error.message,
        response: error.response?.data,
        status: error.response?.status,
      });
      throw error;
    }
  },

  resetPassword: async (token, password) => {
    try {
      const response = await api.post('/auth/reset-password', { token, password });
      return response.data;
    } catch (error) {
      console.error('authService.resetPassword error:', {
        message: error.message,
        response: error.response?.data,
        status: error.response?.status,
      });
      throw error;
    }
  },
};

