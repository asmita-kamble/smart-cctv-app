import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5001/api';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      // Ensure token is properly formatted
      const cleanToken = token.trim();
      config.headers.Authorization = `Bearer ${cleanToken}`;
      console.log('API Request - Token added:', {
        tokenLength: cleanToken.length,
        tokenStart: cleanToken.substring(0, 20) + '...',
        headerSet: !!config.headers.Authorization,
      });
    } else {
      console.warn('API Request - No token found in localStorage!');
    }
    // Log for debugging
    console.log('API Request:', {
      method: config.method?.toUpperCase(),
      url: config.url,
      baseURL: config.baseURL,
      fullURL: `${config.baseURL}${config.url}`,
      hasToken: !!token,
      authorizationHeader: config.headers.Authorization ? 'Bearer ***' : 'None',
      data: config.data,
    });
    return config;
  },
  (error) => {
    console.error('API Request interceptor error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor to handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', {
      status: error.response?.status,
      data: error.response?.data,
      url: error.config?.url,
    });
    
    if (error.response?.status === 401) {
      // Unauthorized - clear token and redirect to login
      console.warn('401 Unauthorized - clearing token and redirecting to login');
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      // Only redirect if not already on login page
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export default api;

